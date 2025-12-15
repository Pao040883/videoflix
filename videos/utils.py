"""
Video utilities for HLS processing and video handling.
"""
import os
import subprocess
import logging
from django.conf import settings
from videos.models import Video, HLSQuality

logger = logging.getLogger(__name__)

QUALITY_SETTINGS = {
    '480p': {
        'scale': '854:480',
        'bitrate': '1500k',
        'maxrate': '1750k',
        'bufsize': '3500k',
    },
    '720p': {
        'scale': '1280:720',
        'bitrate': '3500k',
        'maxrate': '4000k',
        'bufsize': '8000k',
    },
    '1080p': {
        'scale': '1920:1080',
        'bitrate': '6500k',
        'maxrate': '7500k',
        'bufsize': '15000k',
    },
}


def generate_hls_streams(video):
    """
    Generate HLS streams with multiple quality variants.
    
    Transcodes the uploaded video to HLS format with three quality levels
    (480p, 720p, 1080p) using FFmpeg. Each variant includes adaptive bitrate
    settings optimized for streaming.
    
    Args:
        video: Video model instance to process.
    
    Returns:
        None
    
    Side Effects:
        - Sets video.is_processing = True at start
        - Creates HLS directory: media/hls/video_{id}/
        - Generates .m3u8 playlist and .ts segments for each quality
        - Creates HLSQuality objects for each variant
        - Updates video.hls_path and video.is_processing fields
    
    Raises:
        subprocess.CalledProcessError: If FFmpeg transcoding fails.
    
    Quality Settings:
        - 480p: 854x480, 1500k bitrate, maxrate 1750k
        - 720p: 1280x720, 3500k bitrate, maxrate 4000k
        - 1080p: 1920x1080, 6500k bitrate, maxrate 7500k
    """
    video.is_processing = True
    video.save()

    try:
        video_path = video.video_file.path
        hls_dir = os.path.join(settings.HLS_OUTPUT_PATH, f'video_{video.id}')
        os.makedirs(hls_dir, exist_ok=True)

        for quality, settings_dict in QUALITY_SETTINGS.items():
            output_file = os.path.join(hls_dir, f'{quality}.m3u8')
            segment_pattern = os.path.join(hls_dir, f'{quality}_%03d.ts')
            command = [
                'ffmpeg',
                '-i', video_path,
                '-vf', f"scale={settings_dict['scale']}",
                '-b:v', settings_dict['bitrate'],
                '-maxrate', settings_dict['maxrate'],
                '-bufsize', settings_dict['bufsize'],
                '-hls_time', '10',
                '-hls_list_size', '0',
                '-hls_segment_filename', segment_pattern,
                '-hls_flags', 'independent_segments',
                '-f', 'hls',
                output_file
            ]
            subprocess.run(command, check=True, capture_output=True)
            HLSQuality.objects.create(
                video=video,
                quality=quality,
                file_path=f'hls/video_{video.id}/{quality}.m3u8',
                bitrate=int(settings_dict['bitrate'].replace('k', ''))
            )
            logger.info(f"Generated {quality} stream for video {video.id}")

        video.hls_path = f'hls/video_{video.id}/'
        video.is_processing = False
        video.save()

    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error for video {video.id}: {str(e)}")
        video.is_processing = False
        video.save()


def generate_thumbnail(video):
    """
    Generate thumbnail image from video.
    
    Extracts a single frame at 5 seconds into the video and scales it
    to 320px width for use as a thumbnail preview.
    
    Args:
        video: Video model instance to process.
    
    Returns:
        None
    
    Side Effects:
        - Creates thumbnail directory: media/thumbnails/
        - Generates JPG image: video_{id}.jpg
        - Updates video.thumbnail field with relative path
    
    Raises:
        subprocess.CalledProcessError: If FFmpeg extraction fails.
    
    Thumbnail Settings:
        - Timestamp: 00:00:05 (5 seconds)
        - Scale: 320px width (height auto-calculated)
        - Format: JPEG
    """
    try:
        video_path = video.video_file.path
        thumbnail_dir = settings.THUMBNAIL_PATH
        os.makedirs(thumbnail_dir, exist_ok=True)

        thumbnail_filename = f'video_{video.id}.jpg'
        thumbnail_file = os.path.join(thumbnail_dir, thumbnail_filename)
        command = [
            'ffmpeg',
            '-i', video_path,
            '-ss', '00:00:05',
            '-vf', 'scale=320:-1',
            '-frames:v', '1',
            '-y',
            thumbnail_file
        ]
        subprocess.run(command, check=True, capture_output=True)
        
        # Save relative path to video model
        video.thumbnail = f'thumbnails/{thumbnail_filename}'
        video.save(update_fields=['thumbnail'])
        logger.info(f"Generated thumbnail for video {video.id}")

    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg thumbnail error for video {video.id}: {str(e)}")


def get_video_duration(video_path):
    """
    Extract video duration using FFprobe.
    
    Uses FFprobe to read the video file's duration metadata.
    
    Args:
        video_path: Absolute file path to the video file.
    
    Returns:
        int: Video duration in seconds (rounded down).
        None: If FFprobe fails or duration cannot be determined.
    
    Raises:
        subprocess.CalledProcessError: If FFprobe execution fails (caught internally).
    
    Note:
        Uses FFprobe with minimal output format to extract only duration value.
    """
    try:
        command = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1:noprint_wrappers=1',
            video_path
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        duration = int(float(result.stdout.strip()))
        return duration
    except subprocess.CalledProcessError as e:
        logger.error(f"FFprobe error: {str(e)}")
        return None
