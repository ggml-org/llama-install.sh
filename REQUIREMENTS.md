# Supported Systems

| Name    | Arch      | Backend      | Version    | Libraries                                              |
| ------- | --------- | ------------ | ---------- | ------------------------------------------------------ |
| freebsd | `aarch64` | `cpu`        | FBSD 1.7   | -                                                      |
| freebsd | `x86_64`  | `cpu`        | FBSD 1.7   | -                                                      |
| linux   | `aarch64` | `cpu`        | -          | -                                                      |
| linux   | `aarch64` | `cuda`       | GLIBC 2.35 | `libcuda.so.1`                                         |
| linux   | `aarch64` | `vulkan`     | GLIBC 2.29 | `libvulkan.so.1`                                       |
| linux   | `x86_64`  | `cpu`        | -          | -                                                      |
| linux   | `x86_64`  | `cuda`       | GLIBC 2.35 | `libcuda.so.1`                                         |
| linux   | `x86_64`  | `rocm`       | GLIBC 2.35 | `libamdhip64.so.7` `libhipblas.so.3` `librocblas.so.5` |
| linux   | `x86_64`  | `vulkan`     | GLIBC 2.29 | `libvulkan.so.1`                                       |
| macos   | `aarch64` | `metal/a18`  | macOS 15.0 | -                                                      |
| macos   | `aarch64` | `metal/m1`   | macOS 13.3 | -                                                      |
| macos   | `aarch64` | `metal/m2`   | macOS 13.3 | -                                                      |
| macos   | `aarch64` | `metal/m3`   | macOS 14.0 | -                                                      |
| macos   | `aarch64` | `metal/m4`   | macOS 15.0 | -                                                      |
| macos   | `aarch64` | `metal/m5`   | macOS 26.0 | -                                                      |
| windows | `aarch64` | `cpu`        | Windows 10 | -                                                      |
| windows | `aarch64` | `cuda/13`    | Windows 10 | `cublas64_13.dll`                                      |
| windows | `aarch64` | `cuda/probe` | Windows 10 | -                                                      |
| windows | `aarch64` | `vulkan`     | Windows 10 | `vulkan-1.dll`                                         |
| windows | `x86_64`  | `cpu`        | Windows 8  | -                                                      |
| windows | `x86_64`  | `cuda/12`    | Windows 8  | `cublas64_12.dll` `nvcuda.dll`                         |
| windows | `x86_64`  | `cuda/13`    | Windows 8  | `cublas64_13.dll`                                      |
| windows | `x86_64`  | `cuda/probe` | Windows 7  | `nvcuda.dll`                                           |
| windows | `x86_64`  | `vulkan`     | Windows 8  | `vulkan-1.dll`                                         |
