"""
Video tasks for background processing.
"""
import django_rq
from videos.models import Video
from videos.functions import process_video, mark_video_processing_failed


def process_video_task(video_id):
    """
    Background task to process uploaded video.
    
    Args:
        video_id: Primary key of the Video object to process.
    
    Returns:
        None
    """
    try:
        process_video(video_id)
    except Video.DoesNotExist:
        pass
    except Exception:
        mark_video_processing_failed(video_id)


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
