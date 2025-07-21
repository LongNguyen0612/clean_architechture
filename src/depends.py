from config import ApplicationConfig, PublisherSettings
from src.adapter.services import (RedisCacheBackend, AIOKafkaProducerImplementation)
from src.adapter.services.sql_unit_of_work import SQLAlchemyUnitOfWork

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


def create_session_factory(uri: str) -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(uri, pool_size=20, max_overflow=0, pool_pre_ping=False)
    return async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


session_factory = create_session_factory(ApplicationConfig.DB_URI)


# Create Redis client

def get_unit_of_work() -> SQLAlchemyUnitOfWork:
    return SQLAlchemyUnitOfWork(session_factory)


unit_of_work = get_unit_of_work()


async def get_db_session() -> AsyncSession:
    session = session_factory()
    try:
        yield session
    finally:
        await session.close()


def get_redis_client():
    return RedisCacheBackend(redis_url=ApplicationConfig.REDIS_URL)


async def get_kafka_client():
    """
    Create Kafka client for health checking and general usage
    
    Returns:
        AIOKafkaProducerImplementation: Kafka producer implementation
    """
    # Build SSL config if enabled
    ssl_config = None
    if PublisherSettings.PRODUCER_ENABLE_KAFKA_SSL:
        ssl_config = {
            "security_protocol": PublisherSettings.PRODUCER_SECURITY_PROTOCOL,
            "ssl_check_hostname": PublisherSettings.PRODUCER_SSL_CHECK_HOSTNAME,
        }
        
        if PublisherSettings.PRODUCER_SSL_CA_FILE:
            ssl_config["ssl_cafile"] = PublisherSettings.PRODUCER_SSL_CA_FILE
            
        if PublisherSettings.PRODUCER_SASL_MECHANISM:
            ssl_config.update({
                "sasl_mechanism": PublisherSettings.PRODUCER_SASL_MECHANISM,
                "sasl_plain_username": PublisherSettings.PRODUCER_SASL_PLAIN_USERNAME,
                "sasl_plain_password": PublisherSettings.PRODUCER_SASL_PLAIN_PASSWORD,
            })
    
    # Handle server configuration - provide fallback for missing config
    servers = []
    if PublisherSettings.V4_EVENT_KAFKA_SERVER:
        if isinstance(PublisherSettings.V4_EVENT_KAFKA_SERVER, str):
            servers = [PublisherSettings.V4_EVENT_KAFKA_SERVER]
        else:
            servers = PublisherSettings.V4_EVENT_KAFKA_SERVER
    else:
        servers = ["localhost:9092"]  # Default fallback for local development
    
    # Default topic if not specified
    topic = PublisherSettings.V4_EVENT_TOPIC or "health-check-topic"
    
    return AIOKafkaProducerImplementation(
        servers=servers,
        topic=topic,
        ssl_config=ssl_config
    )

