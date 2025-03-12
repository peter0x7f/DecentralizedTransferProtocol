import os
import subprocess
import ctypes
import sys

def is_admin():
    """Check if the script is running with administrative privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def create_and_encrypt_vhd(vhd_path, drive_letter, size_gb, password):
    """
    Create a VHD, mount it, and encrypt it with BitLocker.

    :param vhd_path: The full path where the VHD will be created.
    :param drive_letter: The drive letter to assign to the mounted VHD.
    :param size_gb: The size of the VHD in gigabytes.
    :param password: The password to use for BitLocker encryption.
    """
    size_mb = size_gb * 1024
    create_vhd_script = f"""
    create vdisk file="{vhd_path}" maximum={size_mb} type=expandable
    select vdisk file="{vhd_path}"
    attach vdisk
    create partition primary
    format fs=ntfs quick
    assign letter={drive_letter}
    """
    script_file = "create_vhd_script.txt"
    with open(script_file, "w") as f:
        f.write(create_vhd_script)
    try:
        subprocess.run(["diskpart", "/s", script_file], check=True)
        print(f"VHD created and mounted as drive {drive_letter}:")
    except subprocess.CalledProcessError as e:
        print("Error during VHD creation:", e)
        return
    finally:
        os.remove(script_file)

    # Convert the password to a secure string
    secure_password = f'ConvertTo-SecureString "{password}" -AsPlainText -Force'

    # Enable BitLocker with the password protector
    enable_cmd = (
        f"powershell.exe -Command "
        f"$SecureString = {secure_password}; "
        f"Enable-BitLocker -MountPoint {drive_letter}: "
        f"-EncryptionMethod Aes256 "
        f"-PasswordProtector -Password $SecureString"
    )

    try:
        subprocess.run(enable_cmd, check=True, shell=True)
        print(f"BitLocker encryption initiated on drive {drive_letter}:")
    except subprocess.CalledProcessError as e:
        print(f"Error enabling BitLocker on drive {drive_letter}: {e}")

def main():
    if not is_admin():
        print("This script requires administrative privileges. Restarting with elevated permissions...")
        # Restart the script with elevated permissions
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, ' '.join(sys.argv), None, 1)
        return

    vhd_path = os.path.join(os.getcwd(), "test.vhd")
    size_gb = 1  # Size of the VHD
    drive_letter = "Z"  # Drive letter to assign to the VHD
    password = "YourSecurePassword123"  # Replace with a strong password
    create_and_encrypt_vhd(vhd_path, drive_letter, size_gb, password)

if __name__ == "__main__":
    main()
