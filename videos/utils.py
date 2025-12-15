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


def build_ffmpeg_hls_command(video_path, output_file, segment_pattern, settings_dict):
    """Build FFmpeg command for HLS transcoding."""
    return [
        'ffmpeg', '-i', video_path,
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


def create_hls_quality_record(video, quality, settings_dict):
    """Create HLSQuality database record."""
    HLSQuality.objects.create(
        video=video,
        quality=quality,
        file_path=f'hls/video_{video.id}/{quality}.m3u8',
        bitrate=int(settings_dict['bitrate'].replace('k', ''))
    )


def build_thumbnail_command(video_path, thumbnail_file):
    """Build FFmpeg command for thumbnail extraction."""
    return ['ffmpeg', '-i', video_path, '-ss', '00:00:05', '-vf', 'scale=320:-1', '-frames:v', '1', '-y', thumbnail_file]


def build_ffprobe_duration_command(video_path):
    """Build FFprobe command for duration extraction."""
    return ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1:noprint_wrappers=1', video_path]


def generate_hls_streams(video):
    """Generate HLS streams with multiple quality variants (480p, 720p, 1080p)."""
    video.is_processing = True
    video.save()
    try:
        hls_dir = os.path.join(settings.HLS_OUTPUT_PATH, f'video_{video.id}')
        os.makedirs(hls_dir, exist_ok=True)
        for quality, settings_dict in QUALITY_SETTINGS.items():
            output_file = os.path.join(hls_dir, f'{quality}.m3u8')
            segment_pattern = os.path.join(hls_dir, f'{quality}_%03d.ts')
            command = build_ffmpeg_hls_command(video.video_file.path, output_file, segment_pattern, settings_dict)
            subprocess.run(command, check=True, capture_output=True)
            create_hls_quality_record(video, quality, settings_dict)
            logger.info(f"Generated {quality} stream for video {video.id}")
        video.hls_path = f'hls/video_{video.id}/'
        video.is_processing = False
        video.save()
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error for video {video.id}: {str(e)}")
        video.is_processing = False
        video.save()


def generate_thumbnail(video):
    """Generate thumbnail image from video at 5 seconds, scaled to 320px width."""
    try:
        thumbnail_dir = settings.THUMBNAIL_PATH
        os.makedirs(thumbnail_dir, exist_ok=True)
        thumbnail_filename = f'video_{video.id}.jpg'
        thumbnail_file = os.path.join(thumbnail_dir, thumbnail_filename)
        command = build_thumbnail_command(video.video_file.path, thumbnail_file)
        subprocess.run(command, check=True, capture_output=True)
        video.thumbnail = f'thumbnails/{thumbnail_filename}'
        video.save(update_fields=['thumbnail'])
        logger.info(f"Generated thumbnail for video {video.id}")
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg thumbnail error for video {video.id}: {str(e)}")


def get_video_duration(video_path):
    """Extract video duration using FFprobe, returns seconds as int or None on error."""
    try:
        command = build_ffprobe_duration_command(video_path)
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        duration = int(float(result.stdout.strip()))
        return duration
    except subprocess.CalledProcessError as e:
        logger.error(f"FFprobe error: {str(e)}")
        return None
