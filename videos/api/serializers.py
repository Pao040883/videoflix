"""
Video serializers.
"""
from rest_framework import serializers
from videos.models import Video, Genre, HLSQuality


class GenreSerializer(serializers.ModelSerializer):
    """
    Serializer for video genre/category data.
    
    Provides basic genre information for categorizing videos.
    """
    class Meta:
        model = Genre
        fields = ['id', 'name', 'description']


class HLSQualitySerializer(serializers.ModelSerializer):
    """
    Serializer for HLS quality variant data.
    
    Provides information about available quality options for adaptive
    bitrate streaming (480p, 720p, 1080p).
    """
    class Meta:
        model = HLSQuality
        fields = ['quality', 'file_path', 'bitrate']


class VideoListSerializer(serializers.ModelSerializer):
    """
    Serializer for video list view with basic information.
    
    Provides essential video data for list display including title,
    description, thumbnail, and category. Uses computed fields for
    category name and absolute thumbnail URL.
    """
    category = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ['id', 'title', 'description', 'thumbnail_url', 'category', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_category(self, obj):
        return obj.genre.name if obj.genre else None

    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        return None


class VideoDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed video view with streaming information.
    
    Provides comprehensive video data including HLS quality variants,
    duration, and all metadata. Includes computed fields for category
    name, absolute thumbnail URL, and nested HLS quality data.
    """
    category = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    hls_qualities = HLSQualitySerializer(many=True, read_only=True)

    class Meta:
        model = Video
        fields = [
            'id',
            'title',
            'description',
            'category',
            'thumbnail_url',
            'duration',
            'hls_path',
            'hls_qualities',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'hls_path', 'hls_qualities']

    def get_category(self, obj):
        return obj.genre.name if obj.genre else None

    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        return None
