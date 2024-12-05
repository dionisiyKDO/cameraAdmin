from django.db import models

class Screenshot(models.Model):
    camera_id = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    file_path = models.CharField(max_length=255)

    def __str__(self):
        return f"Camera {self.camera_id} - {self.timestamp}"
