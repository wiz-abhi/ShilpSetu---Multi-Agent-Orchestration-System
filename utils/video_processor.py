"""
Video processing utilities for creating marketing videos
"""

import cv2
import numpy as np
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import io
import os
from typing import List, Dict, Any, Optional, Tuple
import tempfile

from config.settings import Config
from utils.logger import setup_logger

class VideoProcessor:
    """Utility class for video processing and creation"""
    
    def __init__(self):
        self.logger = setup_logger("VideoProcessor")
        self.fps = Config.VIDEO_FPS
        self.resolution = Config.VIDEO_RESOLUTION
        self.duration = Config.VIDEO_DURATION
        self.format = Config.VIDEO_FORMAT
    
    def create_marketing_video(
        self, 
        images: List[bytes], 
        video_prompt: str,
        scene_breakdown: List[Dict[str, Any]],
        audio_style: str = "upbeat"
    ) -> bytes:
        """Create a marketing video from images and specifications"""
        try:
            self.logger.info(f"Creating marketing video with {len(images)} images")
            
            # Create temporary directory for processing
            with tempfile.TemporaryDirectory() as temp_dir:
                # Save images to temporary files
                image_paths = []
                for i, image_data in enumerate(images):
                    image_path = os.path.join(temp_dir, f"image_{i}.png")
                    with open(image_path, 'wb') as f:
                        f.write(image_data)
                    image_paths.append(image_path)
                
                # Create video clips from images
                clips = self._create_image_clips(image_paths, scene_breakdown)
                
                # Add transitions and effects
                final_clips = self._add_transitions_and_effects(clips, video_prompt)
                
                # Concatenate clips
                final_video = concatenate_videoclips(final_clips, method="compose")
                
                # Add background music (placeholder)
                final_video = self._add_background_audio(final_video, audio_style)
                
                # Add text overlays
                final_video = self._add_text_overlays(final_video, video_prompt)
                
                # Export video
                output_path = os.path.join(temp_dir, f"marketing_video.{self.format}")
                final_video.write_videofile(
                    output_path,
                    fps=self.fps,
                    codec='libx264',
                    audio_codec='aac',
                    temp_audiofile=os.path.join(temp_dir, 'temp_audio.m4a'),
                    remove_temp=True,
                    verbose=False,
                    logger=None
                )
                
                # Read the final video file
                with open(output_path, 'rb') as f:
                    video_data = f.read()
                
                self.logger.info(f"Successfully created marketing video ({len(video_data)} bytes)")
                return video_data
                
        except Exception as e:
            self.logger.error(f"Failed to create marketing video: {str(e)}")
            raise
    
    def _create_image_clips(self, image_paths: List[str], scene_breakdown: List[Dict[str, Any]]) -> List[VideoClip]:
        """Create video clips from images based on scene breakdown"""
        clips = []
        
        for i, image_path in enumerate(image_paths):
            # Determine duration for this clip
            if i < len(scene_breakdown):
                scene = scene_breakdown[i]
                duration = self._parse_duration(scene.get('time', '5s'))
            else:
                duration = self.duration / len(image_paths)
            
            # Create image clip
            clip = ImageClip(image_path, duration=duration)
            
            # Resize to target resolution
            clip = clip.resize(self.resolution)
            
            # Add zoom effect for visual interest
            if i % 2 == 0:
                clip = clip.resize(lambda t: 1 + 0.02 * t)  # Slow zoom in
            else:
                clip = clip.resize(lambda t: 1.02 - 0.02 * t)  # Slow zoom out
            
            clips.append(clip)
        
        return clips
    
    def _add_transitions_and_effects(self, clips: List[VideoClip], video_prompt: str) -> List[VideoClip]:
        """Add transitions and visual effects between clips"""
        if len(clips) <= 1:
            return clips
        
        enhanced_clips = []
        
        for i, clip in enumerate(clips):
            if i == 0:
                # First clip: fade in
                clip = clip.fadein(0.5)
            elif i == len(clips) - 1:
                # Last clip: fade out
                clip = clip.fadeout(0.5)
            else:
                # Middle clips: crossfade
                clip = clip.fadein(0.3).fadeout(0.3)
            
            # Add subtle color correction based on prompt
            if "luxury" in video_prompt.lower() or "premium" in video_prompt.lower():
                # Enhance contrast and saturation for luxury feel
                clip = clip.fx(colorx, 1.1).fx(lum_contrast, 0, 10, 128)
            elif "natural" in video_prompt.lower() or "organic" in video_prompt.lower():
                # Warmer tones for natural products
                clip = clip.fx(colorx, 0.9)
            
            enhanced_clips.append(clip)
        
        return enhanced_clips
    
    def _add_background_audio(self, video: VideoClip, audio_style: str) -> VideoClip:
        """Add background audio to the video (placeholder implementation)"""
        try:
            # In production, you would:
            # 1. Select appropriate background music based on audio_style
            # 2. Load the audio file
            # 3. Adjust volume and duration
            # 4. Composite with video
            
            # For now, we'll create a silent audio track
            # This ensures the video has an audio track for compatibility
            silent_audio = AudioClip(lambda t: [0, 0], duration=video.duration, fps=22050)
            video = video.set_audio(silent_audio)
            
            self.logger.info(f"Added {audio_style} background audio (silent placeholder)")
            return video
            
        except Exception as e:
            self.logger.warning(f"Failed to add background audio: {str(e)}")
            return video
    
    def _add_text_overlays(self, video: VideoClip, video_prompt: str) -> VideoClip:
        """Add text overlays to the video"""
        try:
            # Extract key phrases from the prompt for overlay text
            overlay_texts = self._extract_overlay_texts(video_prompt)
            
            if not overlay_texts:
                return video
            
            # Create text clips
            text_clips = []
            
            for i, text in enumerate(overlay_texts):
                # Calculate timing for text appearance
                start_time = (video.duration / len(overlay_texts)) * i
                duration = min(3.0, video.duration / len(overlay_texts))
                
                # Create text clip
                text_clip = TextClip(
                    text,
                    fontsize=60,
                    color='white',
                    font='Arial-Bold',
                    stroke_color='black',
                    stroke_width=2
                ).set_position(('center', 'bottom')).set_start(start_time).set_duration(duration)
                
                # Add fade in/out
                text_clip = text_clip.fadein(0.5).fadeout(0.5)
                
                text_clips.append(text_clip)
            
            # Composite text over video
            final_video = CompositeVideoClip([video] + text_clips)
            
            self.logger.info(f"Added {len(text_clips)} text overlays")
            return final_video
            
        except Exception as e:
            self.logger.warning(f"Failed to add text overlays: {str(e)}")
            return video
    
    def _parse_duration(self, time_str: str) -> float:
        """Parse duration string like '0-5s' or '5s' to float seconds"""
        try:
            if '-' in time_str:
                # Range format like "0-5s"
                end_time = time_str.split('-')[1]
                return float(end_time.replace('s', ''))
            else:
                # Simple format like "5s"
                return float(time_str.replace('s', ''))
        except:
            return 5.0  # Default duration
    
    def _extract_overlay_texts(self, video_prompt: str) -> List[str]:
        """Extract key phrases from video prompt for text overlays"""
        # Simple keyword extraction for overlay text
        keywords = []
        
        if "handcrafted" in video_prompt.lower():
            keywords.append("Handcrafted")
        if "artisan" in video_prompt.lower():
            keywords.append("Artisan Made")
        if "unique" in video_prompt.lower():
            keywords.append("Unique Design")
        if "quality" in video_prompt.lower():
            keywords.append("Premium Quality")
        if "authentic" in video_prompt.lower():
            keywords.append("Authentic")
        
        # Add a call-to-action
        if keywords:
            keywords.append("Shop Now")
        
        return keywords[:3]  # Limit to 3 overlays
    
    def create_slideshow_video(self, images: List[bytes], duration_per_image: float = 3.0) -> bytes:
        """Create a simple slideshow video from images"""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Save images
                image_paths = []
                for i, image_data in enumerate(images):
                    image_path = os.path.join(temp_dir, f"slide_{i}.png")
                    with open(image_path, 'wb') as f:
                        f.write(image_data)
                    image_paths.append(image_path)
                
                # Create clips
                clips = []
                for image_path in image_paths:
                    clip = ImageClip(image_path, duration=duration_per_image)
                    clip = clip.resize(self.resolution)
                    clip = clip.fadein(0.5).fadeout(0.5)
                    clips.append(clip)
                
                # Concatenate
                final_video = concatenate_videoclips(clips, method="compose")
                
                # Export
                output_path = os.path.join(temp_dir, f"slideshow.{self.format}")
                final_video.write_videofile(
                    output_path,
                    fps=self.fps,
                    codec='libx264',
                    verbose=False,
                    logger=None
                )
                
                with open(output_path, 'rb') as f:
                    return f.read()
                    
        except Exception as e:
            self.logger.error(f"Failed to create slideshow video: {str(e)}")
            raise
    
    def add_logo_watermark(self, video_data: bytes, logo_data: bytes, position: str = "bottom-right") -> bytes:
        """Add logo watermark to video"""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Save video and logo
                video_path = os.path.join(temp_dir, "input_video.mp4")
                logo_path = os.path.join(temp_dir, "logo.png")
                output_path = os.path.join(temp_dir, "watermarked_video.mp4")
                
                with open(video_path, 'wb') as f:
                    f.write(video_data)
                with open(logo_path, 'wb') as f:
                    f.write(logo_data)
                
                # Load video and logo
                video = VideoFileClip(video_path)
                logo = ImageClip(logo_path, duration=video.duration)
                
                # Resize logo (10% of video width)
                logo_width = int(self.resolution[0] * 0.1)
                logo = logo.resize(width=logo_width)
                
                # Position logo
                if position == "bottom-right":
                    logo = logo.set_position(('right', 'bottom')).set_margin(20)
                elif position == "bottom-left":
                    logo = logo.set_position(('left', 'bottom')).set_margin(20)
                elif position == "top-right":
                    logo = logo.set_position(('right', 'top')).set_margin(20)
                elif position == "top-left":
                    logo = logo.set_position(('left', 'top')).set_margin(20)
                
                # Composite
                final_video = CompositeVideoClip([video, logo])
                
                # Export
                final_video.write_videofile(
                    output_path,
                    fps=self.fps,
                    codec='libx264',
                    verbose=False,
                    logger=None
                )
                
                with open(output_path, 'rb') as f:
                    return f.read()
                    
        except Exception as e:
            self.logger.error(f"Failed to add watermark: {str(e)}")
            return video_data  # Return original if watermarking fails
