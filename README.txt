P2P File Sharing (Python + Tkinter)

Run on Windows (Python 3.8+, no extra packages):
  Double-click run_demo.bat   -> opens three simulated devices (PC1, PC2, PC3)

To start one device, run:
  python main.py --port 5001

A startup screen appears before the main interface. Enter a device name and choose an existing folder with Browse. The computer hostname and the shared folder are prefilled as convenient defaults. Click Start sharing to begin peer discovery and open the main file-sharing interface.

You can provide initial values from the command line:
  python main.py --name MyDevice --port 5001 --folder shared
These values are editable on the startup screen.

On first run Windows Firewall may ask for permission: click "Allow".
Choose a unique device name on the local network. Use "Refresh peers" if a computer was started after the others.

Windows: run setup_firewall.bat once as administrator, and set your Wi-Fi network to "Private".
Devices found by a scan stay listed; scans retry 3 times, so one lost packet no longer hides a device.


File sharing features:
- Discover other devices on the local network.
- Browse and search files in connected devices' shared folders.
- Download files directly from another device into your configured shared folder.
- Monitor download progress in the green progress bar.

The remote device must be running P2P Share and its firewall must allow incoming TCP connections on its configured file-server port.
