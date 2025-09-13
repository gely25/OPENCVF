from django.http import StreamingHttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from ultralytics import YOLO
import cv2
import json
import base64
import numpy as np
from .models import Flashcard
from gtts import gTTS
import io

from googletrans import Translator
translator = Translator()


# ==========================
# Cargar modelo YOLOv8 (nano)
# ==========================
model = YOLO("yolov8n.pt")

# Guardamos las últimas detecciones para usarlas después
last_labels = []
last_boxes = []  # guardamos también las cajas (x1, y1, x2, y2)
last_frame = None


# ==========================
# Streaming de cámara con detección
# ==========================
def gen_frames():
    global last_labels, last_boxes, last_frame
    camera = cv2.VideoCapture(0)

    while True:
        success, frame = camera.read()
        if not success:
            break

        results = model(frame)

        labels = []
        boxes = []
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                label = model.names[cls_id]
                labels.append(label)

                # Coordenadas del objeto detectado
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                boxes.append((label, x1, y1, x2, y2))

        last_labels = list(set(labels))
        last_boxes = boxes
        last_frame = frame.copy()

        annotated_frame = results[0].plot()
        ret, buffer = cv2.imencode(".jpg", annotated_frame)
        frame = buffer.tobytes()

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")


def video_feed(request):
    return StreamingHttpResponse(
        gen_frames(),
        content_type="multipart/x-mixed-replace; boundary=frame"
    )


# ==========================
# Vista JSON con los objetos detectados
# ==========================
def objects_view(request):
    global last_labels
    return JsonResponse({"labels": last_labels})


# ==========================
# Generar audio de una palabra
# ==========================
def speak_word(request):
    word = request.GET.get("word", "")
    if word:
        tts = gTTS(text=word, lang="en")
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        audio_b64 = base64.b64encode(audio_bytes.read()).decode("utf-8")
        return JsonResponse({"audio": audio_b64})
    return JsonResponse({"error": "No word provided"}, status=400)


# ==========================
# Vista principal con el streaming
# ==========================
def live_view(request):
    return render(request, "recognition/live.html")






@csrf_exempt
def add_flashcard(request):
    """
    Recibe POST JSON con {"label": "<label_detected>"}
    Busca la caja en last_boxes, recorta el objeto de last_frame,
    traduce automáticamente y guarda un Flashcard.
    """
    global last_boxes, last_frame
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        label = data.get("label")
        if not (label and last_frame is not None and last_boxes):
            return JsonResponse({"error": "No detection available"}, status=400)

        # Ignorar si ya existe (insensible a mayúsculas)
        if Flashcard.objects.filter(palabra__iexact=label).exists():
            return JsonResponse({"message": f"La flashcard '{label}' ya existe."}, status=200)

        # Buscar la caja del objeto con ese label (buscar la primera aparición)
        for lbl, x1, y1, x2, y2 in last_boxes:
            if lbl == label:
                # Validar límites
                h, w = last_frame.shape[:2]
                x1c = max(0, min(w - 1, x1))
                x2c = max(0, min(w, x2))
                y1c = max(0, min(h - 1, y1))
                y2c = max(0, min(h, y2))

                if x2c <= x1c or y2c <= y1c:
                    return JsonResponse({"error": "Invalid bounding box"}, status=400)

                # Recortar objeto de la imagen original
                cropped = last_frame[y1c:y2c, x1c:x2c]

                # Convertir a JPG y luego base64 (sin prefijos)
                _, buffer = cv2.imencode(".jpg", cropped)
                img_b64 = base64.b64encode(buffer).decode("utf-8")

                # Traducción automática (inglés -> español)
                try:
                    translation = translator.translate(label, src="en", dest="es").text
                except Exception:
                    translation = ""  # si falla la librería de traducción, dejar vacío

                # Guardar en el modelo Flashcard
                flashcard = Flashcard(palabra=label, traduccion=translation)
                # Hay que forzar created_at para nombrar archivo (opcional). Guardamos temporalmente para que created_at exista:
                flashcard.save()  # guardamos primero para obtener id/created_at si quieres usar timestamp
                # Guardar imagen desde base64
                flashcard.save_image_from_base64(img_b64)
                flashcard.save()  # guardamos de nuevo con la imagen

                return JsonResponse({
                    "message": f"Flashcard '{label}' creada!",
                    "palabra": label,
                    "traduccion": translation,
                    "id": flashcard.id
                }, status=201)

        return JsonResponse({"error": "Object not found"}, status=404)

    return JsonResponse({"error": "Invalid request"}, status=400)







from django.shortcuts import render
from .models import Flashcard

def flashcards_list(request):
    flashcards = Flashcard.objects.all()
    return render(request, "recognition/flashcards_list.html", {"flashcards": flashcards})





from django.shortcuts import render
from .models import Flashcard

def review_flashcards(request):
    flashcards = list(Flashcard.objects.all())
    if not flashcards:
        return render(request, "recognition/review_flashcards.html", {"flashcards": []})

    # Índice de flashcard actual (del GET o 0 por defecto)
    index = int(request.GET.get("index", 0))
    index = index % len(flashcards)  # para que vuelva al inicio

    card = flashcards[index]
    next_index = (index + 1) % len(flashcards)

    return render(request, "recognition/review_flashcards.html", {
        "card": card,
        "next_index": next_index
    })