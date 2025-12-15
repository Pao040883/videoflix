"""
Helper functions for video processing.
"""
import logging
from django.core.cache import cache

from videos.models import Video
from videos.utils import get_video_duration, generate_thumbnail, generate_hls_streams

logger = logging.getLogger(__name__)


def process_video(video_id):
    """
    Process video: extract duration, generate thumbnail and HLS streams.
    
    Args:
        video_id: Primary key of Video object.
    
    Returns:
        None
    
    Side Effects:
        Updates Video fields and invalidates cache.
    """
    video = Video.objects.get(id=video_id)
    duration = get_video_duration(video.video_file.path)
    video.duration = duration
    video.save(update_fields=['duration'])
    
    generate_thumbnail(video)
    generate_hls_streams(video)
    
    video.is_processing = False
    video.save(update_fields=['is_processing'])
    cache.delete('video_list_published')


def mark_video_processing_failed(video_id):
    """
    Mark video as processing failed.
    
    Args:
        video_id: Primary key of Video object.
    
    Returns:
        None
    """
    try:
        video = Video.objects.get(id=video_id)
        video.is_processing = False
        video.save(update_fields=['is_processing'])
    except Video.DoesNotExist:
        pass
