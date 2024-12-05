from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.index, name="index"),
    path("video_feed/<int:camera_id>/", views.video_feed, name="video_feed"),
    path("release_camera/<int:camera_id>/", views.release_camera, name="release_camera"),
    path("save_screenshot/<int:camera_id>/", views.save_screenshot, name="save_screenshot"),
    path("delete_screenshot/<int:screenshot_id>/", views.delete_screenshot, name="delete_screenshot"),
    path("screenshots/", views.screenshots_list, name="screenshots_list"),
]