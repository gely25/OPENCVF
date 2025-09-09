from flask import Flask, render_template, Response, request, jsonify
import cv2
import os
from datetime import datetime

app = Flask(__name__)

# Carpeta donde se guardarán las flashcards
FLASHCARDS_FOLDER = "media/flashcards"
os.makedirs(FLASHCARDS_FOLDER, exist_ok=True)

camera = cv2.VideoCapture(0)

@app.route('/')
def index():
    return render_template('index.html')

def gen_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/save_flashcard', methods=['POST'])
def save_flashcard():
    data = request.json
    x, y, w, h = data["x"], data["y"], data["w"], data["h"]

    success, frame = camera.read()
    if not success:
        return jsonify({"status": "error", "message": "No se pudo capturar la cámara"})

    # Recortar la parte del objeto
    crop = frame[y:y+h, x:x+w]

    # Guardar la imagen
    filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"
    filepath = os.path.join(FLASHCARDS_FOLDER, filename)
    cv2.imwrite(filepath, crop)

    return jsonify({"status": "success", "message": "Flashcard guardada", "path": filepath})

if __name__ == '__main__':
    app.run(debug=True)
