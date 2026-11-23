"""Tkinter interface: peer list, search, download, and upload."""
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from client import broadcast, client


def fmt_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


class App:
    def __init__(self, root, discovery, folder):
        self.root, self.discovery, self.folder = root, discovery, folder
        self.q = queue.Queue()
        root.title(f"P2P Share - {discovery.name}")
        root.geometry("760x460")

        top = ttk.Frame(root, padding=6)
        top.pack(fill="x")
        ttk.Label(top, text=f"You: {discovery.name}  (folder: {folder})").pack(side="left")
        ttk.Button(top, text="Refresh peers", command=self.refresh).pack(side="right")

        body = ttk.Frame(root, padding=6)
        body.pack(fill="both", expand=True)

        left = ttk.LabelFrame(body, text="Available devices")
        left.pack(side="left", fill="y")
        self.peer_list = tk.Listbox(left, width=22, exportselection=False)
        self.peer_list.pack(fill="y", expand=True, padx=4, pady=4)
        self.peer_list.bind("<<ListboxSelect>>", self.browse_peer)
        ttk.Button(left, text="Upload file", command=self.upload).pack(fill="x", padx=4, pady=(0, 4))

        right = ttk.Frame(body)
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))
        bar = ttk.Frame(right)
        bar.pack(fill="x")
        self.search_var = tk.StringVar()
        entry = ttk.Entry(bar, textvariable=self.search_var)
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda e: self.search())
        ttk.Button(bar, text="Search all devices", command=self.search).pack(side="left", padx=4)

        cols = ("file", "size", "peer")
        self.tree = ttk.Treeview(right, columns=cols, show="headings", selectmode="browse")
        for c, w in zip(cols, (320, 80, 120)):
            self.tree.heading(c, text=c.capitalize())
            self.tree.column(c, width=w)
        self.tree.pack(fill="both", expand=True, pady=6)
        ttk.Button(right, text="Download selected", command=self.download).pack(anchor="e")

        self.status = tk.StringVar(value="Starting...")
        ttk.Label(root, textvariable=self.status, relief="sunken", anchor="w").pack(fill="x")

        root.after(100, self._poll)
        self.refresh()

    def _poll(self):
        while not self.q.empty():
            self.q.get()()
        self.root.after(100, self._poll)

    def _bg(self, work, done):
        def run():
            try:
                result = work()
                self.q.put(lambda: done(result, None))
            except Exception as e:
                self.q.put(lambda: done(None, e))
        threading.Thread(target=run, daemon=True).start()

    def refresh(self):
        self.status.set("Scanning network for devices...")
        self._bg(self.discovery.refresh, self._show_peers)

    def _show_peers(self, peers, err):
        self.peer_list.delete(0, "end")
        for name in sorted(peers):
            self.peer_list.insert("end", name)
        self.status.set(f"{len(peers)} device(s) found")

    def _fill(self, rows):
        self.tree.delete(*self.tree.get_children())
        for name, size, peer in rows:
            self.tree.insert("", "end", values=(name, fmt_size(size), peer))

    def browse_peer(self, _event=None):
        sel = self.peer_list.curselection()
        if not sel:
            return
        name = self.peer_list.get(sel[0])
        peer = broadcast.get_peers().get(name)
        if not peer:
            self.status.set("That device is no longer available. Refresh peers.")
            return
        ip, port = peer
        self.status.set(f"Loading files from {name}...")

        def done(files, err):
            if err:
                self.status.set(f"Could not reach {name}: {err}")
                return
            self._fill([(f["name"], f["size"], name) for f in files])
            self.status.set(f"{len(files)} file(s) on {name}")
        self._bg(lambda: client.list_files(ip, port), done)

    def search(self):
        term = self.search_var.get().strip().lower()
        peers = broadcast.get_peers()
        self.status.set("Searching all devices...")

        def work():
            rows = []
            for name, (ip, port) in peers.items():
                try:
                    for file in client.list_files(ip, port):
                        if term in file["name"].lower():
                            rows.append((file["name"], file["size"], name))
                except OSError:
                    pass
            return rows

        def done(rows, err):
            self._fill(rows or [])
            self.status.set(f"{len(rows or [])} match(es) across {len(peers)} device(s)")
        self._bg(work, done)

    def download(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Download", "Select a file first.")
            return
        fname, _size, peer = self.tree.item(sel[0], "values")
        device = broadcast.get_peers().get(peer)
        if not device:
            self.status.set("That device is no longer available. Refresh peers.")
            return
        ip, port = device
        self.status.set(f"Downloading {fname} from {peer}...")

        def done(path, err):
            self.status.set(f"Error: {err}" if err else f"Saved to {path}")
        self._bg(lambda: client.download(ip, port, fname, self.folder), done)

    def upload(self):
        sel = self.peer_list.curselection()
        if not sel:
            messagebox.showinfo("Upload", "Select a device to receive the file first.")
            return

        peer = self.peer_list.get(sel[0])
        device = broadcast.get_peers().get(peer)
        if not device:
            self.status.set("That device is no longer available. Refresh peers.")
            return

        file_path = filedialog.askopenfilename(parent=self.root, title=f"Choose a file to send to {peer}")
        if not file_path:
            return

        ip, port = device
        file_name = os.path.basename(file_path)
        self.status.set(f"Sending {file_name} to {peer}...")

        def done(received_name, err):
            if err:
                self.status.set(f"Upload failed: {err}")
            else:
                self.status.set(f"Sent to {peer} as {received_name}")
        self._bg(lambda: client.upload(ip, port, file_path), done)
