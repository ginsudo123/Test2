import os
import sys
import zipfile
import io
import tarfile
import subprocess

try:
    from cryptography.fernet import Fernet
except ImportError:
    print("cryptography module not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography"])
    from cryptography.fernet import Fernet


def main():
    # Load .env if present
    if os.path.exists(".env"):
        try:
            with open(".env", "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip().strip("'").strip('"'))
        except Exception as e:
            print(f"Warning: Could not parse .env file: {e}")

    key_str = os.environ.get("AES_SECRET_KEY")
    if not key_str:
        print("Error: AES_SECRET_KEY environment variable is not set!")
        sys.exit(1)

    encrypted_file = "test.enc"
    if not os.path.exists(encrypted_file):
        print(f"Error: Encrypted code archive '{encrypted_file}' not found!")
        sys.exit(1)

    print(f"Decrypting '{encrypted_file}'...")
    key = key_str.encode('utf-8')
    try:
        fernet = Fernet(key)
    except Exception as e:
        print(f"Invalid AES_SECRET_KEY format: {e}")
        sys.exit(1)

    with open(encrypted_file, 'rb') as f:
        encrypted_data = f.read()

    try:
        decrypted_data = fernet.decrypt(encrypted_data)
    except Exception as e:
        print(f"Decryption failed: {e}. Check if AES_SECRET_KEY matches.")
        sys.exit(1)

    print("Extracting code files...")
    zip_buffer = io.BytesIO(decrypted_data)
    with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
        zip_file.extractall(".")

    # Ensure chrome profile is prepared (from release archive or created)
    profile_target = os.path.join("code", "Amazon", "chrome_profile")
    if not os.path.exists(profile_target):
        tar_asset = "chrome_profile.tar.gz"
        enc_profile = "profile.enc"

        if os.path.exists(enc_profile):
            print(f"Decrypting release profile '{enc_profile}'...")
            try:
                with open(enc_profile, 'rb') as pf:
                    p_decrypted = fernet.decrypt(pf.read())
                with tarfile.open(fileobj=io.BytesIO(p_decrypted), mode="r:gz") as tar:
                    tar.extractall(path=os.path.join("code", "Amazon"))
                print(f"Successfully unpacked release profile into {profile_target}.")
            except Exception as pe:
                print(f"Could not unpack '{enc_profile}': {pe}")

        elif os.path.exists(tar_asset):
            print(f"Unpacking release profile '{tar_asset}'...")
            try:
                with tarfile.open(tar_asset, "r:gz") as tar:
                    tar.extractall(path=os.path.join("code", "Amazon"))
                print(f"Successfully unpacked release profile into {profile_target}.")
            except Exception as pe:
                print(f"Could not unpack '{tar_asset}': {pe}")

        if not os.path.exists(profile_target):
            os.makedirs(profile_target, exist_ok=True)

    main_script = os.path.join("code", "main.py")
    if not os.path.exists(main_script):
        print(f"Error: Framework entry point '{main_script}' not found!")
        sys.exit(1)

    print("Launching framework entry point (main.py)...")
    cmd = [sys.executable, main_script] + sys.argv[1:]
    try:
        sys.exit(subprocess.run(cmd).returncode)
    except Exception as e:
        print(f"Execution error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
