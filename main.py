"""Run one simulated computer:
    python main.py --name PC1 --port 5001 --folder shared/PC1
"""
import argparse
import os
import tkinter as tk

from client.broadcast import Discovery
from server.server import FileServer
from ui.app import App

p = argparse.ArgumentParser()
p.add_argument("--name", required=True, help="unique device name")
p.add_argument("--port", type=int, required=True, help="TCP file-server port")
p.add_argument("--folder", required=True, help="folder this device shares")
a = p.parse_args()

os.makedirs(a.folder, exist_ok=True)
FileServer(a.folder, a.port).start()
discovery = Discovery(a.name, a.port)
discovery.start_listener()

root = tk.Tk()
App(root, discovery, a.folder)
root.mainloop()
