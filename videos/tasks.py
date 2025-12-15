"""
Video tasks for background processing.
"""
import django_rq
from videos.models import Video
from videos.utils import generate_hls_streams, generate_thumbnail, get_video_duration


def process_video_task(video_id):
    """
    Background task to process uploaded video.
    
    Performs complete video processing pipeline including:
    1. Extract video duration using FFprobe
    2. Generate thumbnail from video frame
    3. Transcode video to HLS format with multiple quality variants
    4. Update video status and invalidate cache
    
    Args:
        video_id: Primary key of the Video object to process.
    
    Returns:
        None
    
    Side Effects:
        - Updates Video.duration, Video.thumbnail, Video.is_processing fields
        - Creates HLSQuality objects for each transcoded variant
        - Invalidates 'video_list_published' cache key
        - Generates HLS files in media/hls/ directory
        - Generates thumbnail in media/thumbnails/ directory
    
    Error Handling:
        Sets is_processing=False on any exception to prevent stuck videos.
    """
    try:
        video = Video.objects.get(id=video_id)
        duration = get_video_duration(video.video_file.path)
        video.duration = duration
        video.save(update_fields=['duration'])

        generate_thumbnail(video)
        generate_hls_streams(video)
        
        video.is_processing = False
        video.save(update_fields=['is_processing'])
        
        # Invalidate cache after video processing completes
        from django.core.cache import cache
        cache.delete('video_list_published')
    except Video.DoesNotExist:
        pass
    except Exception as e:
        # Mark processing as failed if error occurs
        try:
            video = Video.objects.get(id=video_id)
            video.is_processing = False
            video.save(update_fields=['is_processing'])
        except:
            pass


def enqueue_video_processing(video_id):
    """
    Enqueue video processing task in Redis queue.
    
    Adds video processing job to the default RQ queue for asynchronous
    execution by background workers.
    
    Args:
        video_id: Primary key of the Video object to process.
    
    Returns:
        None
    
    Note:
        Task is executed by django-rq worker process.
    """
    queue = django_rq.get_queue('default')
    queue.enqueue(process_video_task, video_id)
