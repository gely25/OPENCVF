from django.db import models
from django.utils import timezone
from datetime import timedelta


from datetime import timedelta
from django.utils import timezone

class Flashcard(models.Model):
    palabra = models.CharField(max_length=100)
    traduccion = models.CharField(max_length=100)
    imagen = models.ImageField(upload_to="flashcards/", null=True, blank=True)
    next_review = models.DateField(default=timezone.now)
    interval = models.IntegerField(default=1)  # días hasta próxima revisión

    def mark_reviewed(self, success=True):
        today = timezone.now().date()
        if success:
            # aumentar intervalo (curva de repaso básica)
            self.interval = int(self.interval * 2)
        else:
            # si falló, reinicia intervalo
            self.interval = 1
        self.next_review = today + timedelta(days=self.interval)
        self.save()
        
        
    
    