import io
import json
import os
import platform
import shutil
import sys
import tarfile
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps
from pathlib import Path
from urllib.request import urlopen

from versions import CUDA_VERSIONS

URL = "https://developer.download.nvidia.com/compute/cuda/redist"

def cuda_version():
    code = os.getenv("CUDA_CODE")
    if code in CUDA_VERSIONS:
        return CUDA_VERSIONS[code]
    codes = ", ".join(sorted(CUDA_VERSIONS))
    sys.exit(f"Unknown CUDA_CODE '{code}' (expected one of: {codes})")

VERSION = cuda_version()

ROOT = Path.cwd() / "deps" / "cuda"
DEST = ROOT.with_suffix(".tmp")

COMPONENTS = [
    ("libcublas",      "target", None, None),
    ("cuda_cudart",    "target", None, None),
    ("cuda_cccl",      "target", None, lambda m: "cccl" if "cccl" in m else "cuda_cccl"),
    ("cuda_crt",       "target", lambda m, t: "cuda_crt" in m, None),
    ("libnvvm",        "host",   lambda m, t: "libnvvm" in m, None),
    ("cuda_nvcc",      "host",   None, None),
    ("cuda_nvprune",   "host",   lambda m, t: t == "linux", None),
    ("cuda_cuobjdump", "host",   lambda m, t: t == "linux", None),
]

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

def platform_key(arch, os_name):
    if os_name == "linux":
        return {"x86_64": "linux-x86_64", "aarch64": "linux-sbsa"}[arch]

    if os_name == "windows":
        return {"x86_64": "windows-x86_64", "aarch64": "windows-arm64"}[arch]

    sys.exit(f"Unsupported OS: {os_name}")

def strip_top(path):
    parts = Path(path).parts
    return str(Path(*parts[1:])) if len(parts) > 1 else ""

def _extract_zip(data, dest):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for member in z.infolist():
            rel = strip_top(member.filename)
            if not rel or member.is_dir():
                continue
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(member) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)

def _extract_tar(data, dest):
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as tar:
        members = []
        for member in tar.getmembers():
            rel = strip_top(member.name)
            if not rel:
                continue
            member.name = rel
            members.append(member)
        tar.extractall(dest, members=members, filter="tar")

def make_task(manifest, component, key, plat):
    data = manifest[key(manifest) if key else component]
    label = f"{data['name']} version {data['version']} ({plat})"
    return (label, data[plat]["relative_path"])

def collect_tasks(manifest, target_plat, host_plat, target_os):
    tasks = []
    for name, which, gate, key in COMPONENTS:
        if gate is not None and not gate(manifest, target_os):
            continue
        plat = target_plat if which == "target" else host_plat
        tasks.append(make_task(manifest, name, key, plat))
    return tasks

@retry
def download_manifest():
    with urlopen(f"{URL}/redistrib_{VERSION}.json", timeout=60) as r:
        return json.load(r)

@retry
def install_component(name, file):
    with urlopen(f"{URL}/{file}", timeout=120) as r:
        data = r.read()

    if file.endswith(".zip"):
        _extract_zip(data, DEST)
    else:
        _extract_tar(data, DEST)

    return f" - {name}"

def main():
    arch = sys.argv[1] if len(sys.argv) >= 2 else detect_arch()
    target_os = sys.argv[2] if len(sys.argv) >= 3 else os.getenv("CUDA_TARGET_OS", detect_os())

    host_os = detect_os()
    host_plat = platform_key(arch, host_os)
    target_plat = platform_key(arch, target_os)

    cross = host_os != target_os
    print(f"Installing CUDA {VERSION} (arch={arch}, target={target_os}"
          f"{f', host={host_os}' if cross else ''})...")

    manifest = download_manifest()
    tasks = collect_tasks(manifest, target_plat, host_plat, target_os)

    shutil.rmtree(DEST, ignore_errors=True)
    DEST.mkdir(parents=True)

    with ThreadPoolExecutor(2) as pool:
        futures = [pool.submit(install_component, name, file) for name, file in tasks]
        for f in as_completed(futures):
            print(f.result())

    DEST.rename(ROOT)

    if target_os == "linux":
        (ROOT / "lib64").symlink_to("lib")


if __name__ == "__main__":
    main()
