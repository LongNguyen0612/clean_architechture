from fastapi import APIRouter, Depends
import asyncio
import time
import logging
from typing import Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.adapter.services import RedisCacheBackend, AIOKafkaProducerImplementation
from src.depends import get_db_session, get_redis_client, get_kafka_client
from fastapi.responses import JSONResponse

router = APIRouter()
logger = logging.getLogger(__name__)


async def check_postgres(db: AsyncSession) -> Tuple[bool, float]:
    try:
        start = time.time()
        # Execute a simple query with timeout
        result = await asyncio.wait_for(db.execute(text("SELECT 1")), timeout=10.0)
        # Make sure we can fetch the result - use scalar() instead of fetchone()
        row = result.scalar()
        if row is None:
            logger.error("PostgreSQL health check failed: No result returned")
            return False, 0
        # Calculate latency
        latency = (time.time() - start) * 1000
        return True, latency
    except asyncio.TimeoutError:
        logger.error("PostgreSQL health check timed out after 10 seconds")
        return False, 0
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        return False, 0


async def check_redis(redis_client: RedisCacheBackend) -> Tuple[bool, float]:
    try:
        start = time.time()
        # Simple ping with timeout
        ping_result = await asyncio.wait_for(redis_client.redis_client.ping(), timeout=10.0)
        if not ping_result:
            logger.error("Redis health check failed: Ping returned false")
            return False, 0
        # Calculate latency
        latency = (time.time() - start) * 1000
        return True, latency
    except asyncio.TimeoutError:
        logger.error("Redis health check timed out after 10 seconds")
        return False, 0
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False, 0


async def check_kafka(kafka_client: AIOKafkaProducerImplementation) -> Tuple[bool, float]:
    try:
        start = time.time()
        # Start the producer and check cluster metadata
        await asyncio.wait_for(kafka_client.start(), timeout=10.0)
        
        # Get cluster metadata to verify connectivity
        cluster_metadata = kafka_client._AIOKafkaProducerImplementation__producer.client.cluster
        
        # Check if we have brokers
        if not cluster_metadata.brokers:
            logger.error("Kafka health check failed: No brokers available")
            return False, 0
            
        # Calculate latency
        latency = (time.time() - start) * 1000
        
        # Stop the producer
        await kafka_client.stop()
        
        return True, latency
    except asyncio.TimeoutError:
        logger.error("Kafka health check timed out after 10 seconds")
        return False, 0
    except Exception as e:
        logger.error(f"Kafka health check failed: {e}")
        return False, 0
    finally:
        try:
            await kafka_client.stop()
        except Exception as e:
            logger.warning(f"Error stopping Kafka client during health check: {e}")

@router.get("/health-check")
async def health_check(
    db: AsyncSession = Depends(get_db_session), 
    redis_client=Depends(get_redis_client),
    kafka_client=Depends(get_kafka_client)
) -> Dict[str, Any]:
    response = {"checks": {}, "status": "healthy"}
    healthy = True

    # Check PostgreSQL
    pg_status, pg_latency = await check_postgres(db)
    response["checks"]["postgres"] = {
        "status": "healthy" if pg_status else "unhealthy",
        "latency_ms": pg_latency
    }
    if not pg_status:
        healthy = False

    # Check Redis
    redis_status, redis_latency = await check_redis(redis_client)
    response["checks"]["redis"] = {
        "status": "healthy" if redis_status else "unhealthy",
        "latency_ms": redis_latency
    }
    if not redis_status:
        healthy = False

    # Check Kafka
    kafka_status, kafka_latency = await check_kafka(kafka_client)
    response["checks"]["kafka"] = {
        "status": "healthy" if kafka_status else "unhealthy",
        "latency_ms": kafka_latency
    }
    if not kafka_status:
        healthy = False

    response["status"] = "healthy" if healthy else "unhealthy"

    return JSONResponse(content=response, status_code=200 if healthy else 500)
