from django.db import models
import base64
from django.core.files.base import ContentFile



class Flashcard(models.Model):
    palabra = models.CharField(max_length=100)
    traduccion = models.CharField(max_length=100)
    imagen = models.ImageField(upload_to='flashcards/', blank=True, null=True)

    def save_image_from_base64(self, img_b64):
        if img_b64:
            format, imgstr = img_b64.split(';base64,') if ';base64,' in img_b64 else ('jpeg', img_b64)
            ext = format.split('/')[-1] if '/' in format else 'jpg'
            self.imagen.save(f"{self.palabra}.{ext}", ContentFile(base64.b64decode(imgstr)), save=False)
