from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Flashcard

@admin.register(Flashcard)
class FlashcardAdmin(admin.ModelAdmin):
    list_display = ("label", "created_at")
