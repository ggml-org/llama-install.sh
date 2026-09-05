import os
import subprocess
from collections import defaultdict
import json
import platform
import stat
import urllib.request
from pathlib import Path
from ruamel.yaml import YAML

def get_unzstd(os_name=None, arch=None):
    if not os_name:
        os_map = {
            'darwin': 'macos',
        }
        system = platform.system().lower()
        os_name = os_map.get(system, system)

    if not arch:
        arch_map = {
            'amd64': 'x86_64',
            'arm64': 'aarch64',
        }
        machine = platform.machine().lower()
        arch = arch_map.get(machine, machine)

    ext = ".exe" if os_name == "windows" else ""
    filename = f"unzstd{ext}"
    url = f"https://github.com/angt/unzstd/releases/latest/download/{arch}-{os_name}-{filename}"
    return url, filename

def get_featcode(os_name=None, arch=None):
    if not os_name:
        os_map = {
            'darwin': 'macos',
        }
        system = platform.system().lower()
        os_name = os_map.get(system, system)

    if not arch:
        arch_map = {
            'amd64': 'x86_64',
            'arm64': 'aarch64',
        }
        machine = platform.machine().lower()
        arch = arch_map.get(machine, machine)

    ext = ".exe" if os_name == "windows" else ""
    filename = f"featcode{ext}"
    url = f"https://github.com/angt/featcode/releases/download/v10/{arch}-{os_name}-{filename}"
    return url, filename

ROCM_ARCHS = [
    "906", "90a", "942", "950",
    "1030", "1031", "1032",
    "1011", # aws
    "1100", "1101", "1102", "1103",
    "1150", "1151", "1152", "1153",
    "1200", "1201"
]
CUDA_ARCHS = {
    "75":  "128",
    "80":  "128",
    "86":  "128",
    "89":  "128",
    "90":  "128",
    "100": "128",
    "120": "128",
    "121": "129",
}
CUDA_MAJORS = ["12", "13"]

METAL_ARCHS = {
    "m1":  ("13.3", False, None),
    "m2":  ("13.3", False, None),
    "m3":  ("14.0", True,  None),
    "m4":  ("15.0", True,  None),
    "m5":  ("16.0", True,  "m4"),
    "a18": ("15.0", True,  None),
}

CPU_ARCHS = {}

def generate_features(features, implications):
    rules = [(1 << features.index(c), 1 << features.index(p)) for c, p in implications]
    ret = []
    for i in range(1 << len(features)):
        if all(not (i & child) or (i & parent) for child, parent in rules):
            ret.append([f for k, f in enumerate(features) if (i >> k) & 1])
    return ret

def generate_aarch64_features():
    features = [
        'fp16',
        'dotprod',
        'i8mm',
        'sve',
        'sve2', # only to detect v9a
        'sme',
    ]
    implications = [
        # strict
        ('sve',  'fp16'   ),
        ('sve2', 'sve'    ),
        ('sme',  'fp16'   ),
        # observed so far
        ('i8mm', 'dotprod'),
        ('sve2', 'dotprod'),
        ('sme',  'i8mm'   ),
    ]
    return generate_features(features, implications)

def generate_x86_64_features():
    features = [
        'avx',
        'f16c',
        'fma',
        'avx2',
        'bmi2',
        'avxvnni',
        'avxvnniint8',
        'avx512f',
        'avx512vl',
        'avx512bw',
        'avx512dq',
        'avx512cd',
        'avx512vnni',
        'avx512vbmi',
        'avx512bf16',
        'avx512fp16',
        'amx-tile',
        'amx-int8',
        'amx-bf16',
    ]
    implications = [
        # strict
        ('f16c',        'avx'       ),
        ('fma',         'avx'       ),
        ('avx2',        'avx'       ),
        ('avxvnni',     'avx2'      ),
        ('avxvnniint8', 'avx2'      ),
        ('avx512f',     'f16c'      ),
        ('avx512f',     'fma'       ),
        ('avx512f',     'avx2'      ),
        ('avx512vl',    'avx512f'   ),
        ('avx512bw',    'avx512f'   ),
        ('avx512dq',    'avx512f'   ),
        ('avx512cd',    'avx512f'   ),
        ('avx512vnni',  'avx512f'   ),
        ('avx512vbmi',  'avx512bw'  ),
        ('avx512bf16',  'avx512bw'  ),
        ('avx512fp16',  'avx512bw'  ),
        ('amx-int8',    'amx-tile'  ),
        ('amx-bf16',    'amx-tile'  ),
        # observed so far
        ('fma',         'f16c'      ),
        ('avx2',        'bmi2'      ),
        ('bmi2',        'fma'       ),
        ('bmi2',        'avx2'      ),
        ('avxvnniint8', 'avxvnni'   ),
        ('avx512f',     'avx512cd'  ),
        ('avx512vl',    'avx512dq'  ),
        ('avx512bw',    'avx512dq'  ),
        ('avx512dq',    'avx512vl'  ),
        ('avx512dq',    'avx512bw'  ),
        ('avx512vnni',  'avx512dq'  ),
        ('avx512bf16',  'avx512vnni'),
        ('avx512fp16',  'avxvnni'   ),  # instead of ('avx512fp16', 'amx-bf16')
        ('avx512fp16',  'avx512bf16'),  # see https://github.com/ggml-org/llama-install.sh/issues/92
        ('avx512fp16',  'avx512vbmi'),  #
        ('amx-tile',    'amx-bf16'  ),
        ('amx-bf16',    'avxvnni'   ),
        ('amx-bf16',    'avx512vbmi'),
        ('amx-bf16',    'avx512bf16'),
        ('amx-bf16',    'avx512fp16'),
        ('amx-bf16',    'amx-int8'  ),
    ]
    return generate_features(features, implications)

def select_min_aarch64_arch(features):
    march = {
        'sve2':    'generic+v9a',
        'sme':     'generic+v8_7a', # only because of apple-m4
        'i8mm':    'generic+v8_4a',
        'sve':     'generic+v8_2a',
        'dotprod': 'generic+v8_2a',
        'fp16':    'generic+v8_2a',
    }
    return next((march[f] for f in march if f in set(features)), 'generic')

def select_min_x86_64_arch(features):
    march = {
        'amx-bf16':    'x86_64_v4',
        'amx-int8':    'x86_64_v4',
        'amx-tile':    'x86_64_v4',
        'avx512bf16':  'x86_64_v4',
        'avx512vbmi':  'x86_64_v4',
        'avx512vnni':  'x86_64_v4',
        'avx512bw':    'x86_64_v4',
        'avx512dq':    'x86_64_v4',
        'avx512vl':    'x86_64_v4',
        'avx512cd':    'x86_64_v3',
        'avx512f':     'x86_64_v3',
        'avxvnniint8': 'x86_64_v3',
        'avxvnni':     'x86_64_v3',
        'bmi2':        'x86_64_v3',
        'avx2':        'x86_64_v3',
        'fma':         'x86_64_v2',
        'f16c':        'x86_64_v2',
        'avx':         'x86_64_v2',
    }
    return next((march[f] for f in march if f in set(features)), 'x86_64')

def download_featcode():
    url, filename = get_featcode()
    path = Path(filename)
    urllib.request.urlretrieve(url, path)
    path.chmod(path.stat().st_mode | stat.S_IEXEC)

def featcode(arch, features):
    _, filename = get_featcode()
    result = subprocess.run(
        [Path.cwd() / filename, '+'] + ['+' + feat for feat in features],
        env={**os.environ, 'FEATCODE_ARCH': arch},
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()

def generate_aarch64_flags(features):
    mcpu = '+'.join([
        select_min_aarch64_arch(features),
        *('fullfp16' if f == 'fp16' else f for f in features)
    ])
    return f"-mcpu={mcpu}"

def generate_x86_64_flags(features):
    arch = select_min_x86_64_arch(features)
    flags = ' '.join([
        f"-march={arch}",
        *(f"-m{feat}" for feat in features),
    ])
    return flags

def generate_cpu_archs():
    CPU_ARCHS['aarch64'] = {}

    for features in generate_aarch64_features():
        name = featcode('aarch64', features)
        flags = generate_aarch64_flags(features)
        CPU_ARCHS['aarch64'][name] = flags

    CPU_ARCHS['x86_64'] = {}

    for features in generate_x86_64_features():
        name = featcode('x86_64', features)
        flags = generate_x86_64_flags(features)
        CPU_ARCHS['x86_64'][name] = flags

def generate_presets(os_name, arch, backend, toolchain, configs):
    configure = []
    build = []
    workflow = []

    for config_name, config_cache in configs:
        name_seg = config_name.replace("/", "-")
        preset_name = f"{arch}-{os_name}-{backend}-{name_seg}"
        preset_path = f"{arch}/{os_name}/{backend}/{config_name}"
        configure.append({
            "name": preset_name,
            "binaryDir": "build/${presetName}",
            "cacheVariables": {
                "LLAMA_INSTALL_DIR": f"${{sourceDir}}/output/{preset_path}",
                "LLAMA_INSTALL_OS": os_name,
                "LLAMA_INSTALL_ARCH": arch,
            } | config_cache,
            "toolchainFile": toolchain,
            "generator": "Ninja",
        })
        build.append({
            "name": preset_name,
            "configurePreset": preset_name,
            "jobs": 0,
            "targets": ["llama-install"],
        })
        workflow.append({
            "name": preset_name,
            "steps": [
                {"type": "configure", "name": preset_name},
                {"type": "build", "name": preset_name}
            ]
        })

    return configure, build, workflow

def generate_cpu_presets(os_name, arch):
    configs = []
    for name, flags in CPU_ARCHS[arch].items():
        cache = {
            "LLAMA_INSTALL_FLAGS": flags,
        }
        configs.append((name, cache))

    return generate_presets(
        os_name   = os_name,
        arch      = arch,
        backend   = 'cpu',
        toolchain = 'toolchains/cross.cmake',
        configs   = configs,
    )

def rocwmma(arch):
    return arch.startswith(('11', '12')) or (arch.startswith('9') and arch not in {'900', '906'})

def generate_x86_64_linux_rocm_presets():
    configs = []
    for arch in ROCM_ARCHS:
        name = f"gfx{arch}"
        cache = {
            "GGML_HIP": "ON",
            "GGML_HIP_ROCWMMA_FATTN": "ON" if rocwmma(arch) else "OFF",
            "CMAKE_HIP_ARCHITECTURES": name,
        }
        configs.append((name, cache))

    return generate_presets(
        os_name   = 'linux',
        arch      = 'x86_64',
        backend   = 'rocm',
        toolchain = 'toolchains/rocm.cmake',
        configs   = configs,
    )

def generate_x86_64_linux_rocm_probe_preset():
    configs = []
    name = "probe"
    cache = {
        "LLAMA_INSTALL_PROBE": "rocm",
    }
    configs.append((name, cache))

    return generate_presets(
        os_name   = 'linux',
        arch      = 'x86_64',
        backend   = 'rocm',
        toolchain = 'toolchains/rocm.cmake',
        configs   = configs,
    )

def generate_linux_cuda_presets(arch):
    configs = []
    last_arch = next(reversed(CUDA_ARCHS))
    for cuda_arch in list(CUDA_ARCHS):
        cache = {
            "GGML_CUDA": "ON",
            "GGML_STATIC": "ON",
            "CMAKE_CUDA_ARCHITECTURES": cuda_arch if cuda_arch == last_arch else f"{cuda_arch}-real",
            "CMAKE_CUDA_COMPILER": "${sourceDir}/deps/cuda/bin/nvcc",
            "CMAKE_CUDA_FLAGS": "-isystem ${sourceDir}/deps/cuda/include",
        }
        configs.append((cuda_arch, cache))

    return generate_presets(
        os_name   = 'linux',
        arch      = arch,
        backend   = 'cuda',
        toolchain = 'toolchains/base.cmake',
        configs   = configs,
    )

def generate_linux_cuda_probe_preset(arch):
    configs = []
    name = "probe"
    cache = {
        "LLAMA_INSTALL_PROBE": "cuda",
        "LLAMA_INSTALL_PROBE_ARCHS": ",".join(CUDA_ARCHS),
        "LLAMA_INSTALL_PROBE_VERSIONS": ",".join(CUDA_ARCHS.values()),
        "CMAKE_CUDA_ARCHITECTURES": ";".join(CUDA_ARCHS), # useless
        "CMAKE_CUDA_COMPILER": "${sourceDir}/deps/cuda/bin/nvcc",
        "CMAKE_CUDA_FLAGS": "-isystem ${sourceDir}/deps/cuda/include",
    }
    configs.append((name, cache))

    return generate_presets(
        os_name   = 'linux',
        arch      = arch,
        backend   = 'cuda',
        toolchain = 'toolchains/base.cmake',
        configs   = configs,
    )

def generate_windows_cuda_presets(arch):
    configs = []
    last_arch = next(reversed(CUDA_ARCHS))
    for major in CUDA_MAJORS:
        for cuda_arch in list(CUDA_ARCHS):
            config_name = f"{major}/{cuda_arch}"
            cache = {
                "GGML_CUDA": "ON",
                "GGML_STATIC": "ON",
                "CMAKE_CUDA_ARCHITECTURES": cuda_arch if cuda_arch == last_arch else f"{cuda_arch}-real",
                "CMAKE_CUDA_COMPILER": "${sourceDir}/deps/cuda/bin/nvcc.exe",
                "CMAKE_CUDA_FLAGS": "-diag-suppress 221 -isystem ${sourceDir}/deps/cuda/include",
            }
            configs.append((config_name, cache))

    return generate_presets(
        os_name   = 'windows',
        arch      = arch,
        backend   = 'cuda',
        toolchain = 'toolchains/base.cmake',
        configs   = configs,
    )

def generate_windows_cuda_probe_preset(arch):
    configs = []
    name = "probe"
    cache = {
        "LLAMA_INSTALL_PROBE": "cuda",
        "LLAMA_INSTALL_PROBE_ARCHS": ",".join(CUDA_ARCHS),
        "LLAMA_INSTALL_PROBE_VERSIONS": ",".join(CUDA_ARCHS.values()),
        "CMAKE_CUDA_ARCHITECTURES": ";".join(CUDA_ARCHS), # useless
        "CMAKE_CUDA_COMPILER": "${sourceDir}/deps/cuda/bin/nvcc.exe",
        "CMAKE_CUDA_FLAGS": "-diag-suppress 221 -isystem ${sourceDir}/deps/cuda/include",
    }
    configs.append((name, cache))

    return generate_presets(
        os_name   = 'windows',
        arch      = arch,
        backend   = 'cuda',
        toolchain = 'toolchains/base.cmake',
        configs   = configs,
    )

def generate_vulkan_presets(os_name, arch):
    configs = []
    for name, flags in CPU_ARCHS[arch].items():
        cache = {
            "LLAMA_INSTALL_FLAGS": flags,
            "GGML_VULKAN": "ON",
        }
        configs.append((name, cache))

    return generate_presets(
        os_name   = os_name,
        arch      = arch,
        backend   = 'vulkan',
        toolchain = 'toolchains/vulkan.cmake',
        configs   = configs,
    )

def generate_vulkan_probe_preset(os_name, arch):
    configs = []
    name = "probe"
    cache = {
        "LLAMA_INSTALL_PROBE": "vulkan",
    }
    configs.append((name, cache))

    return generate_presets(
        os_name   = os_name,
        arch      = arch,
        backend   = 'vulkan',
        toolchain = 'toolchains/vulkan.cmake',
        configs   = configs,
    )

def generate_metal_presets():
    configs = []
    for name, (osx, bf16, mcpu_override) in METAL_ARCHS.items():
        mcpu = f"apple-{mcpu_override or name}"
        cache = {
            "GGML_METAL": "ON",
            "GGML_METAL_EMBED_LIBRARY": "ON",
            "GGML_METAL_USE_BF16": "ON" if bf16 else "OFF",
            "CMAKE_OSX_ARCHITECTURES": "arm64",
            "CMAKE_OSX_DEPLOYMENT_TARGET": osx,
            "LLAMA_INSTALL_FLAGS": f"-mcpu={mcpu}"
        }
        configs.append((name, cache))

    return generate_presets(
        os_name   = 'macos',
        arch      = 'aarch64',
        backend   = 'metal',
        toolchain = 'toolchains/base.cmake',
        configs   = configs
    )

def format_x86_64_features(flags):
    feats = []
    arch = ""
    parts = flags.split()
    for p in parts:
        if p.startswith("-march="):
            arch = p.replace("-march=", "")
        elif p.startswith("-m"):
            feats.append(p[2:])
    return arch, feats

def format_aarch64_features(flags):
    feats = []
    arch = ""
    parts = flags.replace("-mcpu=", "").split("+")
    arch_map = {
        "v8_2a":   "ARMv8.2-a",
        "v8_4a":   "ARMv8.4-a",
        "v8_7a":   "ARMv8.7-a",
        "v9a":     "ARMv9-a",
        "generic": "ARMv8.0-a"
    }
    for p in parts:
        if p in arch_map:
            arch = arch_map[p]
        else:
            feats.append(p)
    return arch, feats

def make_table(cols, rows):
    if not rows:
        return []

    widths = [max(map(len, x)) for x in zip(*([cols] + rows))]
    header = [[c.ljust(w) for c, w in zip(cols, widths)], ["-" * w for w in widths]]
    rows   = [[r.ljust(w) for r, w in zip(row, widths)] for row in rows]

    return "\n".join([
        "| " + " | ".join(line) + " |"
        for line in header + rows
    ])

def generate_report():
    return "\n\n".join([
        "# Build Presets Reference",
        "## CPU",
        "### AArch64 (ARM64)",
        make_table(["Suffix", "Architecture", "Features"], [
            [f"`{code}`", f"**{arch}**", " ".join(f"`{f}`" for f in feats) or "-"]
            for code, flags in CPU_ARCHS['aarch64'].items()
            for arch, feats in [format_aarch64_features(flags)]
        ]),
        "### x86_64 (Intel/AMD)",
        make_table(["Suffix", "Architecture", "Features"], [
            [f"`{code}`", f"**{arch}**", " ".join(f"`{f}`" for f in feats) or "-"]
            for code, flags in CPU_ARCHS['x86_64'].items()
            for arch, feats in [format_x86_64_features(flags)]
        ]),
        "## GPU",
        "### CUDA (NVIDIA)",
        make_table(["Architecture"], [
            [f"`{a}`"] for a in CUDA_ARCHS
        ]),
        "### ROCm (AMD)",
        make_table(["Architecture", "Features"], [
            [f"`gfx{arch}`", "ROCWMMA+FlashAttn" if rocwmma(arch) else "-"]
            for arch in ROCM_ARCHS
        ]),
        "### Metal (Apple Silicon)",
        make_table(["Suffix", "Architecture", "Features"], [
            [f"`{cpu}`", f"Apple {cpu.upper()}", "BF16" if bf16 else "-"]
            for cpu, (_, bf16, _) in METAL_ARCHS.items()
        ]),
    ])

def generate_artefacts(cpu_os_archs):
    artefacts = []
    for os_name, arch in cpu_os_archs:
        url, filename = get_featcode(os_name, arch)
        artefacts.append({
            "src": url,
            "dst": f"output/{arch}/{os_name}/{filename}"
        })
    for os_name, arch in cpu_os_archs:
        url, filename = get_unzstd(os_name, arch)
        artefacts.append({
            "src": url,
            "dst": f"output/{arch}/{os_name}/{filename}"
        })
    return artefacts

def cuda_build_code(major, arch):
    return str(max(int(major + "0"), int(CUDA_ARCHS[arch])))

def preset_cuda_code(preset_name):
    parts = preset_name.split("-")
    if len(parts) >= 5 and parts[3] != "probe":
        return cuda_build_code(parts[3], parts[4])
    arch = parts[-1]
    if arch in CUDA_ARCHS:
        return CUDA_ARCHS[arch]
    return max(CUDA_ARCHS.values())  # probe

def generate_jobs(workflow_presets):
    groups = defaultdict(list)
    for preset in workflow_presets:
        parts = preset["name"].split("-")
        group = f"{parts[0]}-{parts[1]}-{parts[2]}"
        groups[group].append(preset["name"])

    probe_code = max(CUDA_ARCHS.values())

    jobs = {}
    for group, filters in groups.items():
        _, os_name, backend = group.split("-")
        matrix = {"filter": filters}
        extra = {}
        if backend == "cuda":
            matrix = {"include": [
                {"filter": f, "cuda_code": preset_cuda_code(f)}
                for f in filters
            ]}
            extra = {"cuda_code": "${{ matrix.cuda_code }}"}
        workflow_name = f"{os_name}-{backend}" if backend == "cuda" else backend
        jobs[group] = {
            "name": "${{ matrix.filter }}",
            "needs": ["init"],
            "strategy": {
                "fail-fast": False,
                "matrix": matrix
            },
            "uses": f"./.github/workflows/build-any-{workflow_name}.yml",
            "with": {
                "filter": "${{ matrix.filter }}",
                **extra,
                "deploy": True,
                "llamacpp_repo": "${{ inputs.llamacpp_repo }}",
                "llamacpp_version": "${{ needs.init.outputs.llamacpp_version }}",
                "boringssl_version": "${{ needs.init.outputs.boringssl_version }}",
            },
            "secrets": "inherit",
        }

    return jobs

def main():
    download_featcode()
    generate_cpu_archs()

    cpu_os_archs = [
        (os_name, arch)
        for os_name in ['linux', 'windows', 'freebsd']
        for arch in ['aarch64', 'x86_64']
    ]

    presets = [
        *[generate_cpu_presets(os_name, arch) for os_name, arch in cpu_os_archs],
        *[preset
          for os_name in ['linux', 'windows']
          for arch in ['aarch64', 'x86_64']
          for preset in (generate_vulkan_presets(os_name, arch),
                         generate_vulkan_probe_preset(os_name, arch))
        ],
        *[preset
          for arch in ['aarch64', 'x86_64']
          for preset in (generate_linux_cuda_presets(arch),
                         generate_linux_cuda_probe_preset(arch))
        ],
        generate_windows_cuda_presets('x86_64'),
        generate_windows_cuda_probe_preset('x86_64'),
        generate_x86_64_linux_rocm_presets(),
        generate_x86_64_linux_rocm_probe_preset(),
        generate_metal_presets(),
    ]
    data = {
        "version": 7,
        "configurePresets": [],
        "buildPresets": [],
        "workflowPresets": []
    }
    for configure, build, workflow in presets:
        data["configurePresets"].extend(configure)
        data["buildPresets"].extend(build)
        data["workflowPresets"].extend(workflow)

    with open("CMakePresets.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    artefacts = generate_artefacts(sorted({
        (p["cacheVariables"]["LLAMA_INSTALL_OS"], p["cacheVariables"]["LLAMA_INSTALL_ARCH"])
        for p in data["configurePresets"]
    }))

    with open("artefacts.json", "w", encoding="utf-8") as f:
        json.dump(artefacts, f, indent=2)

    report = generate_report()

    with open("PRESETS.md", "w", encoding="utf-8") as f:
        f.write(report)

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.default_flow_style = False
    yaml.width = 4096
    yaml.indent(mapping=2, sequence=4, offset=2)

    release_path = ".github/workflows/release.yml"

    with open(release_path, "r", encoding="utf-8") as f:
        release = yaml.load(f)

    release_job = release["jobs"]["release"]
    build_jobs = generate_jobs(data.get("workflowPresets", []))
    release_job["needs"] = ["init"] + list(build_jobs.keys())

    release["jobs"] = {
        **release["jobs"],
        **build_jobs,
        "release": release_job,
    }
    with open(release_path, "w", encoding="utf-8") as f:
        yaml.dump(release, f)

if __name__ == "__main__":
    main()
