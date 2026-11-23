"""Tiny helpers shared by client and server: newline-terminated JSON headers."""
import json


def recv_line(conn):
    buf = b""
    while not buf.endswith(b"\n"):
        ch = conn.recv(1)
        if not ch:
            break
        buf += ch
    return buf.decode().strip()


def send_json(conn, obj):
    conn.sendall((json.dumps(obj) + "\n").encode())
