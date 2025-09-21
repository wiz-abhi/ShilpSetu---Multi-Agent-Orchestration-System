"""
Agent 3: Video Generator Agent
Creates marketing videos using Google's Veo 3 model
"""

import asyncio
from typing import Dict, Any, List, Optional
import requests
import io
from google import genai
import base64

from agents.base_agent import BaseAgent
from models.data_models import AgentResponse, AgentType, GeneratedVideo
from config.settings import Config
from utils.gcs_manager import GCSManager
from utils.video_processor import VideoProcessor
from utils.logger import setup_logger

class VideoGeneratorAgent(BaseAgent):
    """Agent responsible for generating marketing videos using Google Veo 3 and storing them in GCS"""
    
    def __init__(self):
        super().__init__(AgentType.VIDEO_GENERATOR)
        self.gcs_manager = GCSManager()
        self.video_processor = VideoProcessor()  # Keep as fallback
        
        self.client = genai.Client(api_key=Config.GOOGLE_AI_API_KEY)
        
        # Video generation settings
        self.default_duration = Config.VIDEO_DURATION
        self.video_format = Config.VIDEO_FORMAT
        self.video_resolution = Config.VIDEO_RESOLUTION
        
        self.veo_model = "veo-3.0-generate-001"  # Google's Veo 3 model
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Process input data and generate marketing video"""
        try:
            # Extract data from previous agents
            generated_prompt = input_data.get('generated_prompt', {})
            video_prompt = generated_prompt.get('video_prompt', '')
            generated_images = input_data.get('generated_images', [])
            product_input = input_data.get('product_input', {})
            video_prompt_details = input_data.get('video_prompt_details', {})
            
            if not video_prompt:
                raise ValueError("No video prompt provided")
            
            self.logger.info(f"Generating video for product: {product_input.get('product_id', 'unknown')}")
            
            # Collect images for video creation
            image_sources = await self._collect_image_sources(generated_images, product_input)
            
            if not image_sources:
                raise ValueError("No images available for video generation")
            
            # Download images
            image_data_list = await self._download_images(image_sources)
            
            # Extract scene breakdown from prompt details
            scene_breakdown = video_prompt_details.get('scene_breakdown', [])
            music_style = video_prompt_details.get('music_style', 'upbeat')
            
            # Generate video
            video_data = await self._generate_video(
                images=image_data_list,
                video_prompt=video_prompt,
                scene_breakdown=scene_breakdown,
                music_style=music_style
            )
            
            # Upload video to GCS
            upload_result = self.gcs_manager.upload_video(
                video_data=video_data,
                filename=f"marketing_video_{product_input.get('product_id', 'unknown')}.{self.video_format}",
                content_type=f"video/{self.video_format}"
            )
            
            # Create GeneratedVideo object
            generated_video = GeneratedVideo(
                video_url=upload_result['public_url'],
                gcs_path=upload_result['gcs_path'],
                duration=self.default_duration,
                source_images=[img['image_url'] for img in generated_images],
                prompt_used=video_prompt
            )
            
            # Prepare response data
            response_data = {
                'generated_video': generated_video.__dict__,
                'video_details': {
                    'duration': self.default_duration,
                    'resolution': self.video_resolution,
                    'format': self.video_format,
                    'file_size': len(video_data),
                    'scene_count': len(scene_breakdown) if scene_breakdown else len(image_data_list)
                },
                'source_images_count': len(image_data_list),
                'product_input': product_input,
                'upload_info': upload_result
            }
            
            self.logger.info(f"Successfully generated and uploaded video for product {product_input.get('product_id', 'unknown')}")
            
            return AgentResponse(
                success=True,
                data=response_data
            )
            
        except Exception as e:
            self.logger.error(f"Error in video generation: {str(e)}")
            return AgentResponse(
                success=False,
                error=f"Video generation failed: {str(e)}"
            )
    
    async def _collect_image_sources(self, generated_images: List[Dict], product_input: Dict) -> List[Dict]:
        """Collect all available image sources for video creation"""
        image_sources = []
        
        # Add generated images from Agent 2
        for img in generated_images:
            image_sources.append({
                'url': img.get('image_url'),
                'source': 'generated',
                'prompt': img.get('prompt_used', '')
            })
        
        # Add optional user-provided image if available
        optional_image_url = product_input.get('optional_image_url')
        if optional_image_url:
            image_sources.append({
                'url': optional_image_url,
                'source': 'user_provided',
                'prompt': 'Original user image'
            })
        
        self.logger.info(f"Collected {len(image_sources)} image sources for video")
        return image_sources
    
    async def _download_images(self, image_sources: List[Dict]) -> List[bytes]:
        """Download images from URLs"""
        image_data_list = []
        
        async def download_single_image(source: Dict) -> Optional[bytes]:
            try:
                # Use requests for simplicity (in production, consider aiohttp)
                response = requests.get(source['url'], timeout=30)
                response.raise_for_status()
                return response.content
            except Exception as e:
                self.logger.warning(f"Failed to download image from {source['url']}: {str(e)}")
                return None
        
        # Download images concurrently
        download_tasks = [download_single_image(source) for source in image_sources]
        results = await asyncio.gather(*download_tasks, return_exceptions=True)
        
        # Filter successful downloads
        for result in results:
            if isinstance(result, bytes):
                image_data_list.append(result)
            elif isinstance(result, Exception):
                self.logger.warning(f"Image download failed: {str(result)}")
        
        if not image_data_list:
            raise ValueError("Failed to download any images for video generation")
        
        self.logger.info(f"Successfully downloaded {len(image_data_list)} images")
        return image_data_list
    
    async def _generate_video(
        self, 
        images: List[bytes], 
        video_prompt: str,
        scene_breakdown: List[Dict],
        music_style: str
    ) -> bytes:
        """Generate video using Google's Veo 3 model"""
        try:
            video_data = await self._call_veo_api(
                video_prompt=video_prompt,
                reference_images=images,
                duration=self.default_duration,
                scene_breakdown=scene_breakdown
            )
            
            return video_data
            
        except Exception as e:
            self.logger.error(f"Veo 3 video generation failed: {str(e)}")
            # Fallback to traditional video processing
            self.logger.info("Falling back to traditional video processing")
            return await self._create_fallback_video(images)
    
    async def _call_veo_api(
        self, 
        video_prompt: str, 
        reference_images: List[bytes],
        duration: float,
        scene_breakdown: List[Dict]
    ) -> bytes:
        """Call Google Veo 3 API to generate video"""
        try:
            # Prepare reference images for Veo
            image_parts = []
            for i, image_data in enumerate(reference_images[:3]):  # Limit to 3 images
                # Convert image to base64
                image_b64 = base64.b64encode(image_data).decode('utf-8')
                image_parts.append({
                    "mime_type": "image/jpeg",
                    "data": image_b64
                })
            
            # Create enhanced prompt for Veo
            enhanced_prompt = self._create_veo_prompt(video_prompt, scene_breakdown, duration)
            
            contents = [enhanced_prompt] + image_parts
            
            response = self.client.models.generate_content(
                model=self.veo_model,
                contents=contents
            )
            
            if response.candidates and response.candidates[0].content:
                # Extract video data from response
                content = response.candidates[0].content
                if hasattr(content, 'parts') and content.parts:
                    for part in content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            # Convert base64 to bytes
                            video_data = base64.b64decode(part.inline_data.data)
                            return video_data
                
                raise Exception("No video data found in Veo response")
            else:
                raise Exception("No video generated by Veo API")
                
        except Exception as e:
            self.logger.error(f"Veo API call failed: {str(e)}")
            raise
    
    def _create_veo_prompt(self, base_prompt: str, scene_breakdown: List[Dict], duration: float) -> str:
        """Create an enhanced prompt optimized for Veo 3"""
        veo_prompt = f"""
        Create a {duration}-second marketing video for an artisan product.
        
        Main concept: {base_prompt}
        
        Video structure:
        """
        
        if scene_breakdown:
            for scene in scene_breakdown:
                veo_prompt += f"- {scene.get('time', '')}: {scene.get('scene', '')}\n"
        else:
            # Default structure
            veo_prompt += f"""
            - 0-{duration//3}s: Product introduction with smooth zoom-in
            - {duration//3}-{2*duration//3}s: Showcase product details and craftsmanship
            - {2*duration//3}-{duration}s: Final presentation with call-to-action
            """
        
        veo_prompt += """
        
        Style requirements:
        - Professional marketing quality
        - Smooth camera movements
        - High-end product photography aesthetic
        - Clean, modern presentation
        - Subtle transitions between scenes
        - Focus on product craftsmanship and quality
        """
        
        return veo_prompt
    
    async def _download_from_gcs_uri(self, gcs_uri: str) -> bytes:
        """Download video from Google Cloud Storage URI"""
        try:
            # Extract bucket and object name from GCS URI
            # Format: gs://bucket-name/object-name
            uri_parts = gcs_uri.replace('gs://', '').split('/', 1)
            bucket_name = uri_parts[0]
            object_name = uri_parts[1]
            
            # Use GCS client to download
            from google.cloud import storage
            client = storage.Client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(object_name)
            
            return blob.download_as_bytes()
            
        except Exception as e:
            self.logger.error(f"Failed to download from GCS URI {gcs_uri}: {str(e)}")
            raise
    
    async def _create_fallback_video(self, images: List[bytes]) -> bytes:
        """Create a simple fallback video if advanced generation fails"""
        try:
            loop = asyncio.get_event_loop()
            
            video_data = await loop.run_in_executor(
                None,
                self.video_processor.create_slideshow_video,
                images,
                self.default_duration / len(images)
            )
            
            return video_data
            
        except Exception as e:
            self.logger.error(f"Fallback video generation failed: {str(e)}")
            raise
    
    def create_video_from_single_image(self, image_data: bytes, duration: float = 10.0) -> bytes:
        """Create a video from a single image with zoom effects"""
        try:
            return self.video_processor.create_slideshow_video([image_data], duration)
        except Exception as e:
            self.logger.error(f"Single image video creation failed: {str(e)}")
            raise
    
    async def add_branding_to_video(self, video_data: bytes, logo_data: Optional[bytes] = None) -> bytes:
        """Add branding elements to the generated video"""
        try:
            if not logo_data:
                return video_data
            
            loop = asyncio.get_event_loop()
            
            branded_video = await loop.run_in_executor(
                None,
                self.video_processor.add_logo_watermark,
                video_data,
                logo_data,
                "bottom-right"
            )
            
            return branded_video
            
        except Exception as e:
            self.logger.warning(f"Failed to add branding: {str(e)}")
            return video_data  # Return original if branding fails
    
    def get_video_metadata(self, video_data: bytes) -> Dict[str, Any]:
        """Extract metadata from generated video"""
        try:
            import tempfile
            import os
            from moviepy.editor import VideoFileClip
            
            with tempfile.TemporaryDirectory() as temp_dir:
                video_path = os.path.join(temp_dir, "temp_video.mp4")
                
                with open(video_path, 'wb') as f:
                    f.write(video_data)
                
                with VideoFileClip(video_path) as clip:
                    metadata = {
                        'duration': clip.duration,
                        'fps': clip.fps,
                        'size': clip.size,
                        'file_size': len(video_data),
                        'has_audio': clip.audio is not None
                    }
                
                return metadata
                
        except Exception as e:
            self.logger.warning(f"Failed to extract video metadata: {str(e)}")
            return {
                'file_size': len(video_data),
                'duration': self.default_duration,
                'format': self.video_format
            }
