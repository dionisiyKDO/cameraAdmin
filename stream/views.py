from django.http import StreamingHttpResponse, JsonResponse
from django.shortcuts import render
import cv2
import threading

# ABOBA
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
            # Encode the frame to JPEG format
            ret, buffer = cv2.imencode(".jpg", frame)
            frame = buffer.tobytes()
            # Yield the frame in byte format, stolen from the internet :)
            yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")

