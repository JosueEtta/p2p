@echo off
rem Starts three simulated computers, each with its own port and folder.
start "PC1" python main.py --name PC1 --port 5001 --folder shared\PC1
start "PC2" python main.py --name PC2 --port 5002 --folder shared\PC2
start "PC3" python main.py --name PC3 --port 5003 --folder shared\PC3
