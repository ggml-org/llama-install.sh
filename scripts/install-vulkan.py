import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import zipfile
from functools import wraps
from pathlib import Path
from urllib.request import urlopen, Request

from versions import VULKAN_VERSION as VERSION

ROOT = Path.cwd() / "deps" / "vulkan"
DEST = ROOT.with_suffix(".tmp")

URL = "https://sdk.lunarg.com/sdk/download"

# everything the build needs from the SDK is the headers, the glslc
# compiler and the libs it depends on
KEEP = ("bin", "include", "lib")

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
    if machine in ("x86_64", "amd64"):
        return "x86_64"
    if machine in ("aarch64", "arm64"):
        return "aarch64"
    return machine

def detect_os():
    system = platform.system().lower()
    return {"darwin": "macos"}.get(system, system)

@retry
def install(file):
    req = Request(f"{URL}/{VERSION}/linux/{file}.tar.xz", headers={"User-Agent": "curl/8.0"})

    def members(tar):
        for member in tar:
            # skip the version/arch dirs at the top of the archive
            # (e.g. 1.4.357.1/x86_64/include/... -> include/...)
            parts = Path(member.name).parts
            if len(parts) > 3 and parts[2] in KEEP:
                member.name = str(Path(*parts[2:]))
                yield member

    with urlopen(req, timeout=300) as r, tarfile.open(fileobj=r, mode="r|*") as tar:
        tar.extractall(DEST, members=members(tar), filter="tar")

# the macOS SDK is a zip wrapping a Qt Installer Framework app, which
# installs rootlessly (no sudo) - we drive it headless into a temp dir,
# then lift the payload out of its macOS/ wrapper to match the linux
# layout (deps/vulkan/{bin,include,lib})
@retry
def install_mac():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        archive = tmp / "vulkansdk.zip"
        req = Request(f"{URL}/{VERSION}/mac/vulkansdk-macos-{VERSION}.zip",
                      headers={"User-Agent": "curl/8.0"})
        with urlopen(req, timeout=600) as r, open(archive, "wb") as f:
            shutil.copyfileobj(r, f)
        with zipfile.ZipFile(archive) as z:
            z.extractall(tmp)
        app = next(tmp.glob("*.app"))
        exe = next((app / "Contents" / "MacOS").iterdir())
        exe.chmod(0o755)
        # the installer needs an empty install root of its own (it backs
        # up its operations), so keep it away from the extracted app/zip
        root = tmp / "root"
        # only the core component (headers, loader, tools) - skip
        # com.lunarg.vulkan.usr ("System Global Installation"),
        # which drops vkcube.app in /Applications and a MoltenVK ICD
        # into /usr/local/lib
        subprocess.run([exe, "in", "--root", root, "-c", "--al", "--da",
                        "com.lunarg.vulkan.core"], check=True)
        for name in KEEP:
            shutil.move(root / "macOS" / name, DEST / name)

def main():
    arch = sys.argv[1] if len(sys.argv) >= 2 else detect_arch()
    osname = detect_os()

    if osname not in ("linux", "macos"):
        sys.exit(f"Vulkan builds are only supported on linux/macos (got '{osname}')")
    if osname == "linux" and arch != "x86_64":
        sys.exit(f"LunarG only publishes x86_64 {osname} SDKs (got '{arch}')")

    if (ROOT / "include/vulkan/vulkan.h").exists():
        print(f" - Vulkan SDK {VERSION} found in {ROOT}")
        return

    print(f"Installing Vulkan SDK {VERSION} ({arch}/{osname})...")
    shutil.rmtree(ROOT, ignore_errors=True)
    shutil.rmtree(DEST, ignore_errors=True)
    DEST.mkdir(parents=True)

    if osname == "macos":
        install_mac()
    else:
        install(f"vulkansdk-linux-{arch}-{VERSION}")

    DEST.rename(ROOT)

    if not (ROOT / "include/vulkan/vulkan.h").exists():
        sys.exit("installer finished but headers are missing - SDK layout changed?")

    print(f" - Vulkan SDK {VERSION} ({arch}/{osname})")

if __name__ == "__main__":
    main()
