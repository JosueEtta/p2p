"""TCP file server for listing and downloading shared files."""
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
        self._ready = threading.Event()
        self._stop_event = threading.Event()
        self._socket = None
        self.startup_error = None

    def wait_until_ready(self, timeout=5):
        if not self._ready.wait(timeout):
            raise TimeoutError("The file server did not start in time")
        if self.startup_error:
            raise self.startup_error

    def stop(self):
        self._stop_event.set()
        if self._socket:
            try:
                self._socket.close()
            except OSError:
                pass

    def run(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket = srv
        try:
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind(("0.0.0.0", self.port))
            srv.listen(10)
            srv.settimeout(1)
            self._ready.set()

            while not self._stop_event.is_set():
                try:
                    conn, _ = srv.accept()
                except socket.timeout:
                    continue
                except OSError:
                    if self._stop_event.is_set():
                        break
                    raise
                threading.Thread(target=self._handle, args=(conn,), daemon=True).start()
        except OSError as exc:
            self.startup_error = exc
            self._ready.set()
        finally:
            srv.close()

    def list_files(self):
        files = []
        for name in sorted(os.listdir(self.folder)):
            path = os.path.join(self.folder, name)
            if os.path.isfile(path) and not name.endswith(".part") and not name.startswith(".p2p-"):
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

            else:
                send_json(conn, {"error": "Unknown command"})

        except Exception as exc:
            try:
                send_json(conn, {"error": str(exc) or "Transfer failed"})
            except OSError:
                pass
        finally:
            conn.close()
