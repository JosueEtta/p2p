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


Uploading a file to another device:
1. Start sharing on both devices and make sure they are on the same local network.
2. On the sending device, select the receiving device in Available devices.
3. Click Upload file and choose a file from your computer.
4. The file is transferred directly to the receiving device's shared folder.
5. If a file with the same name already exists, the receiver saves the incoming file with a numbered name instead of overwriting the existing file.

The receiving device must be running P2P Share and its firewall must allow incoming TCP connections on the configured file-server port.
