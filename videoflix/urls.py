"""
URL configuration for videoflix project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('users.urls')),
    path('api/', include('videos.urls')),
    path('django-rq/', include('django_rq.urls')),
]

# Media files - auch in Produktion über Django ausliefern (Nginx als Proxy)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Static files nur im DEBUG-Modus (in Produktion über WhiteNoise)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
