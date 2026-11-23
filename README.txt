P2P File Sharing (Python + Tkinter)

Run on Windows (Python 3.8+, no extra packages):
  Double-click run_demo.bat   -> opens three simulated computers (PC1, PC2, PC3)
or, one terminal per computer:
  python main.py --name PC1 --port 5001 --folder shared\PC1
  python main.py --name PC2 --port 5002 --folder shared\PC2
  python main.py --name PC3 --port 5003 --folder shared\PC3

On first run Windows Firewall may ask for permission: click "Allow".
Names must be unique. Put files to share in each computer's folder.
Use "Refresh peers" if a computer was started after the others.

Windows: run setup_firewall.bat once as administrator, and set your Wi-Fi network to "Private".
Devices found by a scan stay listed; scans retry 3 times, so one lost packet no longer hides a device.
