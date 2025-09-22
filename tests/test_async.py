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
from unittest.mock import patch


async def dummy_task(name: str):
    return f"{name}-ok"


@pytest.mark.trio
async def test_http_simulation(monkeypatch):
    monkeypatch.setattr("async_tasks.http_simulation", dummy_task)
    result = await http_simulation("test_http")
    assert result == "test_http-ok"


@pytest.mark.trio
async def test_tcp_simulation(monkeypatch):
    class DummySocket:
        def settimeout(self, t): ...
        def connect(self, addr):
            raise OSError

        def close(self): ...

    monkeypatch.setattr(
        "async_tasks.socket.create_connection", lambda *a, **k: DummySocket()
    )
    result = await tcp_simulation("test_tcp")
    assert "tcp-failure" in result


@pytest.mark.trio
async def test_file_simulation(tmp_path, monkeypatch):
    async def dummy_file(name, base_path=tmp_path):
        path = tmp_path / f"{name}.txt"
        path.write_text("ok")
        return f"{name}-ok"

    monkeypatch.setattr("async_tasks.file_simulation", dummy_file)
    result = await file_simulation("test_file", base_path=tmp_path)
    assert result == "test_file-ok"
    assert (tmp_path / "test_file.txt").exists()


@pytest.mark.trio
async def test_subprocess_simulation(monkeypatch):
    class DummyProc:
        async def communicate(self):
            return (b"ok", b"")

    async def dummy_create_subprocess_exec(*args, **kwargs):
        return DummyProc()

    monkeypatch.setattr(
        "async_tasks.create_subprocess_exec", dummy_create_subprocess_exec
    )

    result = await subprocess_simulation("ok")
    assert result == "ok"


@pytest.mark.trio
async def test_random_task_runs(monkeypatch):
    monkeypatch.setattr("async_tasks.random.choice", lambda l: dummy_task)
    result = await random_task("rand")
    assert result == "rand-ok"


@pytest.mark.trio
async def test_handle_task_runs(monkeypatch):
    monkeypatch.setattr("async_tasks.random_task", dummy_task)
    await handle_task("task1", 0)


@pytest.mark.trio
async def test_nested_tasks_runs(monkeypatch):
    monkeypatch.setattr("async_tasks.random_task", dummy_task)
    await nested_tasks(2)


@pytest.mark.trio
async def test_main_runs(monkeypatch):
    monkeypatch.setattr("async_tasks.random_task", dummy_task)
    await main()


@pytest.mark.trio
async def test_handle_task_cancel():
    async def never_finishing_task(name):
        await trio.sleep_forever()

    with patch("async_tasks.random_task", never_finishing_task):
        async with trio.open_nursery() as nursery:
            nursery.start_soon(handle_task, "cancel-test", 0)
            await trio.sleep(0.1)
            nursery.cancel_scope.cancel()
