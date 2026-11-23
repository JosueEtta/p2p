"""Start P2P Share with a device configuration screen."""
import argparse
import os
import socket
import tkinter as tk
from tkinter import messagebox

from client.broadcast import Discovery
from server.server import FileServer
from ui.app import App
from ui.startup import StartupScreen


p = argparse.ArgumentParser()
p.add_argument("--name", default=socket.gethostname(), help="initial device name")
p.add_argument("--port", type=int, required=True, help="TCP file-server port")
p.add_argument("--folder", default="shared", help="initial shared folder")
a = p.parse_args()

os.makedirs(a.folder, exist_ok=True)

root = tk.Tk()


def start_sharing(device_name, folder):
    try:
        server = FileServer(folder, a.port)
        server.start()
        discovery = Discovery(device_name, a.port)
        discovery.start_listener()
    except OSError as exc:
        messagebox.showerror("Could not start sharing", str(exc), parent=root)
        return

    for widget in root.winfo_children():
        widget.destroy()

    App(root, discovery, folder)


StartupScreen(root, start_sharing, initial_name=a.name, initial_folder=os.path.abspath(a.folder))
root.mainloop()
