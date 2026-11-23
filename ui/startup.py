"""Startup screen for configuring this device before sharing files."""
import os
import socket
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class StartupScreen:
    def __init__(self, root, on_start, initial_name=None, initial_folder=""):
        self.root = root
        self.on_start = on_start
        self.root.title("P2P Share - Get started")
        self.root.geometry("520x340")
        self.root.minsize(460, 320)

        container = ttk.Frame(root, padding=28)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="P2P Share", font=("TkDefaultFont", 20, "bold")).pack(anchor="w")
        ttk.Label(
            container,
            text="Set up this device before connecting with others.",
            foreground="gray",
        ).pack(anchor="w", pady=(4, 22))

        ttk.Label(container, text="Device name").pack(anchor="w")
        self.name_var = tk.StringVar(value=initial_name or socket.gethostname())
        name_entry = ttk.Entry(container, textvariable=self.name_var)
        name_entry.pack(fill="x", pady=(6, 16))

        ttk.Label(container, text="Folder to share").pack(anchor="w")
        folder_row = ttk.Frame(container)
        folder_row.pack(fill="x", pady=(6, 18))
        self.folder_var = tk.StringVar(value=initial_folder)
        ttk.Entry(folder_row, textvariable=self.folder_var).pack(side="left", fill="x", expand=True)
        ttk.Button(folder_row, text="Browse", command=self.choose_folder).pack(side="left", padx=(8, 0))

        ttk.Button(container, text="Start sharing", command=self.start).pack(fill="x", ipady=5)
        self.root.bind("<Return>", lambda _event: self.start())
        name_entry.focus_set()

    def choose_folder(self):
        folder = filedialog.askdirectory(
            parent=self.root,
            title="Choose a folder to share",
            mustexist=True,
        )
        if folder:
            self.folder_var.set(folder)

    def start(self):
        name = self.name_var.get().strip()
        folder = self.folder_var.get().strip()

        if not name:
            messagebox.showerror("Missing device name", "Enter a name for this device.", parent=self.root)
            return

        if not folder or not os.path.isdir(folder):
            messagebox.showerror(
                "Choose a folder",
                "Select an existing folder that you want to share.",
                parent=self.root,
            )
            return

        self.on_start(name, os.path.abspath(folder))
