"""Tkinter interface: peer list, search, and download."""
import os
import queue
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
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
        self._refreshing = False
        root.title(f"P2P Share - {discovery.name}")
        root.geometry("760x500")

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

        transfer = ttk.LabelFrame(root, text="File transfer", padding=6)
        transfer.pack(fill="x", padx=6, pady=(0, 6))
        self.progress_text = tk.StringVar(value="No active transfer")
        ttk.Label(transfer, textvariable=self.progress_text).pack(anchor="w")
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure(
            "Green.Horizontal.TProgressbar",
            troughcolor="#e5e7eb",
            background="#16a34a",
            bordercolor="#e5e7eb",
            lightcolor="#16a34a",
            darkcolor="#16a34a",
        )
        self.progress = ttk.Progressbar(
            transfer,
            mode="determinate",
            maximum=100,
            style="Green.Horizontal.TProgressbar",
        )
        self.progress.pack(fill="x", pady=(4, 0))

        self.status = tk.StringVar(value="Starting...")
        ttk.Label(root, textvariable=self.status, relief="sunken", anchor="w").pack(fill="x")

        root.after(100, self._poll)
        self.refresh()
        root.after(60_000, self._auto_refresh)

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
                self.q.put(lambda error=e: done(None, error))
        threading.Thread(target=run, daemon=True).start()

    def _set_progress(self, transferred, total, direction):
        percent = 100 if total == 0 else transferred * 100 / total
        self.progress["value"] = percent
        self.progress_text.set(
            f"{direction}: {fmt_size(transferred)} / {fmt_size(total)} ({percent:.1f}%)"
        )

    def refresh(self):
        if self._refreshing:
            return
        self._refreshing = True
        self.status.set("Scanning network for devices...")
        self._bg(self.discovery.refresh, self._show_peers)

    def _auto_refresh(self):
        self.refresh()
        self.root.after(60_000, self._auto_refresh)

    def _show_peers(self, peers, err):
        self._refreshing = False
        if err:
            self.status.set(f"Could not refresh devices: {err}")
            return
        selected = self.peer_list.curselection()
        selected_name = self.peer_list.get(selected[0]) if selected else None
        self.peer_list.delete(0, "end")
        for name in sorted(peers):
            self.peer_list.insert("end", name)
        if selected_name in peers:
            index = sorted(peers).index(selected_name)
            self.peer_list.selection_set(index)
        self.status.set(f"{len(peers)} other device(s) found")

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
        term = self.search_var.get().strip().casefold()
        peers = broadcast.get_peers()

        self.status.set(
            f"Searching this device and {len(peers)} discovered device(s)..."
        )

        def search_local():
            matches = []
            try:
                with os.scandir(self.folder) as entries:
                    for entry in entries:
                        if (
                            entry.is_file()
                            and not entry.name.endswith(".part")
                            and not entry.name.startswith(".p2p-")
                            and term in entry.name.casefold()
                        ):
                            matches.append(
                                (entry.name, entry.stat().st_size, self.discovery.name)
                            )
            except OSError as exc:
                raise RuntimeError(f"Could not search this device's folder: {exc}") from exc
            return matches

        def search_peer(name, address):
            ip, port = address
            files = client.list_files(ip, port)
            matches = [
                (file["name"], file["size"], name)
                for file in files
                if term in file["name"].casefold()
            ]
            return matches

        def work():
            rows = search_local()
            failures = []

            with ThreadPoolExecutor(max_workers=max(1, min(len(peers), 8))) as executor:
                futures = {
                    executor.submit(search_peer, name, address): name
                    for name, address in peers.items()
                }

                for future in as_completed(futures):
                    name = futures[future]
                    try:
                        rows.extend(future.result())
                    except Exception as exc:
                        failures.append((name, str(exc)))

            rows.sort(key=lambda row: (row[0].casefold(), row[2].casefold()))
            return rows, failures

        def done(result, err):
            if err:
                self._fill([])
                self.status.set(f"Search failed: {err}")
                return

            rows, failures = result
            self._fill(rows)

            if failures:
                failed_names = ", ".join(name for name, _ in failures)
                self.status.set(
                    f"{len(rows)} match(es). Could not search {len(failures)} "
                    f"device(s): {failed_names}"
                )
            else:
                self.status.set(
                    f"{len(rows)} match(es) found on this device and "
                    f"{len(peers)} other device(s)"
                )

        self._bg(work, done)

    def download(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Download", "Select a file first.")
            return
        fname, _size, peer = self.tree.item(sel[0], "values")
        if peer == self.discovery.name:
            self.status.set("This file is already on your device.")
            return
        device = broadcast.get_peers().get(peer)
        if not device:
            self.status.set("That device is no longer available. Refresh peers.")
            return
        ip, port = device
        self.progress["value"] = 0
        self.progress_text.set(f"Downloading {fname} from {peer}...")
        self.status.set(f"Downloading {fname} from {peer}...")

        def report(received, total):
            self.q.put(lambda received=received, total=total: self._set_progress(received, total, "Receiving"))

        def done(path, err):
            if err:
                self.progress_text.set("Download failed")
                self.status.set(f"Download failed: {err}")
            else:
                self.progress["value"] = 100
                self.progress_text.set("Download complete")
                self.status.set(f"Saved to {path}")
        self._bg(lambda: client.download(ip, port, fname, self.folder, report), done)
