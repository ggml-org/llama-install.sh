import hashlib
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

JSIGN_VERSION = "7.6"
JSIGN_SHA256 = "6cf58aa080e7ff82656f320cff8d4a3bff30408df8766806dcba3740dd839fa5"

SIGN_ENV = (
    "AZURE_TENANT_ID",
    "AZURE_CLIENT_ID",
    "AZURE_CLIENT_SECRET",
    "AZURE_TS_ENDPOINT",
    "AZURE_TS_ACCOUNT_NAME",
    "AZURE_TS_PROFILE_NAME",
)

files = [
    str(file)
    for arg in sys.argv[1:]
    for file in (sorted(Path(arg).rglob("*.exe")) if Path(arg).is_dir() else [Path(arg)])
]

if not files:
    sys.exit("usage: sign.py FILE|DIR...")

missing = [name for name in SIGN_ENV if not os.environ.get(name)]

if len(missing) == len(SIGN_ENV):
    print("Signing skipped, no configuration", file=sys.stderr)
    sys.exit(0)

if missing:
    sys.exit(f"Missing signing configuration: {', '.join(missing)}")

jar = Path(__file__).resolve().parent.parent / "deps" / "jsign" / f"jsign-{JSIGN_VERSION}.jar"

if not jar.exists():
    print(f"Installing Jsign {JSIGN_VERSION}...")
    url = f"https://repo1.maven.org/maven2/net/jsign/jsign/{JSIGN_VERSION}/jsign-{JSIGN_VERSION}.jar"
    data = urlopen(Request(url, headers={"User-Agent": "curl/8.0"}), timeout=60).read()
    if hashlib.sha256(data).hexdigest() != JSIGN_SHA256:
        sys.exit("jsign: checksum mismatch")
    jar.parent.mkdir(parents=True, exist_ok=True)
    jar.write_bytes(data)
elif hashlib.sha256(jar.read_bytes()).hexdigest() != JSIGN_SHA256:
    sys.exit(f"{jar}: checksum mismatch")

cmd = [
    "java", "-jar", str(jar), "sign",
    "--storetype", "TRUSTEDSIGNING",
    "--keystore", os.environ["AZURE_TS_ENDPOINT"],
    "--alias", f'{os.environ["AZURE_TS_ACCOUNT_NAME"]}/{os.environ["AZURE_TS_PROFILE_NAME"]}',
    "--alg", "SHA-256",
    "--tsmode", "RFC3161",
    "--tsaurl", "http://timestamp.acs.microsoft.com",
]
try:
    for file in files:
        for attempt in range(3):
            code = subprocess.run([*cmd, file]).returncode
            if code == 0:
                break
            if code < 0 or attempt == 2:
                sys.exit(code)
            delay = 5 * (attempt + 1)
            print(f"Signing failed for {file}, retrying in {delay}s...", file=sys.stderr)
            time.sleep(delay)
except FileNotFoundError:
    sys.exit("java not found, install a java runtime to sign")
