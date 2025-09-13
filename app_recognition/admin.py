from django.contrib import admin
from .models import Flashcard

@admin.register(Flashcard)
class FlashcardAdmin(admin.ModelAdmin):
    list_display = ('palabra', 'traduccion', 'imagen')  # solo los campos que tienes
