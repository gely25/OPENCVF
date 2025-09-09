from django.db import models
from django.db import models
import base64
from django.core.files.base import ContentFile

class Flashcard(models.Model):
    label = models.CharField(max_length=100)
    image = models.ImageField(upload_to="flashcards/")

    def save_image_from_base64(self, b64_data):
        self.image.save(f"{self.label}.jpg", ContentFile(base64.b64decode(b64_data)), save=False)
