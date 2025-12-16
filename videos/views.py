"""
Video views.
"""
import os
from rest_framework import generics, permissions, filters
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.http import FileResponse, Http404
from django.conf import settings
from django.core.cache import cache
from videos.models import Video, Genre
from videos.serializers import VideoListSerializer, VideoDetailSerializer, GenreSerializer
from videos.functions import get_video_hls_path, get_hls_segment_path, create_cors_response


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def video_list(request):
    """Retrieve list of all published videos with Redis caching."""
    cache_key = 'video_list_published'
    videos_data = cache.get(cache_key)
    if videos_data is None:
        videos = Video.objects.filter(is_published=True).order_by('-created_at')
        serializer = VideoListSerializer(videos, many=True, context={'request': request})
        videos_data = serializer.data
        cache.set(cache_key, videos_data, timeout=300)
    return Response(videos_data, status=200)


class VideoDetailView(generics.RetrieveAPIView):
    """
    API view for retrieving detailed information about a single video.
    
    Returns comprehensive video details including HLS qualities, duration,
    thumbnail, and category information. Only published videos are accessible.
    
    Attributes:
        queryset: Published videos only.
        serializer_class: VideoDetailSerializer with HLS quality data.
        permission_classes: [IsAuthenticated] - Authentication required.
    """
    queryset = Video.objects.filter(is_published=True)
    serializer_class = VideoDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        """Pass request context to serializer for building absolute URLs."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_hls_manifest(request, movie_id, resolution):
    """Serve HLS manifest file (.m3u8) for video streaming."""
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
    """Serve HLS video segment (.ts file) for streaming."""
    try:
        video = Video.objects.get(id=movie_id, is_published=True)
        segment_file = get_hls_segment_path(movie_id, segment)
        response = create_cors_response(segment_file, 'video/MP2T', request, cache_control='public, max-age=31536000, immutable')
        response['Accept-Ranges'] = 'bytes'
        return response
    except Video.DoesNotExist:
        raise Http404("Video not found")


class GenreListView(generics.ListAPIView):
    """
    API view for retrieving list of all video genres.
    
    Returns all available video categories for filtering and navigation.
    
    Attributes:
        queryset: All Genre objects.
        serializer_class: GenreSerializer.
        permission_classes: [IsAuthenticated] - Authentication required.
    """
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [permissions.IsAuthenticated]
