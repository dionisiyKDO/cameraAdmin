from django.test import TestCase
from stream.views import create_camera_instance, release_camera_instance, list_connected_cameras, camera_instances
import cv2

class StreamUnitTests(TestCase):
    def setUp(self):
        # Инициализация перед тестами
        self.mock_camera_id = 0

    def tearDown(self):
        # Освобождение ресурсов после тестов
        if self.mock_camera_id in camera_instances:
            release_camera_instance(self.mock_camera_id)

    def test_list_connected_cameras_mock(self):
        """Тест для функции list_connected_cameras в режиме MOCK."""
        from stream.views import USE_MOCK, mock_camera_ids
        USE_MOCK = True  # Принудительно включаем MOCK-режим
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
        create_camera_instance(self.mock_camera_id)  # Повторное создание
        second_instance = camera_instances[self.mock_camera_id]
        self.assertIs(first_instance, second_instance)  # Должен быть тот же объект
        
    def test_mock_camera_shared_instance(self):
        """Тест использования общего физического объекта камеры в режиме MOCK."""
        from stream.views import USE_MOCK
        USE_MOCK = True  # Принудительно включаем MOCK-режим
        create_camera_instance(0)
        create_camera_instance(1)
        self.assertIs(camera_instances[0], camera_instances[1])  # Одна физическая камера
        self.assertIsNotNone(camera_instances[0])  # Камера должна быть инициализирована
        release_camera_instance(0)
        release_camera_instance(1)

    def test_list_connected_cameras_real(self):
        """Тест для функции list_connected_cameras в реальном режиме."""
        from stream.views import USE_MOCK
        USE_MOCK = False  # Переключаемся на реальный режим

        cameras = list_connected_cameras()

        # Если камер нет, пропускаем тест
        if not cameras:
            self.skipTest("No physical cameras detected on the system.")

        # Проверяем, что список корректен
        self.assertIsInstance(cameras, list)
        self.assertTrue(all(isinstance(cam, int) for cam in cameras))  # Все элементы списка — int
        self.assertGreater(len(cameras), 0)  # Список не должен быть пустым

    def test_thread_safety_with_multiple_cameras(self):
        """Тест потокобезопасности при создании и освобождении камер."""
        from stream.views import lock  # Убедимся, что lock используется корректно

        def create_and_release(self, camera_id):
            """Функция для создания и освобождения камеры в потоке."""
            create_camera_instance(camera_id)
            release_camera_instance(camera_id)
            threads = []
            for camera_id in range(3):  # Создаем 3 потока для работы с 3 камерами
                thread = threads.Thread(target=create_and_release, args=(camera_id,))
                threads.append(thread)
                thread.start()
            for thread in threads:
                thread.join()
            self.assertEqual(len(camera_instances), 0)  # После завершения словарь должен быть пустым
       
    def test_release_nonexistent_camera(self):
        """Тест освобождения камеры, которая не существует."""
        nonexistent_camera_id = 999  # ID камеры, которая не была создана
        release_camera_instance(nonexistent_camera_id)  # Попытка освободить
        self.assertNotIn(nonexistent_camera_id, camera_instances)  # Камеры там быть не должно
        
# Create your tests here.
