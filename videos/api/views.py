"""
Video views.
"""
import os
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.http import FileResponse, Http404
from django.conf import settings
from django.core.cache import cache
from videos.models import Video, Genre
from videos.api.serializers import VideoListSerializer, VideoDetailSerializer, GenreSerializer
from videos.functions import get_video_hls_path, get_hls_segment_path, create_cors_response


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def video_list(request):
    """
    Retrieve list of all published videos with Redis caching.
    
    Returns cached video list if available (5-minute TTL), otherwise queries
    database for all published videos ordered by creation date (newest first).
    Includes basic video information: title, description, thumbnail, and category.
    
    Args:
        request: HTTP GET request from authenticated user.
    
    Returns:
        Response: HTTP 200 with serialized video list.
    """
    cache_key = 'video_list_published'
    videos_data = cache.get(cache_key)
    if videos_data is None:
        videos = Video.objects.filter(is_published=True).order_by('-created_at')
        serializer = VideoListSerializer(videos, many=True, context={'request': request})
        videos_data = serializer.data
        cache.set(cache_key, videos_data, timeout=300)
    return Response(videos_data, status=200)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_hls_manifest(request, movie_id, resolution):
    """
    Serve HLS manifest file (.m3u8) for video streaming.
    
    Returns the HLS master playlist or variant playlist for the specified
    video and resolution. Playlist contains references to .ts segments.
    Response includes CORS headers and appropriate content type.
    
    Args:
        request: HTTP GET request from authenticated user.
        movie_id: Video primary key.
        resolution: Quality variant (480p, 720p, or 1080p).
    
    Returns:
        FileResponse: HLS manifest with application/vnd.apple.mpegurl content type.
        
    Raises:
        Http404: If video not found or not published.
    """
    try:
        video = Video.objects.get(id=movie_id, is_published=True)
        manifest_file = get_video_hls_path(movie_id, resolution)
        response = create_cors_response(manifest_file, 'application/vnd.apple.mpegurl', request, disposition=f'inline; filename="{resolution}.m3u8"')
        return response
    except Video.DoesNotExist:
        raise Http404("Video not found")


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_hls_segment(request, movie_id, resolution, segment):
    """
    Serve HLS video segment (.ts file) for streaming.
    
    Returns individual video segment (.ts file) as part of HLS adaptive
    bitrate streaming. Segments are cached by browser (immutable, 1-year TTL)
    and support byte-range requests for efficient streaming.
    
    Args:
        request: HTTP GET request from authenticated user.
        movie_id: Video primary key.
        resolution: Quality variant (480p, 720p, or 1080p).
        segment: Segment filename (e.g., '480p_001.ts').
    
    Returns:
        FileResponse: Video segment with video/MP2T content type.
        
    Raises:
        Http404: If video or segment not found.
    """
    try:
        video = Video.objects.get(id=movie_id, is_published=True)
        segment_file = get_hls_segment_path(movie_id, segment)
        response = create_cors_response(segment_file, 'video/MP2T', request, cache_control='public, max-age=31536000, immutable')
        response['Accept-Ranges'] = 'bytes'
        return response
    except Video.DoesNotExist:
        raise Http404("Video not found")
