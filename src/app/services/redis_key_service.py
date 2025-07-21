
class RedisKeyService:
    # Common expiry times (in seconds)
    TOKEN_EXPIRY = 60 * 60 * 24  # 24 hours
    RESET_TOKEN_EXPIRY = 60 * 60  # 1 hour

