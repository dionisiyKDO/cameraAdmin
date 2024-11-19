from django.http import StreamingHttpResponse
from django.shortcuts import render
import cv2

# Initialize the camera
camera = cv2.VideoCapture(0)  # Change the index if using an external camera

def gen_frames():
    """Generate video frames for streaming."""
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            # Encode the frame to JPEG format
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            # Yield the frame in byte format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def index(request):
    """Render the main page."""
    return render(request, 'index.html')

def video_feed(request):
    """Stream the video feed."""
    return StreamingHttpResponse(gen_frames(), content_type='multipart/x-mixed-replace; boundary=frame')
