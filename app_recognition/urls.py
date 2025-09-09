from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('video/', views.video_feed, name='video_feed'),
    path('objects/', views.objects_view, name='objects_view'),
    path("speak/", views.speak_word, name="speak_word"),
    path("detect/", views.detect_objects, name="detect_objects"), 
    path("live/", views.live_view, name="live_view"),
    path("add_flashcard/", views.add_flashcard, name="add_flashcard"),


]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
