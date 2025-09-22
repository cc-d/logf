import pathlib  # --- Ensure project root is on sys.path ---
import sys

ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


import sys
import pathlib
import pytest


# --- Async backend fixture (pytest-anyio) ---
@pytest.fixture
def anyio_backend():
    return "trio"


# --- Example fixtures for mocks ---
import socket
import subprocess
from unittest import mock


@pytest.fixture
def fake_tcp_connect(monkeypatch):
    def _fake(*args, **kwargs):
        raise OSError("Simulated connection error")

    monkeypatch.setattr(socket.socket, "connect", _fake)
    return _fake


@pytest.fixture
def fake_subprocess_run(monkeypatch):
    def _fake(*args, **kwargs):
        return mock.Mock(returncode=0, stdout="fake output", stderr="")

    monkeypatch.setattr(subprocess, "run", _fake)
    return _fake


@pytest.fixture
def sample_file(tmp_path):
    f = tmp_path / "sample.txt"
    f.write_text("hello world")
    return f
