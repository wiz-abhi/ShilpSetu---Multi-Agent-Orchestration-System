"""
Configuration settings for the Multi-Agent System
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the multi-agent system"""
    
    # Google AI API Configuration
    GOOGLE_AI_API_KEY = os.getenv('GOOGLE_AI_API_KEY')
    
    IMAGEN_MODEL = "imagen-3.0-generate-001"
    VEO_MODEL = "veo-3.0-generate-001"
    GEMINI_MODEL = "gemini-2.0-flash-exp"
    GEMINI_VISION_MODEL = "gemini-2.0-flash-exp"
    
    # Google Cloud Storage Configuration
    GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME', 'artisan-marketplace-media')
    GCS_CREDENTIALS_PATH = os.getenv('GCS_CREDENTIALS_PATH')
    
    # Image Generation Settings (optimized for Imagen)
    IMAGE_COUNT_DEFAULT = 2
    IMAGE_COUNT_MAX = 3
    IMAGE_QUALITY = 'high'
    IMAGE_FORMAT = 'PNG'
    IMAGEN_ASPECT_RATIO = "1:1"  # Square format for product images
    IMAGEN_SAFETY_LEVEL = "BLOCK_ONLY_HIGH"
    
    # Video Generation Settings (optimized for Veo 3)
    VIDEO_DURATION = 15  # seconds
    VIDEO_FPS = 30
    VIDEO_RESOLUTION = (1920, 1080)
    VIDEO_FORMAT = 'mp4'
    VEO_ASPECT_RATIO = "16:9"  # Widescreen for marketing videos
    VEO_MOTION_AMOUNT = "MEDIUM"  # Balanced motion for product videos
    VEO_MAX_REFERENCE_IMAGES = 3  # Limit reference images for Veo
    
    # Agent Communication Settings
    AGENT_TIMEOUT = 300  # 5 minutes
    MAX_RETRIES = 3
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = 'logs/agent_system.log'
    
    @classmethod
    def validate_config(cls):
        """Validate that all required configuration is present"""
        required_vars = [
            'GOOGLE_AI_API_KEY',
            'GCS_BUCKET_NAME'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True

# Validate configuration on import
Config.validate_config()
