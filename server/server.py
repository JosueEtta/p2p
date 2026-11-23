"""TCP file server for listing, downloading, and receiving files."""
import json
import os
import socket
import tempfile
import threading

from protocol import recv_line, send_json

CHUNK = 64 * 1024


def _unique_path(folder, name):
    base, ext = os.path.splitext(name)
    path, index = os.path.join(folder, name), 1
    while os.path.exists(path):
        path = os.path.join(folder, f"{base} ({index}){ext}")
        index += 1
    return path


class FileServer(threading.Thread):
    def __init__(self, folder, port):
        super().__init__(daemon=True)
        self.folder = folder
        self.port = port

    def run(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("0.0.0.0", self.port))
        srv.listen(10)
        while True:
            conn, _ = srv.accept()
            threading.Thread(target=self._handle, args=(conn,), daemon=True).start()

    def list_files(self):
        files = []
        for name in sorted(os.listdir(self.folder)):
            path = os.path.join(self.folder, name)
            if os.path.isfile(path) and not name.endswith(".part"):
                files.append({"name": name, "size": os.path.getsize(path)})
        return files

    def _handle(self, conn):
        try:
            req = json.loads(recv_line(conn))
            command = req.get("cmd")

            if command == "LIST":
                send_json(conn, {"files": self.list_files()})

            elif command == "GET":
                name = os.path.basename(req.get("name", "").replace("\\", "/"))
                path = os.path.join(self.folder, name)
                if not name or not os.path.isfile(path):
                    send_json(conn, {"error": "File not found"})
                    return
                send_json(conn, {"size": os.path.getsize(path)})
                with open(path, "rb") as file:
                    while chunk := file.read(CHUNK):
                        conn.sendall(chunk)

            elif command == "SEND":
                raw_name = req.get("name", "")
                name = os.path.basename(raw_name.replace("\\", "/"))
                size = req.get("size")
                if not name or name in (".", "..") or not isinstance(size, int) or isinstance(size, bool) or size < 0:
                    send_json(conn, {"error": "Invalid file details"})
                    return

                send_json(conn, {"ready": True})
                temp_path = None
                try:
                    with tempfile.NamedTemporaryFile(
                        mode="wb", dir=self.folder, prefix=".p2p-", suffix=".part", delete=False
                    ) as file:
                        temp_path = file.name
                        received = 0
                        while received < size:
                            chunk = conn.recv(min(CHUNK, size - received))
                            if not chunk:
                                raise ConnectionError("Connection lost during upload")
                            file.write(chunk)
                            received += len(chunk)

                    destination = _unique_path(self.folder, name)
                    os.replace(temp_path, destination)
                    temp_path = None
                    send_json(conn, {"success": True, "name": os.path.basename(destination)})
                finally:
                    if temp_path and os.path.exists(temp_path):
                        os.remove(temp_path)

            else:
                send_json(conn, {"error": "Unknown command"})

        except Exception as exc:
            try:
                send_json(conn, {"error": str(exc) or "Transfer failed"})
            except OSError:
                pass
        finally:
            conn.close()
