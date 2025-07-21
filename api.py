import uvicorn
import logging
from src.api import create_app
from config import ApplicationConfig
from src.logger import setup_app_level_logger

# Configure application logging using existing function
setup_app_level_logger(
    name="src", level=ApplicationConfig.LOG_LEVEL if hasattr(ApplicationConfig, "LOG_LEVEL") else "INFO"
)

# Get logger for this module
logger = logging.getLogger(__name__)

# Create the FastAPI app
logger.info("Initializing application")
app = create_app(ApplicationConfig)
logger.info(f"Application initialized and ready to serve on {ApplicationConfig.API_HOST}:{ApplicationConfig.API_PORT}")

if __name__ == "__main__":
    uvicorn.run(app, host=ApplicationConfig.API_HOST, port=ApplicationConfig.API_PORT)
