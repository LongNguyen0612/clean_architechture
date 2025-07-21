import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable

logger = logging.getLogger(__name__)


class CriticalException(Exception):
    """Exception for critical errors that should stop processing"""
    pass


class SkippableException(Exception):
    """Exception for errors that can be skipped"""
    pass


class InvalidMessageException(SkippableException):
    """Exception for invalid message format"""
    pass


class Filterable(ABC):
    """Abstract base class for event filters"""
    
    @abstractmethod
    def filter(self, event: Dict[str, Any]) -> None:
        """Filter the event"""
        raise NotImplementedError() 
    

class BackendKafkaConsumer(ABC):
    """Abstract base class for Kafka consumer"""
    
    @abstractmethod
    async def start(self) -> None:
        """Start the consumer"""
        raise NotImplementedError()
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the consumer"""
        raise NotImplementedError()
    
    @abstractmethod
    async def _get_new_event(self) -> Dict[str, Any]:
        """Get new event from Kafka"""
        raise NotImplementedError()
    
    @abstractmethod
    def _filter_event(self, event: Dict[str, Any]) -> None:
        """Apply filters to the event"""
        raise NotImplementedError()
    
    @abstractmethod
    async def _commit_event(self, event: Dict[str, Any]) -> None:
        """Commit the event offset"""
        raise NotImplementedError()
    
    @abstractmethod
    async def _handle_event(self, event: Dict[str, Any]) -> None:
        """Handle the event using registered callbacks"""
        raise NotImplementedError()
    
    def _create_header(self, headers) -> None:
        """Create and process message headers for event tracing"""
        try:
            decoded_headers = self._decode_headers(dict(headers or []))
        except KeyError as ke:
            raise InvalidMessageException("Invalid headers") from ke
        
        try:
            if not self._mongo_connected:
                log_header = decoded_headers
            else:
                log_header = decoded_headers
                if not log_header and self.__event_root_mapper_service:
                    log_header = self.__event_root_mapper_service.create_header()
                else:
                    log_header = {
                        "root_id": log_header.get('root_id'),
                        "parent_id": log_header.get('parent_id'),
                        "event_id": log_header.get('event_id'),
                    }
            
            self._headers = log_header
            logger.info("Create header %s", self._headers)
            
        except Exception as e:
            logger.exception("Error: %s when create header", str(e))
            raise InvalidMessageException(f"Error creating header: {e}") from e
    
    @staticmethod
    def _decode_headers(headers: Dict[str, Any]) -> Dict[str, Any]:
        """Decode Kafka message headers to extract event tracing information"""
        result = {}
        
        if not headers:
            return result
        
        for key in ['root_id', 'parent_id', 'event_id']:
            if key in headers:
                header_value = headers[key]
                if isinstance(header_value, bytes):
                    result[key] = header_value.decode('utf-8')
                else:
                    result[key] = header_value
        
        return result
    
    async def listen(self) -> None:
        """Start listening for Kafka messages"""
        if not self.__started:
            await self.start()
        
        logger.info("LISTENING EVENT...")
        
        while not self.stopped:
            event = await self._get_new_event()
            if not event:
                await asyncio.sleep(0.1)  # Brief sleep to prevent tight loop
                continue
            
            audit_id = uuid.uuid4().hex
            logger.info("RETRIEVED EVENT: %s", event.get("event", {}))
            
            try:
                event_data = event.get("event", {})
                headers = event.get("headers", None)
                
                logger.info("RETRIEVED EVENT: %s, headers %s", event_data, headers)
                self._create_header(headers)
                logger.info("HANDLING EVENT")
                
                await self._handle_event(event_data)
                
            except SkippableException as se:
                logger.info("EVENT SKIPPED BECAUSE %s", se)
                await self._commit_event(event)
                continue
                
            except CriticalException as ce:
                logger.exception("CRITICAL ERROR ON EVENT %s: %s", event, ce)
                raise ce
                
            else:
                # Save header if service is available
                if self.__event_root_mapper_service:
                    await self.__event_root_mapper_service.save_header(
                        self._headers,
                        event_data.get('payload'),
                        self.__topic,
                        event_data.get('event_type'),
                        event_data.get('issued_at')
                    )
                    logger.info("Saved header %s to mongo", self._headers)
                
                await self._commit_event(event)
                
            finally:
                logger.info("Finished event")
