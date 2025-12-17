"""
Helper functions for video processing.
"""
import os
import logging
from django.core.cache import cache
from django.conf import settings
from django.http import FileResponse, Http404

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
    
    # Generate thumbnail only if not manually uploaded
    if not video.thumbnail:
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


def get_video_hls_path(movie_id, resolution):
    hls_dir = os.path.join(settings.HLS_OUTPUT_PATH, f'video_{movie_id}')
    manifest_file = os.path.join(hls_dir, f'{resolution}.m3u8')
    if not os.path.exists(manifest_file):
        raise Http404("Manifest not found")
    return manifest_file


def get_hls_segment_path(movie_id, segment):
    hls_dir = os.path.join(settings.HLS_OUTPUT_PATH, f'video_{movie_id}')
    segment_file = os.path.join(hls_dir, f'{segment}')
    if not os.path.exists(segment_file):
        raise Http404("Segment not found")
    return segment_file


def create_cors_response(file_path, content_type, request, disposition=None, cache_control=None):
    response = FileResponse(open(file_path, 'rb'), content_type=content_type)
    if disposition:
        response['Content-Disposition'] = disposition
    response['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
    response['Access-Control-Allow-Credentials'] = 'true'
    if cache_control:
        response['Cache-Control'] = cache_control
    else:
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
    return response
