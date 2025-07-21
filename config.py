import os
import yaml

ROOT_PATH = os.path.dirname(__file__)

CONFIG_FILE_PATH = os.path.join(ROOT_PATH, "env.yaml")

if os.path.exists(CONFIG_FILE_PATH):
    with open(CONFIG_FILE_PATH, "r") as r_file:
        data = yaml.safe_load(r_file)
else:
    data = dict()


class ApplicationConfig:
    # Database configuration
    DB_URI = data["DB_URI"]
    MIGRATION_DB_URI = data["MIGRATION_DB_URI"]

    # API configuration
    API_PREFIX = data.get("API_PREFIX", "/api")
    API_PORT = data.get("API_PORT", 8000)
    API_HOST = data.get("API_HOST", "0.0.0.0")

    # CORS configuration
    CORS_ORIGINS = data["CORS_ORIGINS"]
    CORS_ALLOW_CREDENTIALS = data.get("CORS_ALLOW_CREDENTIALS", True)

    # Logging configuration
    LOG_LEVEL = data.get(
        "LOG_LEVEL", "INFO"
    )  # DEBUG, INFO, WARNING, ERROR, CRITICAL# If None, defaults to logs/travel_hub.log
    AUTH_DISABLED = bool(data.get("AUTH_DISABLED", False))
    ENABLE_LOGGING_MIDDLEWARE = bool(data.get("ENABLE_LOGGING_MIDDLEWARE", 1))
    ENABLE_SENTRY = data.get("ENABLE_SENTRY", 0)
    DSN_SENTRY = data.get("DSN_SENTRY", "")
    SENTRY_ENVIRONMENT = data.get("SENTRY_ENVIRONMENT", "dev")

    # REDIS
    REDIS_URL = data["REDIS_URL"]
    CACHE_BACKEND = data["CACHE_BACKEND"]


class ListenerSettings:
    EVENT_KAFKA_SERVER_LISTENER = data["EVENT_KAFKA_SERVER_LISTENER"]
    EVENT_TOPIC_LISTENER = data["EVENT_TOPIC_LISTENER"]
    CONSUMER_GROUP_LISTENER = data["CONSUMER_GROUP_LISTENER"]
    CONSUMER_SECURITY_PROTOCOL = data.get("CONSUMER_SECURITY_PROTOCOL", None)
    CONSUMER_SSL_CA_FILE = data.get("CONSUMER_SSL_CA_FILE", None)
    CONSUMER_SSL_CHECK_HOSTNAME = data.get("CONSUMER_SSL_CHECK_HOSTNAME", None)
    CONSUMER_SASL_MECHANISM = data.get("CONSUMER_SASL_MECHANISM", None)
    CONSUMER_SASL_PLAIN_USERNAME = data.get("CONSUMER_SASL_PLAIN_USERNAME", None)
    CONSUMER_SASL_PLAIN_PASSWORD = data.get("CONSUMER_SASL_PLAIN_PASSWORD", None)
    CONSUMER_ENABLE_KAFKA_SSL = data.get("CONSUMER_ENABLE_KAFKA_SSL", None)


class PublisherSettings:
    EVENT_KAFKA_SERVER_PUBLISHER = data.get("EVENT_KAFKA_SERVER_PUBLISHER", None)
    EVENT_TOPIC_PUBLISHER = data.get("EVENT_TOPIC_PUBLISHER", None)
    PUBLISHER_SECURITY_PROTOCOL = data.get("PUBLISHER_SECURITY_PROTOCOL", None)
    PUBLISHER_SSL_CA_FILE = data.get("PUBLISHER_SSL_CA_FILE", None)
    PUBLISHER_SSL_CHECK_HOSTNAME = data.get("PUBLISHER_SSL_CHECK_HOSTNAME", None)
    PUBLISHER_SASL_MECHANISM = data.get("PUBLISHER_SASL_MECHANISM", None)
    PUBLISHER_SASL_PLAIN_USERNAME = data.get("PUBLISHER_SASL_PLAIN_USERNAME", None)
    PUBLISHER_SASL_PLAIN_PASSWORD = data.get("PUBLISHER_SASL_PLAIN_PASSWORD", None)
    PUBLISHER_ENABLE_KAFKA_SSL = data.get("PUBLISHER_ENABLE_KAFKA_SSL", None)
    

