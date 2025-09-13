from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('video/', views.video_feed, name='video_feed'),
    path('objects/', views.objects_view, name='objects_view'),
    path("speak/", views.speak_word, name="speak_word"),
    path("live/", views.live_view, name="live_view"),
    path("add_flashcard/", views.add_flashcard, name="add_flashcard"),
    path("flashcards/", views.flashcards_list, name="flashcards_list"),
    path("flashcards/review/", views.review_flashcards, name="review_flashcards"),



]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
