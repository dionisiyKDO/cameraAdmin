from django.http import StreamingHttpResponse, JsonResponse
from django.shortcuts import render
import cv2
import os
import threading
from .models import Screenshot
from django.core.files.storage import default_storage
from django.utils.timezone import now
from django.conf import settings
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

# Set to True for mock testing, False for real multiple cameras
USE_MOCK = True

# Mock settings
mock_camera_ids = [0, 1, 2, 3, 4, 5, 6]  # Simulating two cameras with the same physical camera
physical_camera = None  # Will be initialized if USE_MOCK is True



# Shared dictionary for camera instances
camera_instances = {}
lock = threading.Lock() # To ensure thread safety. Do not fully understand why this is needed, but it better be safe than sorry
# Code inside the 'with lock:' block is executed by one thread at a time. This guarantees that camera creation and deletion are thread-safe.


def index(request):
    """Render the main page."""
    connected_cameras = list_connected_cameras()
    context = {"connected_cameras": connected_cameras}
    return render(request, "index.html", context)

def screenshots_list(request):
    """Render the page to view and search screenshots."""
    query = request.GET.get("search", "")
    screenshots = Screenshot.objects.all()
    if query:
        screenshots = screenshots.filter(camera_id__icontains=query)
    context = {"screenshots": screenshots, "query": query}
    return render(request, "screenshots_list.html", context)


def list_connected_cameras():
    """List all connected cameras."""
    if USE_MOCK:
        return mock_camera_ids
    else:
        connected_cameras = []
        for index in range(10):  # TODO: Replace with logic to find connected cameras instead of hardcoded 10 cameras
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if cap.isOpened():
                connected_cameras.append(
                    index
                )  # TODO: Maybe add names of cameras instead of IDs
                cap.release()
        return connected_cameras


def create_camera_instance(camera_id):
    """Create a camera instance for the given camera ID."""
    global physical_camera # to make it treated as a global variable, not a local variable
    with lock:
        if camera_id not in camera_instances:
            if USE_MOCK:
                # All mock cameras use the same physical camera
                if physical_camera is None:
                    physical_camera = cv2.VideoCapture(0)
                camera_instances[camera_id] = physical_camera
            else:
                # Create a new instance for each real camera
                camera_instances[camera_id] = cv2.VideoCapture(camera_id)

def release_camera_instance(camera_id):
    """Release a camera instance."""
    with lock:
        if camera_id in camera_instances:
            if USE_MOCK:
                # Keep the shared physical camera open in mock mode
                del camera_instances[camera_id]
                if not camera_instances and physical_camera is not None:
                    physical_camera.release()
            else:
                # Release the specific camera in real mode
                camera_instances[camera_id].release()
                del camera_instances[camera_id]


def video_feed(request, camera_id):
    """Stream the video feed for a specific camera."""
    return StreamingHttpResponse(
        gen_frames(int(camera_id)),
        content_type="multipart/x-mixed-replace; boundary=frame", # HTTP content type used to stream video frames continuously as part of a single HTTP response
    )

def release_camera(request, camera_id):
    """API endpoint to release a camera."""
    release_camera_instance(int(camera_id))
    return JsonResponse({"status": "released", "camera_id": camera_id})


def gen_frames(camera_id):
    """Generate video frames for a specific camera."""
    create_camera_instance(camera_id)  # On init call function to create camera instance
    camera = camera_instances[camera_id]  # Get the camera instance

    while True:  # Infinite loop to keep the video feed running
        success, frame = camera.read()
        if not success:  # success is True if a frame was read successfully
            break
        else:
            # Detect cats in the frame
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # Convert to grayscale for detection
            cascade_path = os.path.join(settings.BASE_DIR, "cascades", "haarcascade_frontalcatface.xml")
            cat_cascade = cv2.CascadeClassifier(cascade_path)
            cats = cat_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(75, 75))

            if cat_cascade.empty():
                raise Exception(f"Error loading cat cascade. Check if the file exists at {cascade_path}")

            # Draw rectangles around detected cats
            for (x, y, w, h) in cats:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

            # Encode the frame to JPEG format
            ret, buffer = cv2.imencode(".jpg", frame)
            frame = buffer.tobytes()

            # Yield the frame in byte format
            yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")


@csrf_exempt
def save_screenshot(request, camera_id):
    """Save a screenshot to the server with detected cats highlighted and record metadata in the database."""
    try:
        # Generate file name and path
        formatted_time = now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"camera_{camera_id}_screenshot_{formatted_time}.jpg"
        
        # Get upload directory and file path
        upload_dir = os.path.join(settings.MEDIA_ROOT, "screenshots")
        file_path = os.path.join(upload_dir, file_name)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Capture the frame from the camera instance
        camera = camera_instances[camera_id]
        success, frame = camera.read()
        if not success:
            return JsonResponse({"error": "Failed to capture frame"}, status=500)
        
        # Detect cats in the frame
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # Convert to grayscale for detection
        cascade_path = os.path.join(settings.BASE_DIR, "cascades", "haarcascade_frontalcatface.xml")
        cat_cascade = cv2.CascadeClassifier(cascade_path)
        
        if cat_cascade.empty():
            raise Exception(f"Error loading cat cascade. Check if the file exists at {cascade_path}")
        
        # Detect cats and draw rectangles
        cats = cat_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(75, 75))
        for (x, y, w, h) in cats:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        
        # Save the frame with rectangles as an image file
        cv2.imwrite(file_path, frame)
        
        # Save metadata to the database
        Screenshot.objects.create(camera_id=camera_id, file_path=file_name)
        
        return JsonResponse({"status": "success", "file_path": file_name})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def delete_screenshot(request, screenshot_id):
    if request.method == "POST":
        try:
            # Get the screenshot from the database
            screenshot = Screenshot.objects.get(id=screenshot_id) 
            
            # Delete the file from the server
            file_path = os.path.join(settings.MEDIA_ROOT, "screenshots", screenshot.file_path) 
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Delete the screenshot entry from the database
            screenshot.delete() 
            return JsonResponse({"status": "success", "screenshot_id": screenshot_id})
        except Screenshot.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Screenshot not found"}, status=404)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)
