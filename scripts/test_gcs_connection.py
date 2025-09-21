"""
Script to test Google Cloud Storage connection and setup
"""

import asyncio
from utils.gcs_manager import GCSManager
from config.settings import Config

async def test_gcs_connection():
    """Test GCS connection and basic operations"""
    try:
        print("Testing Google Cloud Storage connection...")
        
        # Initialize GCS manager
        gcs_manager = GCSManager()
        print(f"✓ Connected to bucket: {Config.GCS_BUCKET_NAME}")
        
        # Test file listing
        files = gcs_manager.list_files(limit=5)
        print(f"✓ Listed {len(files)} files in bucket")
        
        # Test upload with a small test file
        test_data = b"Test file content for GCS connection"
        upload_result = gcs_manager.upload_image(
            image_data=test_data,
            filename="test_connection.txt",
            content_type="text/plain"
        )
        print(f"✓ Test upload successful: {upload_result['public_url']}")
        
        # Test download
        downloaded_data = gcs_manager.download_file(upload_result['gcs_path'])
        assert downloaded_data == test_data
        print("✓ Test download successful")
        
        # Clean up test file
        gcs_manager.delete_file(upload_result['gcs_path'])
        print("✓ Test cleanup successful")
        
        print("\n🎉 All GCS tests passed! Your Google Cloud Storage is properly configured.")
        
    except Exception as e:
        print(f"❌ GCS test failed: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Verify your GCS_BUCKET_NAME in .env")
        print("2. Check your GCS_CREDENTIALS_PATH points to valid service account key")
        print("3. Ensure the service account has Storage Admin permissions")
        print("4. Verify the bucket exists and is accessible")

if __name__ == "__main__":
    asyncio.run(test_gcs_connection())
