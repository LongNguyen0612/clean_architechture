from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime



class KafkaPublishMessageFailed(Exception):
    """Exception raised when Kafka message publishing fails"""
    pass 

class BackendKafkaProducer(ABC):
    """Abstract base class for Kafka producer"""
    
    @abstractmethod
    async def publish(
        self,
        event_type: str,
        payload: Dict[str, Any],
        key: Optional[str] = None,
        issued_at: Optional[datetime] = None,
    ) -> None:
        """
        Publish a message to Kafka
        
        Args:
            event_type: Type of the event
            payload: Event payload data
            key: Optional message key for partitioning
            issued_at: Optional timestamp, defaults to current time
            
        Raises:
            KafkaPublishMessageFailed: When message publishing fails
        """
        raise NotImplementedError()
    
    @abstractmethod
    async def start(self) -> None:
        """Start the producer"""
        raise NotImplementedError()
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the producer"""
        raise NotImplementedError()
    