"""Client operations for listing, downloading, and sending peer files."""
import json
import os
import socket

from protocol import recv_line, send_json

CHUNK = 64 * 1024


def _connect(ip, port):
    s = socket.create_connection((ip, port), timeout=5)
    s.settimeout(30)
    return s


def list_files(ip, port):
    with _connect(ip, port) as s:
        send_json(s, {"cmd": "LIST"})
        return json.loads(recv_line(s)).get("files", [])


def _unique_path(folder, name):
    base, ext = os.path.splitext(name)
    path, i = os.path.join(folder, name), 1
    while os.path.exists(path):
        path = os.path.join(folder, f"{base} ({i}){ext}")
        i += 1
    return path


def download(ip, port, name, dest_folder):
    with _connect(ip, port) as s:
        send_json(s, {"cmd": "GET", "name": name})
        header = json.loads(recv_line(s))
        if "error" in header:
            raise RuntimeError(header["error"])
        size, got = header["size"], 0
        path = _unique_path(dest_folder, name)
        with open(path, "wb") as file:
            while got < size:
                chunk = s.recv(min(CHUNK, size - got))
                if not chunk:
                    raise ConnectionError("Connection lost")
                file.write(chunk)
                got += len(chunk)
    return path


def upload(ip, port, file_path):
    name = os.path.basename(file_path)
    size = os.path.getsize(file_path)

    with _connect(ip, port) as s:
        send_json(s, {"cmd": "SEND", "name": name, "size": size})
        response = json.loads(recv_line(s))
        if "error" in response:
            raise RuntimeError(response["error"])
        if not response.get("ready"):
            raise RuntimeError("The receiving device is not ready")

        with open(file_path, "rb") as file:
            while chunk := file.read(CHUNK):
                s.sendall(chunk)

        result = json.loads(recv_line(s))
        if "error" in result:
            raise RuntimeError(result["error"])
        return result.get("name", name)
