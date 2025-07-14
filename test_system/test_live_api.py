import requests

TARGET_URL = "http://localhost:8000"

def test_status_route():
    r = requests.get(f"{TARGET_URL}/status")
    assert r.status_code == 200
    data = r.json()
    assert "device_id" in data
    assert "ip" in data
    assert "name" in data
    assert "stream_fps" in data
    assert "uptime_sec" in data
    assert "build_path" in data


def test_logs_route():
    r = requests.get(f"{TARGET_URL}/logs")
    if r.status_code == 200:
        logs = r.json()
        assert isinstance(logs, list)
        for log in logs:
            assert "time" in log
            assert "level" in log
            assert "msg" in log
    elif r.status_code == 404:
        assert r.json()["detail"] == "Log file not found."
    else:
        assert False, f"Unexpected status code: {r.status_code}"


def test_files_route():
    r = requests.get(f"{TARGET_URL}/files")
    assert r.status_code == 200
    data = r.json()
    assert "files" in data
    assert isinstance(data["files"], list)
    for f in data["files"]:
        assert "name" in f and "size" in f


def test_restart_route():
    r = requests.post(f"{TARGET_URL}/restart")
    assert r.status_code == 200
    assert "restarting" in r.json()["message"].lower()


def test_rename_route():
    payload = {"name": "NewDevice"}
    r = requests.post(f"{TARGET_URL}/rename", json=payload)
    assert r.status_code == 200
    assert "renaming" in r.json()["message"].lower()


def test_start_trial_route():
    payload = {"name": "Trial001"}
    r = requests.post(f"{TARGET_URL}/start_trial", json=payload)
    assert r.status_code == 200
    assert "starting" in r.json()["message"].lower()


def test_stop_trial_route():
    r = requests.post(f"{TARGET_URL}/stop_trial")
    assert r.status_code == 200
    assert "stopped" in r.json()["message"].lower()
