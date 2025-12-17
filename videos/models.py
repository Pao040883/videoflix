from django.db import models
from django.utils.translation import gettext_lazy as _


class Genre(models.Model):
    """
    Video genre/category model.
    
    Represents video categories for classification and filtering.
    Each genre has a unique name and optional description.
    
    Attributes:
        name: Unique genre name (max 100 characters).
        description: Optional detailed description of the genre.
        created_at: Timestamp of genre creation.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("genre")
        verbose_name_plural = _("genres")
        ordering = ['name']

    def __str__(self):
        return self.name


class Video(models.Model):
    """
    Video content model for streaming platform.
    
    Stores video metadata, file references, and processing status.
    Videos are transcoded to HLS format with multiple quality variants
    for adaptive bitrate streaming.
    
    Attributes:
        title: Video title (max 255 characters).
        description: Detailed video description.
        genre: Foreign key to Genre model (nullable).
        video_file: Uploaded video file (stored in 'videos/uploads/').
        thumbnail: Optional thumbnail image (stored in 'thumbnails/').
        hls_path: Path to HLS output directory after transcoding.
        duration: Video duration in seconds (set after processing).
        is_published: Whether video is visible to users (default True).
        is_processing: Whether video is currently being transcoded (default False).
        created_at: Timestamp of video creation.
        updated_at: Timestamp of last update.
    """
    title = models.CharField(max_length=255)
    description = models.TextField()
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, related_name='videos')
    video_file = models.FileField(upload_to='videos/uploads/')
    thumbnail = models.ImageField(
        upload_to='thumbnails/', 
        null=True, 
        blank=True,
        help_text='Automatically generated from video at 5 seconds if not uploaded.'
    )
    hls_path = models.CharField(max_length=255, blank=True, null=True)
    duration = models.IntegerField(null=True, blank=True)
    is_published = models.BooleanField(default=True)
    is_processing = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("video")
        verbose_name_plural = _("videos")
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class HLSQuality(models.Model):
    """
    HLS quality variant model for adaptive bitrate streaming.
    
    Stores information about each quality variant generated during
    video transcoding. Each video can have multiple quality variants
    (480p, 720p, 1080p) for adaptive streaming.
    
    Attributes:
        video: Foreign key to Video model (cascade on delete).
        quality: Quality level ('480p', '720p', or '1080p').
        file_path: Relative path to HLS manifest file (.m3u8).
        bitrate: Video bitrate in kbps.
        created_at: Timestamp of quality variant creation.
        QUALITY_CHOICES: Available quality options.
    
    Constraints:
        unique_together: ['video', 'quality'] - One quality per video.
    """
    QUALITY_CHOICES = (
        ('480p', '480p'),
        ('720p', '720p'),
        ('1080p', '1080p'),
    )
    
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='hls_qualities')
    quality = models.CharField(max_length=10, choices=QUALITY_CHOICES)
    file_path = models.CharField(max_length=255)
    bitrate = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("HLS quality")
        verbose_name_plural = _("HLS qualities")
        unique_together = ['video', 'quality']

    def __str__(self):
        return f"{self.video.title} - {self.quality}"
