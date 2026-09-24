import os
import platform
import shutil
import sys
import tarfile
import time
from functools import wraps
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from versions import CLANG_VERSIONS

CLANG_CUDA_MAX = {"128": "19", "129": "19", "130": "20", "134": "22"}

ROOT = Path.cwd() / "deps" / "clang"
DEST = ROOT.with_suffix(".tmp")

URL = "https://github.com/llvm/llvm-project/releases/download/llvmorg-{version}/{file}"

ASSETS = {
    ("linux",   "x86_64"):  ["LLVM-{version}-Linux-X64.tar.xz"],
    ("linux",   "aarch64"): ["LLVM-{version}-Linux-ARM64.tar.xz", "clang+llvm-{version}-aarch64-linux-gnu.tar.xz"],
    ("windows", "x86_64"):  ["clang+llvm-{version}-x86_64-pc-windows-msvc.tar.xz"],
    ("windows", "aarch64"): ["clang+llvm-{version}-aarch64-pc-windows-msvc.tar.xz"],
}

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

def resolve_version(arg):
    if arg == "cuda":
        # newest clang the installed CUDA accepts as nvcc host compiler
        code = os.getenv("CUDA_CODE")
        if code not in CLANG_CUDA_MAX:
            codes = ", ".join(sorted(CLANG_CUDA_MAX))
            sys.exit(f"Unknown CUDA_CODE '{code}' (expected one of: {codes})")
        arg = CLANG_CUDA_MAX[code]
    if arg in CLANG_VERSIONS:
        return CLANG_VERSIONS[arg]
    if all(p.isdigit() for p in arg.split(".")) and len(arg.split(".")) == 3:
        return arg
    known = ", ".join(f"{k} -> {v}" for k, v in sorted(CLANG_VERSIONS.items()))
    sys.exit(f"Unknown clang version '{arg}' (expected 'cuda', a major in {known} or a full X.Y.Z version)")

def asset_url(version, os_name, arch):
    if (os_name, arch) not in ASSETS:
        sys.exit(f"Unsupported platform: {os_name}/{arch}")
    for file in ASSETS[(os_name, arch)]:
        file = file.format(version=version).replace("+", "%2B")
        url = URL.format(version=version, file=file)
        try:
            with fetch(Request(url, method="HEAD")) as r:
                if r.status == 200:
                    return url
        except HTTPError:
            continue
    sys.exit(f"No clang {version} release asset found for {os_name}/{arch}")

def fetch(req):
    return urlopen(Request(req.full_url, headers={"User-Agent": "curl/8.0"}, method=req.get_method()), timeout=120)

@retry
def install_tar(url):
    def members(tar):
        for member in tar:
            parts = Path(member.name).parts
            if len(parts) > 1:
                member.name = str(Path(*parts[1:]))
                yield member

    with fetch(Request(url)) as r:
        with tarfile.open(fileobj=r, mode="r|*") as tar:
            tar.extractall(DEST, members=members(tar), filter="tar")

def main():
    if len(sys.argv) < 2:
        sys.exit("usage: install-clang.py <cuda|major|X.Y.Z> [arch] [os]")
    version = resolve_version(sys.argv[1])
    arch = sys.argv[2] if len(sys.argv) >= 3 else detect_arch()
    os_name = sys.argv[3] if len(sys.argv) >= 4 else detect_os()

    url = asset_url(version, os_name, arch)

    shutil.rmtree(DEST, ignore_errors=True)
    DEST.mkdir(parents=True)

    print(f"Installing Clang {version} ({os_name}-{arch})...")
    install_tar(url)
    print(f" - clang {version} ({os_name}-{arch})")

    shutil.rmtree(ROOT, ignore_errors=True)
    DEST.rename(ROOT)

if __name__ == "__main__":
    main()
