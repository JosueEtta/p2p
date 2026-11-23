P2P File Sharing (Python + Tkinter)

Run on Windows (Python 3.8+, no extra packages):
  Double-click run_demo.bat   -> opens three simulated computers (PC1, PC2, PC3)

To start one real device, run:
  python main.py --port 5001 --folder shared

The app automatically uses the computer's system hostname as its device name.
You can still override it when needed:
  python main.py --name MyDevice --port 5001 --folder shared

On first run Windows Firewall may ask for permission: click "Allow".
Names should be unique on the local network. Put files to share in the selected folder.
Use "Refresh peers" if a computer was started after the others.

Windows: run setup_firewall.bat once as administrator, and set your Wi-Fi network to "Private".
Devices found by a scan stay listed; scans retry 3 times, so one lost packet no longer hides a device.
