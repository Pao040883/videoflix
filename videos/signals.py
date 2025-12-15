"""
Video signals for automatic background processing.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from videos.models import Video
from videos.tasks import enqueue_video_processing


@receiver(post_save, sender=Video)
def trigger_video_processing(sender, instance, created, **kwargs):
    """
    Automatically triggers background video processing after a video is created.
    Generates thumbnail, HLS streams, and calculates duration.
    """
    if created and instance.video_file:
        instance.is_processing = True
        instance.save(update_fields=['is_processing'])
        enqueue_video_processing(instance.id)
