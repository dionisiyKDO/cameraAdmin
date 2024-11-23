from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("video_feed/<int:camera_id>/", views.video_feed, name="video_feed"),
    path("release_camera/<int:camera_id>/", views.release_camera, name="release_camera"),
]