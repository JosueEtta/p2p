"""Run one device:
    python main.py --port 5001 --folder shared

The device hostname is used automatically unless --name is provided.
"""
import argparse
import os
import socket
import tkinter as tk

from client.broadcast import Discovery
from server.server import FileServer
from ui.app import App

p = argparse.ArgumentParser()
p.add_argument("--name", default=socket.gethostname(), help="device name (defaults to the system hostname)")
p.add_argument("--port", type=int, required=True, help="TCP file-server port")
p.add_argument("--folder", required=True, help="folder this device shares")
a = p.parse_args()

device_name = a.name.strip() or socket.gethostname()
os.makedirs(a.folder, exist_ok=True)
FileServer(a.folder, a.port).start()
discovery = Discovery(device_name, a.port)
discovery.start_listener()

root = tk.Tk()
App(root, discovery, a.folder)
root.mainloop()
