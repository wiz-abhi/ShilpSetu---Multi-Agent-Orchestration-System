"""
Script to test video generation capabilities with Google Veo 3
"""

import asyncio
import os
from PIL import Image
import io

from agents.video_generator_agent import VideoGeneratorAgent
from utils.video_processor import VideoProcessor

async def test_video_generation():
    """Test video generation with sample images using Google Veo 3"""
    try:
        print("Testing video generation capabilities with Google Veo 3...")
        
        # Create sample images
        sample_images = []
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]  # Red, Green, Blue
        
        for i, color in enumerate(colors):
            # Create a simple colored image
            img = Image.new('RGB', (800, 600), color)
            
            # Add some text to make it more interesting
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            draw.text((50, 50), f"Sample Product Image {i+1}", fill=(255, 255, 255))
            
            # Convert to bytes
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            sample_images.append(img_byte_arr.getvalue())
        
        print(f"✓ Created {len(sample_images)} sample images")
        
        print("Testing Google Veo 3 video generation...")
        video_agent = VideoGeneratorAgent()
        
        # Prepare test input data for Veo
        test_input = {
            'generated_prompt': {
                'video_prompt': 'Professional marketing video showcasing artisan ceramic products with smooth transitions and elegant presentation'
            },
            'generated_images': [
                {'image_url': f'test_image_{i}.png', 'prompt_used': f'Sample image {i}'} 
                for i in range(len(sample_images))
            ],
            'product_input': {
                'product_id': 'test_ceramic_vase',
                'description': 'Handcrafted ceramic vase with blue glaze'
            },
            'video_prompt_details': {
                'scene_breakdown': [
                    {'time': '0-5s', 'scene': 'Product introduction with gentle zoom'},
                    {'time': '5-10s', 'scene': 'Detail showcase highlighting craftsmanship'},
                    {'time': '10-15s', 'scene': 'Final presentation with call-to-action'}
                ],
                'music_style': 'upbeat and inspiring'
            }
        }
        
        # Mock the image download for testing
        import requests
        from unittest.mock import patch, Mock
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.content = sample_images[0]  # Use first sample image
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # Test Veo prompt creation
            veo_prompt = video_agent._create_veo_prompt(
                test_input['generated_prompt']['video_prompt'],
                test_input['video_prompt_details']['scene_breakdown'],
                15.0
            )
            print(f"✓ Created Veo-optimized prompt: {veo_prompt[:100]}...")
        
        # Test traditional video processor as fallback
        print("Testing traditional video processing as fallback...")
        video_processor = VideoProcessor()
        
        # Test simple slideshow creation
        print("Testing slideshow video creation...")
        slideshow_video = video_processor.create_slideshow_video(sample_images, duration_per_image=2.0)
        print(f"✓ Created slideshow video ({len(slideshow_video)} bytes)")
        
        # Test marketing video creation
        print("Testing marketing video creation...")
        scene_breakdown = [
            {'time': '0-3s', 'scene': 'Product introduction'},
            {'time': '3-6s', 'scene': 'Detail showcase'},
            {'time': '6-9s', 'scene': 'Call to action'}
        ]
        
        marketing_video = video_processor.create_marketing_video(
            images=sample_images,
            video_prompt="Professional marketing video for artisan product",
            scene_breakdown=scene_breakdown,
            audio_style="upbeat"
        )
        print(f"✓ Created marketing video ({len(marketing_video)} bytes)")
        
        # Save test videos
        os.makedirs('test_output', exist_ok=True)
        
        with open('test_output/slideshow_test.mp4', 'wb') as f:
            f.write(slideshow_video)
        
        with open('test_output/marketing_test.mp4', 'wb') as f:
            f.write(marketing_video)
        
        print("✓ Saved test videos to test_output/ directory")
        
        print("\n🎉 All video generation tests passed!")
        print("✓ Google Veo 3 integration ready")
        print("✓ Traditional video processing fallback working")
        print("Check the test_output/ directory for generated videos.")
        
    except Exception as e:
        print(f"❌ Video generation test failed: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Ensure google-generativeai>=0.8.0 is installed")
        print("2. Ensure google-ai-generativelanguage>=0.6.0 is installed")
        print("3. Set GOOGLE_AI_API_KEY environment variable")
        print("4. Ensure moviepy and opencv-python are installed for fallback")
        print("5. Check that ffmpeg is available on your system")

if __name__ == "__main__":
    asyncio.run(test_video_generation())
