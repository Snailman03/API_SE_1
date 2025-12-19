"""
Тесты для API управления командами.
Проверяет создание команд, ожидание завершения и обработку ошибок.
"""

import pytest
import logging

logger = logging.getLogger(__name__)


def test_positive_scenario(api_client, wait_for_command_completion):
    """Позитивный сценарий: создать команду → дождаться SUCCESS → проверить результат."""
    logger.info("Запуск позитивного сценария")

    # Создаем команду
    response = api_client.create_command("sensor-1", "RESTART")
    assert response["status"] == "NEW"
    command_id = response["id"]

    logger.info(f"Команда создана, ID: {command_id}")

    # Ждем завершения (polling через фикстуру)
    logger.info(f"Ожидание завершения команды {command_id}")
    final_status = wait_for_command_completion(api_client, command_id, timeout=30)

    # Проверяем результат
    assert final_status["status"] == "SUCCESS"
    assert final_status["result"] == "OK"

    logger.info(f"Тест успешно завершен: команда {command_id} выполнена успешно")


def test_empty_device_id(api_client):
    """Негативный сценарий: пустой device_id → 400 Bad Request."""
    logger.info("Тест: создание команды с пустым device_id")

    with pytest.raises(Exception) as error:
        api_client.create_command("", "RESTART")

    logger.info(f"Получена ожидаемая ошибка: {error.value.response.status_code}")
    assert error.value.response.status_code == 400

    logger.info("Тест пройден: пустой device_id корректно отвергнут")


@pytest.mark.parametrize("device_id, command", [
    ("sensor-1", "RESTART"),
    ("device-2", "SHUTDOWN"),
    ("controller-3", "STATUS"),
])
def test_create_valid_commands(api_client, device_id, command):
    """Параметризация: создание команд с разными параметрами."""
    logger.info(f"Тест: создание команды для device_id={device_id}, command={command}")

    response = api_client.create_command(device_id, command)
    assert response["status"] == "NEW"
    assert "cmd-" in response["id"]

    logger.info(f"Команда успешно создана: {response['id']}")


@pytest.mark.parametrize("invalid_device_id", ["", "   ", None])
def test_invalid_device_ids(api_client, invalid_device_id):
    """Параметризация: невалидные device_id."""
    logger.info(f"Тест: невалидный device_id='{invalid_device_id}'")

    with pytest.raises(Exception) as error:
        api_client.create_command(invalid_device_id, "RESTART")

    status_code = error.value.response.status_code
    logger.info(f"Получена ошибка {status_code} для device_id='{invalid_device_id}'")
    assert status_code == 400


def test_get_command_status(api_client):
    """Тест получения статуса команды."""
    logger.info("Тест: получение статуса команды")

    response = api_client.create_command("sensor-1", "RESTART")
    command_id = response["id"]
    logger.info(f"Создана команда для проверки: {command_id}")

    status = api_client.get_command_status(command_id)

    assert status["id"] == command_id
    assert status["status"] in ["NEW", "IN_PROGRESS", "SUCCESS", "FAILED"]

    logger.info(f"Статус команды {command_id}: {status['status']}")


@pytest.mark.parametrize("invalid_command", ["", "   ", None, 123])
def test_invalid_commands(api_client, invalid_command):
    """Параметризация: невалидные тексты команд."""
    logger.info(f"Тест: невалидная команда='{invalid_command}'")

    with pytest.raises(Exception) as error:
        api_client.create_command("sensor-1", invalid_command)

    status_code = error.value.response.status_code
    logger.info(f"Получена ошибка {status_code} для command='{invalid_command}'")
    assert status_code == 400


def test_command_id_format(api_client):
    """Проверка формата ID команды."""
    logger.info("Тест: проверка формата ID команды")

    response = api_client.create_command("sensor-1", "RESTART")
    command_id = response["id"]

    assert command_id.startswith("cmd-")
    assert len(command_id) > 5

    logger.info(f"ID команды '{command_id}' соответствует формату")


def test_command_not_found(api_client):
    """Запрос несуществующей команды -> 404."""
    logger.info("Тест: запрос несуществующей команды")

    with pytest.raises(Exception) as error:
        api_client.get_command_status("non-existing-cmd-123")

    status_code = error.value.response.status_code
    logger.info(f"Получена ошибка 404: {status_code == 404}")
    assert status_code == 404


def test_multiple_commands_for_same_device(api_client):
    """Несколько команд для одного устройства."""
    logger.info("Тест: несколько команд для одного устройства")

    cmd1 = api_client.create_command("sensor-1", "RESTART")
    cmd2 = api_client.create_command("sensor-1", "STATUS")

    assert cmd1["id"] != cmd2["id"]
    assert cmd1["status"] == "NEW"
    assert cmd2["status"] == "NEW"

    logger.info(f"Созданы 2 команды: {cmd1['id']} и {cmd2['id']}")


def test_response_time(api_client):
    """Время ответа API должно быть разумным."""
    logger.info("Тест: проверка времени ответа API")

    import time

    start = time.time()
    response = api_client.create_command("sensor-1", "RESTART")
    elapsed = time.time() - start

    logger.info(f"Время создания команды: {elapsed:.2f} секунд")
    assert elapsed < 3.0, f"Создание команды заняло {elapsed:.2f} секунд"
    assert response["status"] == "NEW"


def test_api_returns_valid_json(api_client):
    """Ответ API должен быть в формате JSON."""
    logger.info("Тест: проверка формата JSON ответа")

    response = api_client.create_command("sensor-1", "RESTART")

    assert isinstance(response, dict), "Ответ должен быть словарем (JSON object)"
    assert "id" in response
    assert "status" in response
    assert isinstance(response["id"], str)
    assert isinstance(response["status"], str)

    logger.info("JSON ответ корректен")


@pytest.mark.parametrize("device_id", [
    "very-long-device-id-" + "x" * 50,
    "device-with-dash",
    "device_with_underscore",
    "device.with.dots",
    "device123",
])
def test_various_device_id_formats(api_client, device_id):
    """Различные форматы device_id."""
    logger.info(f"Тест: device_id='{device_id[:30]}...' если длинный")

    response = api_client.create_command(device_id, "RESTART")
    assert response["status"] == "NEW"

    logger.info(f"Команда для device_id='{device_id}' создана успешно")