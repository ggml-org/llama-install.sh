import sys
import time
import zipfile
import tempfile
from urllib.request import urlopen, Request
import tarfile
import shutil
import platform
from functools import wraps
from pathlib import Path
from versions import ZIG_VERSION as VERSION

ROOT = Path.cwd() / "deps" / "zig"
DEST = ROOT.with_suffix(".tmp")

URL = "https://zigmirror.com"

def retry(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        for i in reversed(range(5)):
            try:
                return func(*args, **kwargs)
            except Exception:
                if not i:
                    raise
                time.sleep(10)
    return wrapper

def detect_arch():
    machine = platform.machine().lower()
    if machine in ["x86_64", "amd64"]:
        return "x86_64"
    if machine in ["aarch64", "arm64"]:
        return "aarch64"
    return machine

def detect_os():
    system = platform.system()
    if system == "Linux":
        return "linux"
    if system == "Windows":
        return "windows"
    if system == "Darwin":
        return "macos"
    return system.lower()

def fetch(file):
    req = Request(f"{URL}/{file}", headers={"User-Agent": "curl/8.0"})
    return urlopen(req, timeout=60)

def strip_top(member_name):
    parts = Path(member_name).parts
    if len(parts) > 1:
        return str(Path(*parts[1:]))
    return None

@retry
def install_tar(file):
    def members(tar):
        for member in tar:
            name = strip_top(member.name)
            if name:
                member.name = name
                yield member

    with fetch(file) as r:
        with tarfile.open(fileobj=r, mode="r|*") as tar:
            tar.extractall(DEST, members=members(tar), filter='tar')

@retry
def install_zip(file):
    with fetch(file) as r, tempfile.NamedTemporaryFile(suffix=".zip") as tmp:
        shutil.copyfileobj(r, tmp)
        tmp.flush()
        with zipfile.ZipFile(tmp) as z:
            for info in z.infolist():
                name = strip_top(info.filename)
                if not name or info.is_dir():
                    continue
                target = DEST / name
                target.parent.mkdir(parents=True, exist_ok=True)
                with z.open(info) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)

def main():
    arch = sys.argv[1] if len(sys.argv) >= 2 else detect_arch()
    osname = detect_os()

    if osname == "windows":
        file = f"zig-{arch}-windows-{VERSION}.zip"
        install = install_zip
    else:
        file = f"zig-{arch}-{osname}-{VERSION}.tar.xz"
        install = install_tar

    shutil.rmtree(DEST, ignore_errors=True)
    DEST.mkdir(parents=True)

    print(f"Installing Zig {VERSION} ({arch}/{osname})...")
    install(file)
    print(f" - zig {VERSION} ({arch}/{osname})")

    DEST.rename(ROOT)

if __name__ == "__main__":
    main()
