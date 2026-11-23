"""Client: asks a peer for its file list or downloads a file from it."""
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
        with open(path, "wb") as f:
            while got < size:
                chunk = s.recv(min(CHUNK, size - got))
                if not chunk:
                    raise ConnectionError("Connection lost")
                f.write(chunk)
                got += len(chunk)
    return path
