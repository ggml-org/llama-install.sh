import json
import os
import random
import re
import shutil
import statistics
import subprocess
import sys
from pathlib import Path

NUM_ROUNDS = 20
ALPHA = 0.05
DROP_TOLERANCE = 0.05
SEED = 42
WIN32 = sys.platform == "win32"

def download(version):
    suffix = ".exe" if WIN32 else ""
    tag = version.split("-")[0] if version else None

    if tag:
        dest = Path(f"llama-app-{tag}{suffix}").resolve()
        if dest.exists():
            return dest

    env = os.environ.copy()
    env["LLAMA_VERSION"] = version or ""
    env["SKIP_INSTALL"] = "1"

    cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", "install.ps1"] if WIN32 else ["sh", "install.sh"]
    src = (Path(os.environ["LOCALAPPDATA"]) / "llama-app/llama.exe") if WIN32 else (Path.home() / ".llama-app/llama")

    subprocess.run(cmd, check=True, env=env)
    r = subprocess.run([str(src), "version"], capture_output=True, text=True)

    if r.returncode != 0:
        sys.exit("Error: could not detect llama version")

    out = (r.stdout + r.stderr).strip()
    m = re.search(r"(?:build |^b)(\d+)", out)
    if not m:
        sys.exit(f"Error: could not detect llama version (got {out!r})")
    detected = "b" + m.group(1)

    if version and detected != version:
        sys.exit(f"Error: version mismatch (expected {version}, got {detected})")

    dest = Path(f"llama-app-{detected}{suffix}").resolve()
    shutil.copy2(src, dest)
    return dest

def run_bench(binary, model_tag):
    try:
        r = subprocess.run([str(binary), "bench", "--offline", "-fa", "0,1", "-hf", model_tag, "-o", "jsonl", "-r", "10"],
                           capture_output=True, text=True, timeout=300)
    except (subprocess.TimeoutExpired, OSError) as e:
        print(f"  error: {e}")
        return None
    if r.returncode != 0:
        print(f"  error: {r.stderr.strip()}")
        return None

    metrics = {}
    for line in r.stdout.splitlines():
        if not line.startswith("{"):
            continue
        obj = json.loads(line)
        test = f"pp{obj['n_prompt']}" if obj["n_prompt"] else f"tg{obj['n_gen']}"
        key = f"{test}/fa{int(obj['flash_attn'])}"
        metrics[key] = obj["avg_ts"]
    return metrics

def collect_pairs(base_bin, cur_bin, model_tag, rounds=NUM_ROUNDS):
    base_s, cur_s = {}, {}

    for i in range(rounds):
        base_first = random.Random(SEED + i).random() < 0.5
        first, second = (base_bin, cur_bin) if base_first else (cur_bin, base_bin)
        fm = run_bench(first, model_tag)
        sm = run_bench(second, model_tag)
        if fm is None or sm is None:
            print(f" {i+1}/{rounds}: skipped (run failed)")
            continue
        bm, cm = (fm, sm) if base_first else (sm, fm)
        shared = set(bm) & set(cm)
        for k in shared:
            base_s.setdefault(k, []).append(bm[k])
            cur_s.setdefault(k, []).append(cm[k])
        print(f" {i+1:>2}/{rounds}:  " + "  ".join(f"{k} {bm[k]:.0f}/{cm[k]:.0f}" for k in sorted(shared)))

    return base_s, cur_s

def holm_bonferroni(p_raws, alpha=ALPHA):
    m = len(p_raws)
    indexed = sorted(enumerate(p_raws), key=lambda x: x[1])
    p_adjs = [0.0] * m
    prev = 0.0
    for rank, (orig, p) in enumerate(indexed, 1):
        adj = min(max(p * (m - rank + 1), prev), 1.0)
        p_adjs[orig] = adj
        prev = adj
    return p_adjs, [p < alpha for p in p_adjs]

def sign_perm_test(base, cur):
    """Exact one-sided sign permutation test: H1 mean(base-cur) > 0."""
    d = [b - c for b, c in zip(base, cur)]
    n = len(d)
    if n < 2:
        return 1.0
    observed = sum(d)
    count = 0
    for mask in range(1 << n):
        s = sum(d[i] if (mask >> i) & 1 else -d[i] for i in range(n))
        if s >= observed:
            count += 1
    return count / (1 << n)

def compare(base_s, cur_s):
    keys = sorted(set(base_s) | set(cur_s))
    results = {}
    p_raws = []

    for key in keys:
        b, c = base_s.get(key, []), cur_s.get(key, [])
        n = min(len(b), len(c))
        bn, cn = b[:n], c[:n]
        bm = statistics.mean(bn) if n else 0.0
        cm = statistics.mean(cn) if n else 0.0
        rel_drop = (bm - cm) / bm if bm else 0.0

        p_raws.append(sign_perm_test(bn, cn))
        results[key] = dict(
            p_adj=1.0, sig=False, base_mean=bm, cur_mean=cm, n=n,
            rel_drop=rel_drop, worse=False,
        )

    p_adjs, rejects = holm_bonferroni(p_raws)

    for key, pa, rej in zip(keys, p_adjs, rejects):
        results[key]["p_adj"] = pa
        results[key]["sig"] = rej
        results[key]["worse"] = rej and results[key]["rel_drop"] >= DROP_TOLERANCE

    return results

def main():
    if len(sys.argv) < 2 or len(sys.argv) > 4:
        sys.exit(f"Usage: {sys.argv[0]} REPO/MODEL:QUANT [VERSION_BASE [VERSION_CURRENT]]")

    model_tag = sys.argv[1]
    base_ver = sys.argv[2] if len(sys.argv) > 2 else None
    cur_ver = sys.argv[3] if len(sys.argv) > 3 else None

    if not base_ver and not cur_ver:
        cur_ver = os.environ.get("LLAMA_VERSION")
        if not cur_ver:
            sys.exit(f"VERSION_CURRENT required (or set LLAMA_VERSION)")

    base_bin = download(base_ver)
    cur_bin = download(cur_ver)
    base_s, cur_s = collect_pairs(base_bin, cur_bin, model_tag)

    if not any(cur_s.values()):
        print(f"skipped: {model_tag} produced no results (model or quant may not exist)")
        sys.exit(0)

    n = min(len(v) for v in cur_s.values())

    if n < 2:
        sys.exit(f"not enough paired runs ({n})")

    comp = compare(base_s, cur_s)
    any_worse = any(r["worse"] for r in comp.values())

    for key in comp:
        r = comp[key]
        verdict = "WORSE" if r["worse"] else "ok"
        print(f"{key:>10}: {r['base_mean']:>6.2f} {r['cur_mean']:>6.2f} p={r['p_adj']:.4f} {verdict}")

    sys.exit(1 if any_worse else 0)


if __name__ == "__main__":
    main()
