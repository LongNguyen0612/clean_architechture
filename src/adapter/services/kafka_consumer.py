import json
import asyncio
import logging
import signal
import uuid
import sys
import os
from typing import Dict, Any, Optional, List, Callable
from json import JSONDecodeError

from aiokafka import AIOKafkaConsumer
from constant import AUTO_COMMIT, AUTO_OFFSET_RESET, TIMEOUT_LISTENER, MAX_RECORD
from src.app.services import (
    BackendKafkaConsumer,
    CriticalException,
    SkippableException,
    InvalidMessageException,
    Filterable
)

logger = logging.getLogger(__name__)


class AIOKafkaConsumerImplementation(BackendKafkaConsumer):
    """Async Kafka consumer implementation using aiokafka"""
    
    def __init__(
        self,
        servers: list,
        topic: str,
        group_id: str,
        handlers: None,
        filters: Optional[List[Filterable]] = None,
        before_handle_callback: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
        after_handle_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        event_root_mapper_service = None,
        ssl_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize Kafka consumer
        
        Args:
            servers: List of Kafka servers
            topic: Kafka topic to consume from
            group_id: Consumer group ID
            handlers: handlers for the event
            filters: Optional list of event filters
            before_handle_callback: Optional callback before handling event
            after_handle_callback: Optional callback after handling event
            event_root_mapper_service: Optional service for event root mapping
            ssl_config: Optional SSL configuration
        """
        self.__topic = topic
        self.__group_id = group_id
        self.handlers = handlers
        self._filters = filters if filters else []
        self._before_handle_callback = before_handle_callback
        self._after_handle_callback = after_handle_callback
        self.__event_root_mapper_service = event_root_mapper_service
        self._mongo_connected = event_root_mapper_service is not None
        
        # Graceful shutdown settings
        self.stopped = False
        self._body = {}
        self._headers = {}
        self.__started = False
        
        # Configure consumer
        config = {
            "bootstrap_servers": servers,
            "group_id": group_id,
            "enable_auto_commit": AUTO_COMMIT,
            "auto_offset_reset": AUTO_OFFSET_RESET,
            "consumer_timeout_ms": TIMEOUT_LISTENER,
        }
        
        if ssl_config:
            config.update(ssl_config)
        
        self.__consumer = AIOKafkaConsumer(self.__topic, **config)
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._stop)
        signal.signal(signal.SIGTERM, self._stop)
    
    def _stop(self, signum, frame):
        """Handle shutdown signals"""
        if self.stopped:
            sys.exit(0)
        self.stopped = True
        logger.warning(
            "This worker will stop after completing the current job. Press Ctrl+C or send kill -9 %s to force stop",
            os.getpid(),
        )
    
    async def start(self) -> None:
        """Start the consumer"""
        if not self.__started:
            await self.__consumer.start()
            self.__started = True
            logger.info("Kafka consumer started for topic: %s", self.__topic)
    
    async def stop(self) -> None:
        """Stop the consumer"""
        if self.__started:
            await self.__consumer.stop()
            self.__started = False
            logger.info("Kafka consumer stopped")
    
    def _filter_event(self, event: Dict[str, Any]) -> None:
        """Apply filters to the event"""
        for event_filter in self._filters:
            event_filter.filter(event)
    
    async def _get_new_event(self) -> Dict[str, Any]:
        """Get new event from Kafka"""
        try:
            # Poll for messages
            message_batch = await self.__consumer.getmany(timeout_ms=TIMEOUT_LISTENER, max_records=MAX_RECORD)
            
            if not message_batch:
                return {}
            
            for topic_partition, messages in message_batch.items():
                if not messages:
                    continue
                    
                record = messages[0]  # Process one message at a time
                
                try:
                    body = record.value
                    message = json.loads(body.decode("utf-8"))
                    
                    # Extract the key from the Kafka message
                    key = record.key.decode("utf-8") if record.key else None
                    
                    # Add the key to the event if it's a structured event
                    if isinstance(message, dict) and 'event_type' in message and 'payload' in message:
                        message['key'] = key
                        logger.debug("Added Kafka message key to event: %s", key)
                    
                    offset = record.offset
                    
                except (UnicodeDecodeError, JSONDecodeError) as e:
                    logger.exception("DECODING ERROR: %s - EXCEPTIONS: %s", record.value, e)
                    return {}
                
                return {
                    "event": message,
                    "meta_data": {
                        "offset": offset,
                        "key": key,
                        "topic_partition": topic_partition,
                    },
                    "headers": record.headers
                }
            
            return {}
            
        except Exception as e:
            logger.exception("Error getting new event: %s", e)
            return {}
    
    async def _commit_event(self, event: Dict[str, Any]) -> None:
        """Commit the event offset"""
        try:
            event_metadata = event.get("meta_data", {})
            topic_partition = event_metadata.get("topic_partition")
            offset = event_metadata.get("offset")
            
            if topic_partition is not None and offset is not None:
                # Commit the offset
                await self.__consumer.commit({topic_partition: offset + 1})
                logger.info("EVENT COMMITTED")
            else:
                logger.error(
                    "CANNOT COMMIT EVENT %s. MISSING FIELD TOPIC_PARTITION OR OFFSET", event
                )
        except Exception as e:
            logger.exception("Error committing event: %s", e)
    
    async def _handle_event(self, event: Dict[str, Any]) -> None:
        """Handle the event using registered callbacks"""
        try:
            # Apply filters
            self._filter_event(event)
            
            # Before handle callback
            if self._before_handle_callback:
                event = await self._before_handle_callback(event)
            
            # Get event type and find handler
            event_type = event.get('event_type')
            if not event_type:
                raise InvalidMessageException("Missing event_type in message")
        
            # Handle the event
            await self.handlers.handle(event)
            
            # After handle callback
            if self._after_handle_callback:
                await self._after_handle_callback(event)
                
        except SkippableException as se:
            logger.info("EVENT SKIPPED BECAUSE %s", se)
            raise se
        except CriticalException as ce:
            logger.exception("CRITICAL ERROR ON EVENT %s: %s", event, ce)
            raise ce
        except Exception as e:
            logger.exception("Unexpected error handling event %s: %s", event, e)
            raise CriticalException(f"Unexpected error: {e}") from e
                    