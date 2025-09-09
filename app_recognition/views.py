from django.http import StreamingHttpResponse
from django.shortcuts import render
import cv2
from ultralytics import YOLO

# Cargar modelo YOLOv8 (nano por ligereza)
model = YOLO("yolov8n.pt")

# Variable global para guardar los últimos objetos detectados
last_labels = []

def gen_frames():
    global last_labels
    camera = cv2.VideoCapture(0)
    while True:
        success, frame = camera.read()
        if not success:
            break

        # Detectar objetos
        results = model(frame)

        # Extraer nombres de objetos
        labels = []
        for r in results:
            for c in r.boxes.cls:
                labels.append(model.names[int(c)])
        last_labels = list(set(labels))  # guardamos etiquetas únicas

        # Dibujar detecciones
        annotated_frame = results[0].plot()

        # Codificar para enviar al navegador
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def video_feed(request):
    return StreamingHttpResponse(
        gen_frames(),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )





from django.http import JsonResponse

def objects_view(request):
    global last_labels
    return JsonResponse({"labels": last_labels})



from django.http import JsonResponse
from gtts import gTTS
import base64
import io

def speak_word(request):
    word = request.GET.get("word", "")
    if word:
        # Generamos audio en memoria
        tts = gTTS(text=word, lang="en")
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)

        # Convertir a base64
        audio_b64 = base64.b64encode(audio_bytes.read()).decode("utf-8")
        return JsonResponse({"audio": audio_b64})

    return JsonResponse({"error": "No word provided"}, status=400)



from django.shortcuts import render
from ultralytics import YOLO
import cv2

# Cargar modelo YOLOv8 (nano = rápido y ligero)
model = YOLO("yolov8n.pt")

def detect_objects(request):
    # Abrimos la cámara
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return render(request, "detections.html", {"objects": []})

    # Detección
    results = model(frame)
    detected_objects = []

    for result in results:
        for box in result.boxes:
            cls_id = int(box.cls[0])  # ID de clase
            label = model.names[cls_id]  # Nombre de la clase
            if label not in detected_objects:  # Evitar duplicados
                detected_objects.append(label)

    # Enviamos al template
    return render(request, "detections.html", {"objects": detected_objects})

from django.shortcuts import render

def live_view(request):
    return render(request, "recognition/live.html")








from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import base64
from .models import Flashcard  # Asumiendo que tienes un modelo Flashcard

@csrf_exempt
def add_flashcard(request):
    if request.method == "POST":
        data = json.loads(request.body)
        label = data.get("label")
        img_data = data.get("img")
        if label and img_data:
            if img_data.startswith("data:image"):
                img_data = img_data.split(",")[1]

            flashcard = Flashcard(label=label)
            flashcard.save_image_from_base64(img_data)
            flashcard.save()
            return JsonResponse({"message": f"Flashcard '{label}' creada!"})
    return JsonResponse({"error": "Datos incompletos"}, status=400)
