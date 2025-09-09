from django.db import models
import base64
from django.core.files.base import ContentFile

class Flashcard(models.Model):
    label = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to="flashcards/")
    created_at = models.DateTimeField(auto_now_add=True)  # <-- agregado

    def save_image_from_base64(self, img_b64):
        import base64
        from django.core.files.base import ContentFile
        img_data = base64.b64decode(img_b64)
        self.image.save(f"{self.label}.jpg", ContentFile(img_data), save=False)

    def __str__(self):
        return self.label
