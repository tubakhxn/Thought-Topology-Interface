#!/usr/bin/env python3
# setup_and_run.py — one-click install + launch

import subprocess, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
REQ  = os.path.join(HERE, "requirements.txt")

print("Installing dependencies …")
subprocess.check_call([sys.executable, "-m", "pip", "install",
                       "-r", REQ, "--quiet"])
print("All dependencies installed.\n")

# launch
os.chdir(HERE)
subprocess.check_call([sys.executable, "main.py"])