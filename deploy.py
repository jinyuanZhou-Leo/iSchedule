import os
import sys
import subprocess

print("Installing required packages...")
os.system("pip install -r requirements.txt")

try:
    print("Checking lxml library...")
    import lxml
except ImportError as e:
    print("lxml is not found, try to install...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "lxml"])
    except Exception as e:
        print(f"Unexpected error occured while installing lxml")
        raise e
    else:
        print("Successfully installed lxml")
else:
    print("lxml is already installed")
