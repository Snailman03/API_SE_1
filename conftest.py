# conftest.py
"""
Фикстуры для тестов API команд.
Содержит API клиент и функцию для ожидания завершения команд.
"""

import pytest
import requests
import time


@pytest.fixture
def base_url():
    """Базовый URL API."""
    return "https://api.example.com"


@pytest.fixture
def api_client(base_url):
    """Создает и возвращает API клиент."""

    class CommandAPIClient:
        """Клиент для работы с API команд."""

        def __init__(self, url):
            self.base_url = url

        def create_command(self, device_id, command):
            """Создает новую команду. POST /api/commands"""
            url = f"{self.base_url}/api/commands"
            response = requests.post(url, json={"device_id": device_id, "command": command})
            response.raise_for_status()
            return response.json()

        def get_command_status(self, command_id):
            """Получает статус команды. GET /api/commands/{id}"""
            url = f"{self.base_url}/api/commands/{command_id}"
            response = requests.get(url)
            response.raise_for_status()
            return response.json()

    return CommandAPIClient(base_url)


@pytest.fixture
def wait_for_command_completion():
    """
    Фикстура, которая возвращает функцию ожидания завершения команды.
    Sleep находится внутри этой функции, а не в тестах.
    """

    def _wait(api_client, command_id, timeout=15):
        """Ожидает завершения команды (SUCCESS или FAILED)."""
        end_time = time.time() + timeout

        while time.time() < end_time:
            try:
                status = api_client.get_command_status(command_id)
                if status["status"] in ["SUCCESS", "FAILED"]:
                    return status
            except:
                pass  # Игнорируем временные ошибки

            time.sleep(0.5)  # Polling каждые 0.5 секунды

        raise TimeoutError(f"Команда {command_id} не завершилась за {timeout} секунд")

    return _wait
