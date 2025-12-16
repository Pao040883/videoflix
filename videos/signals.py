"""
Video signals for automatic background processing.
"""
import os
import shutil
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.conf import settings
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


@receiver(pre_delete, sender=Video)
def delete_video_files(sender, instance, **kwargs):
    """
    Delete associated video files when Video object is deleted.
    Removes original video file, thumbnail, and HLS streams.
    """
    if instance.video_file:
        if os.path.isfile(instance.video_file.path):
            os.remove(instance.video_file.path)
    
    if instance.thumbnail:
        thumbnail_path = os.path.join(settings.MEDIA_ROOT, str(instance.thumbnail))
        if os.path.isfile(thumbnail_path):
            os.remove(thumbnail_path)
    
    if instance.hls_path:
        hls_dir = os.path.join(settings.HLS_OUTPUT_PATH, f'video_{instance.id}')
        if os.path.isdir(hls_dir):
            shutil.rmtree(hls_dir)
