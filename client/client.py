"""Client operations for listing and downloading peer files."""
import json
import os
import socket
import tempfile

from protocol import recv_line, send_json

CHUNK = 64 * 1024


def _connect(ip, port):
    s = socket.create_connection((ip, port), timeout=5)
    s.settimeout(30)
    return s


def list_files(ip, port):
    with _connect(ip, port) as s:
        send_json(s, {"cmd": "LIST"})
        response = json.loads(recv_line(s))
        if "error" in response:
            raise RuntimeError(response["error"])
        return response.get("files", [])


def _unique_path(folder, name):
    base, ext = os.path.splitext(name)
    path, i = os.path.join(folder, name), 1
    while os.path.exists(path):
        path = os.path.join(folder, f"{base} ({i}){ext}")
        i += 1
    return path


def download(ip, port, name, dest_folder, progress_callback=None):
    os.makedirs(dest_folder, exist_ok=True)
    with _connect(ip, port) as s:
        send_json(s, {"cmd": "GET", "name": name})
        header = json.loads(recv_line(s))
        if "error" in header:
            raise RuntimeError(header["error"])

        size = header.get("size")
        if not isinstance(size, int) or size < 0:
            raise RuntimeError("The peer returned an invalid file size")

        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb", dir=dest_folder, prefix=".p2p-", suffix=".part", delete=False
            ) as file:
                temp_path = file.name
                received = 0
                if progress_callback:
                    progress_callback(0, size)
                while received < size:
                    chunk = s.recv(min(CHUNK, size - received))
                    if not chunk:
                        raise ConnectionError("Connection lost during download")
                    file.write(chunk)
                    received += len(chunk)
                    if progress_callback:
                        progress_callback(received, size)

            destination = _unique_path(dest_folder, os.path.basename(name))
            os.replace(temp_path, destination)
            temp_path = None
            return destination
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
