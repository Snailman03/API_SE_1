# conftest.py
"""
Фикстуры для тестов API команд.
Содержит API клиент и функцию для ожидания завершения команд.

"""

import pytest
import requests
import time
import logging
from datetime import datetime

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_tests.log', encoding='utf-8'),
        logging.StreamHandler()  # Вывод в консоль
    ]
)

logger = logging.getLogger(__name__)


@pytest.fixture
def base_url():
    """Базовый URL API."""
    return "https://api.example.com"


@pytest.fixture
def api_client(base_url):
    """Создает и возвращает API клиент с логированием."""

    class CommandAPIClient:
        """Клиент для работы с API команд с логированием."""

        def __init__(self, url):
            self.base_url = url
            self.logger = logging.getLogger(f"{__name__}.CommandAPIClient")

        def create_command(self, device_id, command):
            """Создает новую команду. POST /api/commands"""
            url = f"{self.base_url}/api/commands"
            payload = {"device_id": device_id, "command": command}

            self.logger.info(f"Создание команды: device_id={device_id}, command={command}")
            self.logger.debug(f"URL: {url}, Payload: {payload}")

            try:
                response = requests.post(url, json=payload)
                response.raise_for_status()

                response_data = response.json()
                self.logger.info(f"Команда создана: id={response_data.get('id')}, status={response_data.get('status')}")
                self.logger.debug(f"Полный ответ: {response_data}")

                return response_data

            except requests.exceptions.RequestException as e:
                self.logger.error(f"Ошибка при создании команды: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    self.logger.error(f"Статус код: {e.response.status_code}")
                    self.logger.error(f"Ответ сервера: {e.response.text}")
                raise

        def get_command_status(self, command_id):
            """Получает статус команды. GET /api/commands/{id}"""
            url = f"{self.base_url}/api/commands/{command_id}"

            self.logger.info(f"Запрос статуса команды: {command_id}")
            self.logger.debug(f"URL: {url}")

            try:
                response = requests.get(url)
                response.raise_for_status()

                response_data = response.json()
                self.logger.info(f"Статус команды {command_id}: {response_data.get('status')}")

                return response_data

            except requests.exceptions.RequestException as e:
                self.logger.error(f"Ошибка при запросе статуса команды {command_id}: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    self.logger.error(f"Статус код: {e.response.status_code}")
                raise

    return CommandAPIClient(base_url)


@pytest.fixture
def wait_for_command_completion():
    """
    Фикстура, которая возвращает функцию ожидания завершения команды.
    """

    def _wait(api_client, command_id, timeout=15):
        """Ожидает завершения команды (SUCCESS или FAILED)."""
        logger = logging.getLogger(f"{__name__}.wait_for_command")
        logger.info(f"Начало ожидания команды {command_id}, таймаут: {timeout} секунд")

        end_time = time.time() + timeout
        attempt = 1

        while time.time() < end_time:
            try:
                logger.debug(f"Попытка #{attempt} для команды {command_id}")
                status = api_client.get_command_status(command_id)

                if status["status"] in ["SUCCESS", "FAILED"]:
                    logger.info(f"Команда {command_id} завершена со статусом: {status['status']}")
                    return status

            except Exception as e:
                logger.warning(f"Временная ошибка при проверке команды {command_id}: {e}")

            attempt += 1
            time.sleep(0.5)

        logger.error(f"Таймаут ожидания команды {command_id}")
        raise TimeoutError(f"Команда {command_id} не завершилась за {timeout} секунд")

    return _wait


@pytest.fixture(autouse=True)
def log_test_start_and_end():
    """Автоматически логирует начало и конец каждого теста."""
    logger = logging.getLogger(__name__)

    logger.info("=" * 50)
    logger.info("Начало выполнения тестов")
    yield
    logger.info("Завершение выполнения тестов")
    logger.info("=" * 50)