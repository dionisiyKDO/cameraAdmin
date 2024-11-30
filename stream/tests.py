from django.test import TestCase
from stream.views import create_camera_instance, release_camera_instance, list_connected_cameras, camera_instances
import cv2

class StreamUnitTests(TestCase):
    def setUp(self):
        self.mock_camera_id = 0

    def tearDown(self):
        if self.mock_camera_id in camera_instances:
            release_camera_instance(self.mock_camera_id)

    def test_list_connected_cameras_mock(self):
        """Тест для функции list_connected_cameras в режиме MOCK."""
        from stream.views import USE_MOCK, mock_camera_ids
        USE_MOCK = True  
        cameras = list_connected_cameras()
        self.assertEqual(cameras, mock_camera_ids)

    def test_create_camera_instance(self):
        """Тест создания камеры."""
        create_camera_instance(self.mock_camera_id)
        self.assertIn(self.mock_camera_id, camera_instances)
        self.assertIsInstance(camera_instances[self.mock_camera_id], cv2.VideoCapture)

    def test_release_camera_instance(self):
        """Тест освобождения камеры."""
        create_camera_instance(self.mock_camera_id)
        release_camera_instance(self.mock_camera_id)
        self.assertNotIn(self.mock_camera_id, camera_instances)

    def test_create_duplicate_camera_instance(self):
        """Тест создания камеры с тем же ID дважды."""
        create_camera_instance(self.mock_camera_id)
        first_instance = camera_instances[self.mock_camera_id]
        create_camera_instance(self.mock_camera_id)  
        second_instance = camera_instances[self.mock_camera_id]
        self.assertIs(first_instance, second_instance)  

# Create your tests here.
