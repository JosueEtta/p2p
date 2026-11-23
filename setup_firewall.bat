@echo off
rem Right-click this file and choose "Run as administrator" (once per Windows computer).
netsh advfirewall firewall add rule name="P2P UDP" dir=in action=allow protocol=UDP localport=50000-50009
netsh advfirewall firewall add rule name="P2P TCP" dir=in action=allow protocol=TCP localport=5001-5010
pause
