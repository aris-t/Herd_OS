import time
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from your_module import create_config_api  # Replace with actual import


@pytest.fixture
def mock_device():
    device = MagicMock()
    device.device_id = "mock-001"
    device.ip = "192.168.0.2"
    device.name = "TestCam"
    device.target_framerate = 30
    device.camera_endpoint = "rtsp://mock"
    device.boot_time = time.time() - 100
    device.logger.info = lambda msg: None
    device.logger.warning = lambda msg: None
    return device


@pytest.fixture
def client(mock_device):
    with tempfile.TemporaryDirectory() as tmpdir:
        build_path = Path(tmpdir)
        app = create_config_api(mock_device, build_path)
        yield TestClient(app)


def test_status(client, mock_device):
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["device_id"] == "mock-001"
    assert data["ip"] == "192.168.0.2"
    assert data["name"] == "TestCam"
    assert data["stream_fps"] == 30
    assert data["camera_endpoint"] == "rtsp://mock"
    assert isinstance(data["uptime_sec"], int)


def test_get_logs_found(client):
    with patch("builtins.open", create=True) as mock_open:
        mock_open.return_value.__enter__.return_value.readlines.return_value = [
            "2025-07-13T10:00:00 INFO Startup complete\n"
        ]
        response = client.get("/logs")
        assert response.status_code == 200
        logs = response.json()
        assert logs[0]["level"] == "INFO"


def test_get_logs_not_found(client):
    with patch("builtins.open", side_effect=FileNotFoundError):
        response = client.get("/logs")
        assert response.status_code == 404
        assert response.json()["detail"] == "Log file not found."


def test_get_files(client):
    with tempfile.TemporaryDirectory() as trial_dir:
        file_path = Path(trial_dir) / "sample.mkv"
        file_path.write_bytes(b"video content")

        with patch("your_module.Path.glob", return_value=[file_path]):
            with patch("your_module.Path.stat", return_value=file_path.stat()):
                response = client.get("/files")
                assert response.status_code == 200
                data = response.json()["files"]
                assert data[0]["name"] == "sample.mkv"


def test_restart(client):
    response = client.post("/restart")
    assert response.status_code == 200
    assert "restarting" in response.json()["message"]


def test_rename(client):
    payload = {"name": "NewName"}
    response = client.post("/rename", json=payload)
    assert response.status_code == 200
    assert "renaming" in response.json()["message"]


def test_start_trial(client):
    payload = {"name": "Trial1"}
    response = client.post("/start_trial", json=payload)
    assert response.status_code == 200
    assert "starting" in response.json()["message"]


def test_stop_trial(client):
    response = client.post("/stop_trial")
    assert response.status_code == 200
    assert "stopped" in response.json()["message"]
