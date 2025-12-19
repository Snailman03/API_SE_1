
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

