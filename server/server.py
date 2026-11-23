"""File server: answers LIST and GET requests over TCP."""
import json
import os
import socket
import threading

from protocol import recv_line, send_json

CHUNK = 64 * 1024


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
            if os.path.isfile(path):
                files.append({"name": name, "size": os.path.getsize(path)})
        return files

    def _handle(self, conn):
        try:
            req = json.loads(recv_line(conn))
            if req.get("cmd") == "LIST":
                send_json(conn, {"files": self.list_files()})
            elif req.get("cmd") == "GET":
                name = os.path.basename(req.get("name", ""))  # no path traversal
                path = os.path.join(self.folder, name)
                if not os.path.isfile(path):
                    send_json(conn, {"error": "File not found"})
                    return
                send_json(conn, {"size": os.path.getsize(path)})
                with open(path, "rb") as f:
                    while chunk := f.read(CHUNK):
                        conn.sendall(chunk)
            else:
                send_json(conn, {"error": "Unknown command"})
        except Exception:
            pass
        finally:
            conn.close()
