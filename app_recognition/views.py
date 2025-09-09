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














from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json, cv2, base64
from .models import Flashcard

@csrf_exempt
def add_flashcard(request):
    global last_boxes, last_frame
    if request.method == "POST":
        data = json.loads(request.body)
        label = data.get("label")

        if not (label and last_frame is not None and last_boxes):
            return JsonResponse({"error": "No detection available"}, status=400)

        # Verificar si ya existe una flashcard con ese label (ignora mayúsculas/minúsculas)
        if Flashcard.objects.filter(label__iexact=label).exists():
            return JsonResponse({"message": f"La flashcard '{label}' ya existe."}, status=200)

        # Buscar la caja del objeto con ese label
        for lbl, x1, y1, x2, y2 in last_boxes:
            if lbl == label:
                # Recortar objeto de la imagen original
                cropped = last_frame[y1:y2, x1:x2]

                # Convertir a JPG y luego base64
                _, buffer = cv2.imencode(".jpg", cropped)
                img_b64 = base64.b64encode(buffer).decode("utf-8")

                # Guardar en el modelo Flashcard
                flashcard = Flashcard(label=label)
                flashcard.save_image_from_base64(img_b64)
                flashcard.save()

                return JsonResponse({"message": f"Flashcard '{label}' creada!"}, status=201)

        return JsonResponse({"error": "Object not found"}, status=404)

    return JsonResponse({"error": "Invalid request"}, status=400)














from django.shortcuts import render
from .models import Flashcard

def flashcards_list(request):
    flashcards = Flashcard.objects.all()
    return render(request, "recognition/flashcards_list.html", {"flashcards": flashcards})
