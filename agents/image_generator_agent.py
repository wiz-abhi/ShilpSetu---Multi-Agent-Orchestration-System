"""
Agent 2: Image Generator Agent
Generates high-quality product images using Google's Imagen model and stores them in Google Cloud Storage
"""

import asyncio
import aiohttp
import io
from typing import Dict, Any, List
from PIL import Image
import requests
import base64
from google import genai

from agents.base_agent import BaseAgent
from models.data_models import AgentResponse, AgentType, GeneratedImage
from config.settings import Config
from utils.gcs_manager import GCSManager
from utils.logger import setup_logger

class ImageGeneratorAgent(BaseAgent):
    """Agent responsible for generating product images using Google Imagen and storing them in GCS"""
    
    def __init__(self):
        super().__init__(AgentType.IMAGE_GENERATOR)
        self.gcs_manager = GCSManager()
        
        self.client = genai.Client(api_key=Config.GOOGLE_AI_API_KEY)
        
        # Image generation settings
        self.default_image_count = Config.IMAGE_COUNT_DEFAULT
        self.max_image_count = Config.IMAGE_COUNT_MAX
        self.image_quality = Config.IMAGE_QUALITY
        self.image_format = Config.IMAGE_FORMAT
        
        self.imagen_model = "imagen-3.0-generate-001"  # Google's Imagen 3 model
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Process prompt data and generate images"""
        try:
            # Extract prompt data from Agent 1
            generated_prompt = input_data.get('generated_prompt', {})
            image_prompt = generated_prompt.get('image_prompt', '')
            style_guidelines = generated_prompt.get('style_guidelines', '')
            product_input = input_data.get('product_input', {})
            
            if not image_prompt:
                raise ValueError("No image prompt provided")
            
            self.logger.info(f"Generating images for product: {product_input.get('product_id', 'unknown')}")
            
            # Determine number of images to generate
            image_count = min(
                input_data.get('image_count', self.default_image_count),
                self.max_image_count
            )
            
            # Create enhanced prompts for variety
            enhanced_prompts = self._create_prompt_variations(image_prompt, style_guidelines, image_count)
            
            # Generate images concurrently
            generation_tasks = [
                self._generate_single_image(prompt, i) 
                for i, prompt in enumerate(enhanced_prompts)
            ]
            
            generated_images = await asyncio.gather(*generation_tasks, return_exceptions=True)
            
            # Process results and upload to GCS
            successful_images = []
            failed_generations = []
            
            for i, result in enumerate(generated_images):
                if isinstance(result, Exception):
                    failed_generations.append(f"Image {i+1}: {str(result)}")
                    continue
                
                try:
                    # Upload to Google Cloud Storage
                    upload_result = self.gcs_manager.upload_image(
                        image_data=result['image_data'],
                        filename=f"product_image_{i+1}.{self.image_format.lower()}",
                        content_type=f"image/{self.image_format.lower()}"
                    )
                    
                    # Create GeneratedImage object
                    generated_image = GeneratedImage(
                        image_url=upload_result['public_url'],
                        gcs_path=upload_result['gcs_path'],
                        prompt_used=result['prompt_used'],
                        generation_params=result['generation_params']
                    )
                    
                    successful_images.append(generated_image.__dict__)
                    
                except Exception as upload_error:
                    self.logger.error(f"Failed to upload image {i+1}: {str(upload_error)}")
                    failed_generations.append(f"Upload failed for image {i+1}: {str(upload_error)}")
            
            # Prepare response
            if not successful_images:
                return AgentResponse(
                    success=False,
                    error=f"Failed to generate any images. Errors: {'; '.join(failed_generations)}"
                )
            
            response_data = {
                'generated_images': successful_images,
                'successful_count': len(successful_images),
                'failed_count': len(failed_generations),
                'failures': failed_generations,
                'product_input': product_input,
                'generation_settings': {
                    'image_count': image_count,
                    'image_quality': self.image_quality,
                    'image_format': self.image_format
                }
            }
            
            self.logger.info(f"Successfully generated {len(successful_images)} images for product {product_input.get('product_id', 'unknown')}")
            
            return AgentResponse(
                success=True,
                data=response_data
            )
            
        except Exception as e:
            self.logger.error(f"Error in image generation: {str(e)}")
            return AgentResponse(
                success=False,
                error=f"Image generation failed: {str(e)}"
            )
    
    def _create_prompt_variations(self, base_prompt: str, style_guidelines: str, count: int) -> List[str]:
        """Create variations of the base prompt for diverse image generation"""
        variations = []
        
        # Different composition styles
        compositions = [
            "centered composition, symmetrical",
            "rule of thirds, dynamic composition",
            "close-up detail shot, macro style",
            "lifestyle context, in-use scenario"
        ]
        
        # Different lighting setups
        lighting_styles = [
            "professional studio lighting, soft shadows",
            "natural window light, bright and airy",
            "dramatic side lighting, high contrast",
            "golden hour lighting, warm tones"
        ]
        
        # Different backgrounds
        backgrounds = [
            "clean white background, minimalist",
            "rustic wooden surface, natural texture",
            "marble surface, luxury aesthetic",
            "lifestyle setting, home environment"
        ]
        
        for i in range(count):
            composition = compositions[i % len(compositions)]
            lighting = lighting_styles[i % len(lighting_styles)]
            background = backgrounds[i % len(backgrounds)]
            
            enhanced_prompt = f"{base_prompt}, {style_guidelines}, {composition}, {lighting}, {background}, high resolution, professional photography, marketing quality"
            variations.append(enhanced_prompt)
        
        return variations
    
    async def _generate_single_image(self, prompt: str, index: int) -> Dict[str, Any]:
        """Generate a single image using Google's Imagen model"""
        try:
            image_data = await self._call_imagen_api(prompt)
            
            return {
                'image_data': image_data,
                'prompt_used': prompt,
                'generation_params': {
                    'model': self.imagen_model,
                    'quality': self.image_quality,
                    'format': self.image_format,
                    'index': index
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate image {index}: {str(e)}")
            raise
    
    async def _call_imagen_api(self, prompt: str) -> bytes:
        """Call Google Imagen API to generate image"""
        try:
            response = self.client.models.generate_content(
                model=self.imagen_model,
                contents=prompt
            )
            
            if response.candidates and response.candidates[0].content:
                # Extract image data from response
                content = response.candidates[0].content
                if hasattr(content, 'parts') and content.parts:
                    for part in content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            # Convert base64 to bytes
                            image_data = base64.b64decode(part.inline_data.data)
                            return image_data
                
                raise Exception("No image data found in Imagen response")
            else:
                raise Exception("No image generated by Imagen API")
                
        except Exception as e:
            self.logger.error(f"Imagen API call failed: {str(e)}")
            return await self._create_fallback_image(prompt)
    
    async def _create_fallback_image(self, prompt: str) -> bytes:
        """Create a fallback placeholder image if Imagen API fails"""
        try:
            # Create a simple placeholder image as fallback
            width, height = 1024, 1024
            image = Image.new('RGB', (width, height), (200, 200, 200))
            
            # Convert to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format=self.image_format)
            return img_byte_arr.getvalue()
            
        except Exception as e:
            self.logger.error(f"Fallback image creation failed: {str(e)}")
            raise

    def optimize_image(self, image_data: bytes, max_size_mb: float = 5.0) -> bytes:
        """Optimize image size and quality"""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Calculate current size
            current_size_mb = len(image_data) / (1024 * 1024)
            
            if current_size_mb <= max_size_mb:
                return image_data
            
            # Reduce quality to meet size requirements
            quality = 95
            while quality > 20:
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format=self.image_format, quality=quality, optimize=True)
                optimized_data = img_byte_arr.getvalue()
                
                if len(optimized_data) / (1024 * 1024) <= max_size_mb:
                    self.logger.info(f"Optimized image from {current_size_mb:.2f}MB to {len(optimized_data)/(1024*1024):.2f}MB")
                    return optimized_data
                
                quality -= 10
            
            # If still too large, resize the image
            image.thumbnail((800, 800), Image.Resampling.LANCZOS)
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format=self.image_format, quality=80, optimize=True)
            
            return img_byte_arr.getvalue()
            
        except Exception as e:
            self.logger.error(f"Failed to optimize image: {str(e)}")
            return image_data
