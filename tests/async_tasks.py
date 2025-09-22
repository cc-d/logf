import trio
import random
import socket
import subprocess


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
        sock.connect(("127.0.0.1", 9999))
    except Exception:
        return f"{name}-tcp-failure"
    finally:
        sock.close()
    return f"{name}-tcp-success"


async def file_simulation(name: str, base_path="/tmp"):
    import random, trio

    await trio.sleep(random.uniform(0.01, 0.2))
    try:
        path = f"{base_path}/{name}.txt"
        with open(path, "w") as f:
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


async def handle_task(name: str, depth: int):
    try:
        result = await random_task(name)
        print(f"{name} result: {result}")
    except Exception as e:
        print(f"{name} exception: {e}")


async def nested_tasks(n: int, depth=0):
    async with trio.open_nursery() as nursery:
        for i in range(n):
            nursery.start_soon(handle_task, f"task-{depth}-{i}", depth)


async def main():
    async with trio.open_nursery() as nursery:
        for i in range(5):
            nursery.start_soon(handle_task, f"root-{i}", 0)
