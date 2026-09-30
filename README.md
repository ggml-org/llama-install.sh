# llama-install.sh

Build and install scripts for [llama.app](https://llama.app)

This repository provides `install.sh` and `install.ps1` scripts that download and set up a prebuilt `llama` binary for your system.
It automatically detects your OS, architecture, and GPU capabilities, so you can start using `llama.cpp` in seconds.

## Features

- Supported architectures: `x86_64`, `aarch64`.
- Supported OS: `Linux`, `macOS`, `FreeBSD`, `Windows`.
- **Automatic detection** for **CPU acceleration**.
- **Automatic detection** for **GPU acceleration**: `CUDA`, `ROCm`, `SYCL`, `Vulkan`, `Metal`.
- Builds are kept as **lightweight** as possible without compromising performance.

See the full list of supported hardware and build configurations in [PRESETS.md](PRESETS.md).
Check [REQUIREMENTS.md](REQUIREMENTS.md) for the detailed requirements, including minimum OS versions and runtime library dependencies.

## Installation & Usage

### POSIX systems

Run the following command in your terminal:

    curl https://llama.app/install.sh | sh

Launch the server:

    ~/.llama-app/llama serve -hf unsloth/Qwen3-4B-GGUF:Q4_0

In some scenarios, you may want to skip detection for specific backends.
You can do this by setting environment variables before piping to `sh`:

    curl https://llama.app/install.sh | SKIP_CUDA=1 sh

Available options: `SKIP_CUDA=1`, `SKIP_ROCM=1`, `SKIP_SYCL=1`, `SKIP_VULKAN=1`.

### Windows

Run the following command in `PowerShell`:

    irm https://llama.app/install.ps1 | iex

Launch the server:

    llama.exe serve -hf unsloth/Qwen3-4B-GGUF:Q4_0

## Enjoy!

Once the server is running with your chosen model, simply open your browser and navigate to:

**http://127.0.0.1:8080**

---
If it doesn't work on your system, please [create an issue](https://github.com/ggml-org/llama-install.sh/issues/new).
