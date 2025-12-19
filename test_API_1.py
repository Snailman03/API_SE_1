
"""
Тесты для API управления командами.
Проверяет создание команд, ожидание завершения и обработку ошибок.
"""

import pytest


def test_positive_scenario(api_client, wait_for_command_completion):
    """Позитивный сценарий: создать команду → дождаться SUCCESS → проверить результат."""
    # Создаем команду
    response = api_client.create_command("sensor-1", "RESTART")
    assert response["status"] == "NEW"
    command_id = response["id"]

    # Ждем завершения (polling через фикстуру)
    final_status = wait_for_command_completion(api_client, command_id, timeout=30)

    # Проверяем результат
    assert final_status["status"] == "SUCCESS"
    assert final_status["result"] == "OK"


def test_empty_device_id(api_client):
    """Негативный сценарий: пустой device_id → 400 Bad Request."""
    with pytest.raises(Exception) as error:
        api_client.create_command("", "RESTART")
    assert error.value.response.status_code == 400


@pytest.mark.parametrize("device_id, command", [
    ("sensor-1", "RESTART"),
    ("device-2", "SHUTDOWN"),
    ("controller-3", "STATUS"),
])
def test_create_valid_commands(api_client, device_id, command):
    """Параметризация: создание команд с разными параметрами."""
    response = api_client.create_command(device_id, command)
    assert response["status"] == "NEW"
    assert "cmd-" in response["id"]


@pytest.mark.parametrize("invalid_device_id", ["", "   ", None])
def test_invalid_device_ids(api_client, invalid_device_id):
    """Параметризация: невалидные device_id."""
    with pytest.raises(Exception) as error:
        api_client.create_command(invalid_device_id, "RESTART")
    assert error.value.response.status_code == 400


def test_get_command_status(api_client):
    """Тест получения статуса команды."""
    response = api_client.create_command("sensor-1", "RESTART")
    status = api_client.get_command_status(response["id"])

    assert status["id"] == response["id"]
    assert status["status"] in ["NEW", "IN_PROGRESS", "SUCCESS", "FAILED"]


@pytest.mark.parametrize("invalid_command", ["", "   ", None, 123])
def test_invalid_commands(api_client, invalid_command):
    """Параметризация: невалидные тексты команд."""
    with pytest.raises(Exception) as error:
        api_client.create_command("sensor-1", invalid_command)
    assert error.value.response.status_code == 400


def test_command_id_format(api_client):
    """Проверка формата ID команды."""
    response = api_client.create_command("sensor-1", "RESTART")
    assert response["id"].startswith("cmd-")
    assert len(response["id"]) > 5


def test_command_not_found(api_client):
    """Запрос несуществующей команды -> 404."""
    with pytest.raises(Exception) as error:
        api_client.get_command_status("non-existing-cmd-123")
    assert error.value.response.status_code == 404


def test_multiple_commands_for_same_device(api_client):
    """Несколько команд для одного устройства."""
    cmd1 = api_client.create_command("sensor-1", "RESTART")
    cmd2 = api_client.create_command("sensor-1", "STATUS")

    assert cmd1["id"] != cmd2["id"]
    assert cmd1["status"] == "NEW"
    assert cmd2["status"] == "NEW"


def test_response_time(api_client):
    """Время ответа API должно быть разумным."""
    import time

    start = time.time()
    response = api_client.create_command("sensor-1", "RESTART")
    elapsed = time.time() - start

    assert elapsed < 3.0, f"Создание команды заняло {elapsed:.2f} секунд"
    assert response["status"] == "NEW"


def test_api_is_json(api_client):
    """Ответ API должен быть в формате JSON."""
    url = f"{api_client.base_url}/api/commands"
    response = requests.post(
        url,
        json={"device_id": "sensor-1", "command": "RESTART"},
        headers={"Accept": "application/json"}
    )

    assert response.headers["Content-Type"] == "application/json"
    data = response.json()
    assert "id" in data
    assert "status" in data


@pytest.mark.parametrize("device_id", [
    "very-long-device-id-" + "x" * 50,  # Длинный ID
    "device-with-dash",
    "device_with_underscore",
    "device.with.dots",
    "device123",
])
def test_various_device_id_formats(api_client, device_id):
    """Различные форматы device_id."""
    response = api_client.create_command(device_id, "RESTART")
    assert response["status"] == "NEW"
