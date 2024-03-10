import os
import platform

def configure_firewall(port):
    system = platform.system().lower()
    if 'windows' in system:
        # Windows: Use netsh command to open port
        os.system(f"netsh advfirewall firewall add rule name='DecentralizedAppPort' dir=in action=allow protocol=TCP localport={port}")
    elif 'linux' in system:
        # Linux: Use ufw command if available
        os.system(f"ufw allow {port}/tcp")
    else:
        print("Unsupported operating system for automatic firewall configuration.")
