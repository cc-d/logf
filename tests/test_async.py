# complex_async_test.py
from .conftest import sys
import trio
import anyio
import random
import socket
import asyncio
import subprocess
from contextlib import asynccontextmanager


async def http_simulation(name: str):
    await trio.sleep(random.uniform(0.01, 0.5))
    if random.random() < 0.1:
        raise RuntimeError(f"{name} failed during HTTP request")
    return f"{name}-http-response"


async def tcp_simulation(name: str):
    await trio.sleep(random.uniform(0.01, 0.5))
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.2)
        sock.connect(("127.0.0.1", 9999))  # may fail if no server
    except Exception:
        return f"{name}-tcp-failure"
    finally:
        sock.close()
    return f"{name}-tcp-success"


async def file_simulation(name: str):
    await trio.sleep(random.uniform(0.01, 0.2))
    try:
        with open(f"/tmp/{name}.txt", "w") as f:
            f.write("x" * random.randint(1, 100))
    except Exception:
        return f"{name}-file-failure"
    return f"{name}-file-success"


async def subprocess_simulation(name: str):
    await trio.sleep(random.uniform(0.01, 0.2))
    try:
        result = subprocess.run(
            ["echo", name], capture_output=True, text=True, timeout=0.1
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return f"{name}-subproc-timeout"


async def random_task(name: str):
    choice = random.choice(
        [
            http_simulation,
            tcp_simulation,
            file_simulation,
            subprocess_simulation,
        ]
    )
    return await choice(name)


async def nested_tasks(n: int, depth=0):
    async with trio.open_nursery() as nursery:
        for i in range(n):
            task_name = f"task-{depth}-{i}"
            nursery.start_soon(handle_task, task_name, depth)


async def handle_task(name: str, depth: int):
    try:
        # simulate layered calls
        result = await random_task(name)
        print(f"{name} result: {result}")
        # maybe spawn a nested task group
        if depth < 2 and random.random() < 0.5:
            await nested_tasks(random.randint(1, 3), depth=depth + 1)
        # simulate cancellation edge
        if random.random() < 0.05:
            raise trio.Cancelled
    except trio.Cancelled:
        print(f"{name} was cancelled")
    except Exception as e:
        print(f"{name} exception: {e}")


async def main():
    async with trio.open_nursery() as nursery:
        for i in range(5):
            nursery.start_soon(handle_task, f"root-{i}", 0)


if __name__ == "__main__":
    trio.run(main)
trio
