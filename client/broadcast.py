"""UDP peer discovery. Found peers are stored in the module-level `peers`
dict ({name: (ip, tcp_port)}) so other modules can read them via get_peers().

Each running instance binds the first free UDP port in 50000-50009, so several
instances can run on one Windows machine. Scans are sent FROM that same bound
port, so replies come back to a port the firewall already allows."""
import json
import socket
import sys
import threading
import time


DISCOVERY_PORTS = range(50000, 50010)
peers = {}
_seen = {}  # name -> time we last heard from it
_lock = threading.Lock()


def get_peers():
    with _lock:
        return dict(peers)


def _disable_udp_connreset(sock):
    """Stop Windows raising WinError 10054 on UDP sockets (best effort).

    Python's socket.ioctl() only accepts a few commands, so we call the
    Windows API (WSAIoctl) directly through ctypes."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        from ctypes import wintypes

        SIO_UDP_CONNRESET = 0x9800000C
        ws2 = ctypes.WinDLL("ws2_32")
        ws2.WSAIoctl.argtypes = [
            ctypes.c_size_t, wintypes.DWORD,
            ctypes.c_void_p, wintypes.DWORD,
            ctypes.c_void_p, wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
            ctypes.c_void_p, ctypes.c_void_p,
        ]
        ws2.WSAIoctl.restype = ctypes.c_int

        flag = wintypes.DWORD(0)  # 0 = disable the connection-reset behaviour
        returned = wintypes.DWORD(0)
        ws2.WSAIoctl(sock.fileno(), SIO_UDP_CONNRESET,
                     ctypes.byref(flag), ctypes.sizeof(flag),
                     None, 0, ctypes.byref(returned), None, None)
    except Exception:
        pass  # not critical: the listener loop already ignores OSError


class Discovery:
    def __init__(self, name, tcp_port):
        self.name = name
        self.tcp_port = tcp_port
        self.sock = None

    def _register(self, data, addr):
        try:
            msg = json.loads(data.decode())
            name, port = msg["name"], msg["port"]
        except (ValueError, KeyError):
            return None
        if name == self.name:  # ignore ourselves
            return None
        with _lock:
            peers[name] = (addr[0], port)
            _seen[name] = time.time()
        return msg

    def _payload(self, kind):
        return json.dumps({"type": kind, "name": self.name, "port": self.tcp_port}).encode()

    def start_listener(self):
        """Answer other peers' DISCOVER requests (and receive replies to ours)."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for port in DISCOVERY_PORTS:
            try:
                s.bind(("", port))
                break
            except OSError:
                continue
        else:
            raise RuntimeError("No free discovery port (50000-50009)")
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        _disable_udp_connreset(s)  # stop Windows raising "connection reset" on UDP
        self.sock = s

        def loop():
            while True:
                try:
                    data, addr = s.recvfrom(4096)
                except OSError:
                    continue
                msg = self._register(data, addr)
                if msg and msg.get("type") == "DISCOVER":
                    try:
                        s.sendto(self._payload("ANNOUNCE"), addr)
                    except OSError:
                        pass

        threading.Thread(target=loop, daemon=True).start()

    def refresh(self, timeout=2.5, tries=3):
        """Send DISCOVER `tries` times from the listener's own port. Replies are
        saved by the listener thread. Peers not heard during the scan are removed."""
        start = time.time()
        msg = self._payload("DISCOVER")
        for _ in range(tries):
            for port in DISCOVERY_PORTS:
                for target in ("255.255.255.255", "127.0.0.1"):
                    try:
                        self.sock.sendto(msg, (target, port))
                    except OSError:
                        pass
            time.sleep(timeout / tries)
        with _lock:
            for name in [n for n in peers if _seen.get(n, 0) < start]:
                del peers[name]
        return get_peers()