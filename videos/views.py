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


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def video_list(request):
    """
    Retrieve list of all published videos with Redis caching.
    
    Returns a cached list of published videos ordered by creation date.
    Cache is valid for 5 minutes to reduce database queries.
    
    Args:
        request: HTTP request from authenticated user.
    
    Returns:
        Response: HTTP 200 with serialized list of published videos.
    
    Cache:
        Key: 'video_list_published'
        Timeout: 300 seconds (5 minutes)
    """
    cache_key = 'video_list_published'
    videos_data = cache.get(cache_key)
    
    if videos_data is None:
        videos = Video.objects.filter(is_published=True).order_by('-created_at')
        serializer = VideoListSerializer(
            videos,
            many=True,
            context={'request': request}
        )
        videos_data = serializer.data
        cache.set(cache_key, videos_data, timeout=300)  # Cache for 5 minutes
    
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
    """
    Serve HLS manifest file (.m3u8) for video streaming.
    
    Returns the HLS playlist file for the specified video and resolution.
    Includes CORS headers to enable cross-origin video playback.
    
    Args:
        request: HTTP request from authenticated user.
        movie_id: ID of the video.
        resolution: Video quality ('480p', '720p', or '1080p').
    
    Returns:
        FileResponse: HLS manifest file with appropriate content type.
    
    Raises:
        Http404: If video or manifest file not found.
    """
    try:
        video = Video.objects.get(id=movie_id, is_published=True)
        
        hls_dir = os.path.join(settings.HLS_OUTPUT_PATH, f'video_{movie_id}')
        manifest_file = os.path.join(hls_dir, f'{resolution}.m3u8')
        
        if not os.path.exists(manifest_file):
            raise Http404("Manifest not found")
        
        response = FileResponse(open(manifest_file, 'rb'), content_type='application/vnd.apple.mpegurl')
        response['Content-Disposition'] = f'inline; filename="{resolution}.m3u8"'
        response['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
    except Video.DoesNotExist:
        raise Http404("Video not found")


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_hls_segment(request, movie_id, resolution, segment):
    """
    Serve HLS video segment (.ts file) for streaming.
    
    Returns the requested video segment for HLS adaptive bitrate streaming.
    Includes CORS headers to enable cross-origin video playback.
    
    Args:
        request: HTTP request from authenticated user.
        movie_id: ID of the video.
        resolution: Video quality ('480p', '720p', or '1080p').
        segment: Segment filename (e.g., 'segment0.ts').
    
    Returns:
        FileResponse: Video segment with MPEG-TS content type.
    
    Raises:
        Http404: If video or segment file not found.
    """
    try:
        video = Video.objects.get(id=movie_id, is_published=True)
        
        hls_dir = os.path.join(settings.HLS_OUTPUT_PATH, f'video_{movie_id}')
        segment_file = os.path.join(hls_dir, f'{segment}')
        
        if not os.path.exists(segment_file):
            raise Http404("Segment not found")
        
        response = FileResponse(open(segment_file, 'rb'), content_type='video/MP2T')
        response['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Accept-Ranges'] = 'bytes'
        response['Cache-Control'] = 'public, max-age=31536000, immutable'
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
