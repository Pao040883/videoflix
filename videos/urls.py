"""
Video URLs.
"""
from django.urls import path
from videos.views import (
    video_list,
    get_hls_manifest,
    get_hls_segment,
)

urlpatterns = [
    path('video/', video_list, name='video_list'),
    path('video/<int:movie_id>/<str:resolution>/index.m3u8', get_hls_manifest, name='hls_manifest'),
    path('video/<int:movie_id>/<str:resolution>/<str:segment>', get_hls_segment, name='hls_segment'),
]
