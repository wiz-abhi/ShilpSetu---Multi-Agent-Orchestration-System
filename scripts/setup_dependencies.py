"""
Setup script for the Artisan Marketplace Multi-Agent System
This script installs all required dependencies for the project
"""

import subprocess
import sys

def install_package(package):
    """Install a package using pip"""
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

dependencies = [
    "google-generativeai>=0.8.0",  # Google AI SDK with Imagen/Veo support
    "google-ai-generativelanguage>=0.6.0",  # Required for Imagen/Veo API calls
    "google-cloud-storage>=2.10.0",  # Google Cloud Storage
    "google-cloud-aiplatform>=1.38.0",  # Vertex AI platform support
    "pillow>=10.0.0",  # Image processing
    "requests>=2.31.0",  # HTTP requests
    "python-dotenv>=1.0.0",  # Environment variables
    "aiohttp>=3.8.0",  # Async HTTP client
    "opencv-python>=4.8.0",  # Video processing
    "moviepy>=1.0.3",  # Video editing
    "numpy>=1.24.0",  # Numerical operations
    "typing-extensions>=4.7.0",  # Type hints
]

print("Installing dependencies for Artisan Marketplace Multi-Agent System...")
print("This includes support for Google Imagen and Veo 3 models...")

for package in dependencies:
    try:
        print(f"Installing {package}...")
        install_package(package)
        print(f"✓ {package} installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install {package}: {e}")

print("\n✓ All dependencies installed successfully!")
print("\nNext steps:")
print("1. Set up your Google Cloud credentials")
print("2. Create a .env file with your API keys")
print("3. Configure your Google Cloud Storage bucket")
print("4. Ensure your Google AI API key has access to Imagen and Veo models")
print("5. Test the connection with scripts/test_gcs_connection.py")
