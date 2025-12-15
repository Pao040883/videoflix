"""
Video admin.
"""
from django.contrib import admin
from videos.models import Video, Genre, HLSQuality


class HLSQualityInline(admin.TabularInline):
    model = HLSQuality
    extra = 1


class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'genre', 'is_published', 'is_processing', 'created_at')
    list_filter = ('genre', 'is_published', 'is_processing', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at', 'hls_path')
    inlines = [HLSQualityInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'genre')
        }),
        ('Media', {
            'fields': ('video_file', 'thumbnail', 'duration')
        }),
        ('HLS Processing', {
            'fields': ('hls_path', 'is_processing')
        }),
        ('Publication', {
            'fields': ('is_published',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at',)


admin.site.register(Video, VideoAdmin)
admin.site.register(Genre, GenreAdmin)
admin.site.register(HLSQuality)
