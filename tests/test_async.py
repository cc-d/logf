import pytest
import trio
from async_tasks import (
    http_simulation,
    tcp_simulation,
    file_simulation,
    subprocess_simulation,
    random_task,
    handle_task,
    nested_tasks,
    main,
)


@pytest.mark.trio
async def test_http_simulation():
    result = await http_simulation("test_http")
    assert "http-response" in result


@pytest.mark.trio
async def test_tcp_simulation(monkeypatch):
    class DummySocket:
        def settimeout(self, t): ...
        def connect(self, addr):
            raise OSError

        def close(self): ...

    monkeypatch.setattr(
        "async_tasks.socket.socket", lambda *a, **k: DummySocket()
    )
    result = await tcp_simulation("test_tcp")
    assert "tcp-failure" in result


@pytest.mark.trio
async def test_file_simulation(tmp_path):
    result = await file_simulation("test_file", base_path=tmp_path)
    assert "file-success" in result
    # optionally check file exists
    assert (tmp_path / "test_file.txt").exists()


@pytest.mark.trio
async def test_subprocess_simulation(monkeypatch):
    monkeypatch.setattr(
        "async_tasks.subprocess.run",
        lambda *a, **k: type("R", (), {"stdout": "ok"})(),
    )
    result = await subprocess_simulation("test_subproc")
    assert result == "ok"


@pytest.mark.trio
async def test_random_task_runs():
    result = await random_task("rand")
    assert isinstance(result, str)


@pytest.mark.trio
async def test_handle_task_runs_without_error():
    await handle_task("task1", 0)


@pytest.mark.trio
async def test_nested_tasks_runs():
    await nested_tasks(2)


@pytest.mark.trio
async def test_main_runs():
    await main()
