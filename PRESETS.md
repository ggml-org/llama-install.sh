# Build Presets Reference

## CPU

### AArch64 (ARM64)

| Suffix | Architecture  | Features                                       |
| ------ | ------------- | ---------------------------------------------- |
| `kk`   | **ARMv8.0-a** | -                                              |
| `lk`   | **ARMv8.2-a** | `fullfp16`                                     |
| `mk`   | **ARMv8.2-a** | `dotprod`                                      |
| `nk`   | **ARMv8.2-a** | `fullfp16` `dotprod`                           |
| `qk`   | **ARMv8.4-a** | `dotprod` `i8mm`                               |
| `rk`   | **ARMv8.4-a** | `fullfp16` `dotprod` `i8mm`                    |
| `sk`   | **ARMv8.2-a** | `fullfp16` `sve`                               |
| `uk`   | **ARMv8.2-a** | `fullfp16` `dotprod` `sve`                     |
| `yk`   | **ARMv8.4-a** | `fullfp16` `dotprod` `i8mm` `sve`              |
| `ml`   | **ARMv9-a**   | `fullfp16` `dotprod` `sve` `sve2`              |
| `ql`   | **ARMv9-a**   | `fullfp16` `dotprod` `i8mm` `sve` `sve2`       |
| `qm`   | **ARMv8.7-a** | `fullfp16` `dotprod` `i8mm` `sme`              |
| `ym`   | **ARMv8.7-a** | `fullfp16` `dotprod` `i8mm` `sve` `sme`        |
| `qn`   | **ARMv9-a**   | `fullfp16` `dotprod` `i8mm` `sve` `sve2` `sme` |

### x86_64 (Intel/AMD)

| Suffix  | Architecture  | Features                                                                                                                                                                                            |
| ------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `kkkkk` | **x86_64**    | -                                                                                                                                                                                                   |
| `lkkkk` | **x86_64_v2** | `avx`                                                                                                                                                                                               |
| `mkkkk` | **x86_64_v2** | `avx` `f16c`                                                                                                                                                                                        |
| `qkkkk` | **x86_64_v2** | `avx` `f16c` `fma`                                                                                                                                                                                  |
| `ylkkk` | **x86_64_v3** | `avx` `f16c` `fma` `avx2` `bmi2`                                                                                                                                                                    |
| `qnkkk` | **x86_64_v3** | `avx` `f16c` `fma` `avx2` `bmi2` `avxvnni`                                                                                                                                                          |
| `qrkkk` | **x86_64_v3** | `avx` `f16c` `fma` `avx2` `bmi2` `avxvnni` `avxvnniint8`                                                                                                                                            |
| `klokk` | **x86_64_v3** | `avx` `f16c` `fma` `avx2` `bmi2` `avx512f` `avx512cd`                                                                                                                                               |
| `knokk` | **x86_64_v3** | `avx` `f16c` `fma` `avx2` `bmi2` `avxvnni` `avx512f` `avx512cd`                                                                                                                                     |
| `krokk` | **x86_64_v3** | `avx` `f16c` `fma` `avx2` `bmi2` `avxvnni` `avxvnniint8` `avx512f` `avx512cd`                                                                                                                       |
| `klzkk` | **x86_64_v4** | `avx` `f16c` `fma` `avx2` `bmi2` `avx512f` `avx512vl` `avx512bw` `avx512dq` `avx512cd`                                                                                                              |
| `knzkk` | **x86_64_v4** | `avx` `f16c` `fma` `avx2` `bmi2` `avxvnni` `avx512f` `avx512vl` `avx512bw` `avx512dq` `avx512cd`                                                                                                    |
| `krzkk` | **x86_64_v4** | `avx` `f16c` `fma` `avx2` `bmi2` `avxvnni` `avxvnniint8` `avx512f` `avx512vl` `avx512bw` `avx512dq` `avx512cd`                                                                                      |
| `klzlk` | **x86_64_v4** | `avx` `f16c` `fma` `avx2` `bmi2` `avx512f` `avx512vl` `avx512bw` `avx512dq` `avx512cd` `avx512vnni`                                                                                                 |
| `knzlk` | **x86_64_v4** | `avx` `f16c` `fma` `avx2` `bmi2` `avxvnni` `avx512f` `avx512vl` `avx512bw` `avx512dq` `avx512cd` `avx512vnni`                                                                                       |
| `krzlk` | **x86_64_v4** | `avx` `f16c` `fma` `avx2` `bmi2` `avxvnni` `avxvnniint8` `avx512f` `avx512vl` `avx512bw` `avx512dq` `avx512cd` `avx512vnni`                                                                         |
| `klxmk` | **x86_64_v4** | `avx` `f16c` `fma` `avx2` `bmi2` `avx512f` `avx512vl` `avx512bw` `avx512dq` `avx512cd` `avx512vbmi`                                                                                                 |
| `knxmk` | **x86_64_v4** | `avx` `f16c` `fma` `avx2` `bmi2` `avxvnni` `avx512f` `avx512vl` `avx512bw` `avx512dq` `avx512cd` `avx512vbmi`                                                                                       |
| `krxmk` | **x86_64_v4** | `avx` `f16c` `fma` `avx2` `bmi2` `avxvnni` `avxvnniint8` `avx512f` `avx512vl` `avx512bw` `avx512dq` `avx512cd` `avx512vbmi`                                                                         |
| `klxnk` | **x86_64_v4** | `avx` `f16c` `fma` `avx2` `bmi2` `avx512f` `avx512vl` `avx512bw` `avx512dq` `avx512cd` `avx512vnni` `avx512vbmi`                                                                                    |
| `knxnk` | **x86_64_v4** | `avx` `f16c` `fma` `avx2` `bmi2` `avxvnni` `avx512f` `avx512vl` `avx512bw` `avx512dq` `avx512cd` `avx512vnni` `avx512vbmi`                                                                          |
| `krxnk` | **x86_64_v4** | `avx` `f16c` `fma` `avx2` `bmi2` `avxvnni` `avxvnniint8` `avx512f` `avx512vl` `avx512bw` `avx512dq` `avx512cd` `avx512vnni` `avx512vbmi`                                                            |
| `klxpk` | **x86_64_v4** | `avx` `f16c` `fma` `avx2` `bmi2` `avx512f` `avx512vl` `avx512bw` `avx512dq` `avx512cd` `avx512vnni` `avx512bf16`                                                                                    |
| `knxpk` | **x86_64_v4** | `avx` `f16c` `fma` `avx2` `bmi2` `avxvnni` `avx512f` `avx512vl` `avx512bw` `avx512dq` `avx512cd` `avx512vnni` `avx512bf16`                                                                          |
| `krxpk` | **x86_64_v4** | `avx` `f16c` `fma` `avx2` `bmi2` `avxvnni` `avxvnniint8` `avx512f` `avx512vl` `avx512bw` `avx512dq` `avx512cd` `avx512vnni` `avx512bf16`                                                            |
| `klxrk` | **x86_64_v4** | `avx` `f16c` `fma` `avx2` `bmi2` `avx512f` `avx512vl` `avx512bw` `avx512dq` `avx512cd` `avx512vnni` `avx512vbmi` `avx512bf16`                                                                       |
| `knxrk` | **x86_64_v4** | `avx` `f16c` `fma` `avx2` `bmi2` `avxvnni` `avx512f` `avx512vl` `avx512bw` `avx512dq` `avx512cd` `avx512vnni` `avx512vbmi` `avx512bf16`                                                             |
| `krxrk` | **x86_64_v4** | `avx` `f16c` `fma` `avx2` `bmi2` `avxvnni` `avxvnniint8` `avx512f` `avx512vl` `avx512bw` `avx512dq` `avx512cd` `avx512vnni` `avx512vbmi` `avx512bf16`                                               |
| `knxzk` | **x86_64_v4** | `avx` `f16c` `fma` `avx2` `bmi2` `avxvnni` `avx512f` `avx512vl` `avx512bw` `avx512dq` `avx512cd` `avx512vnni` `avx512vbmi` `avx512bf16` `avx512fp16`                                                |
| `krxzk` | **x86_64_v4** | `avx` `f16c` `fma` `avx2` `bmi2` `avxvnni` `avxvnniint8` `avx512f` `avx512vl` `avx512bw` `avx512dq` `avx512cd` `avx512vnni` `avx512vbmi` `avx512bf16` `avx512fp16`                                  |
| `knxzq` | **x86_64_v4** | `avx` `f16c` `fma` `avx2` `bmi2` `avxvnni` `avx512f` `avx512vl` `avx512bw` `avx512dq` `avx512cd` `avx512vnni` `avx512vbmi` `avx512bf16` `avx512fp16` `amx-tile` `amx-int8` `amx-bf16`               |
| `krxzq` | **x86_64_v4** | `avx` `f16c` `fma` `avx2` `bmi2` `avxvnni` `avxvnniint8` `avx512f` `avx512vl` `avx512bw` `avx512dq` `avx512cd` `avx512vnni` `avx512vbmi` `avx512bf16` `avx512fp16` `amx-tile` `amx-int8` `amx-bf16` |

## GPU

### CUDA (NVIDIA)

| Architecture |
| ------------ |
| `75`         |
| `80`         |
| `86`         |
| `89`         |
| `90`         |
| `100`        |
| `120`        |
| `121`        |

### ROCm (AMD)

| Architecture | Features          |
| ------------ | ----------------- |
| `gfx906`     | -                 |
| `gfx90a`     | ROCWMMA+FlashAttn |
| `gfx942`     | ROCWMMA+FlashAttn |
| `gfx950`     | ROCWMMA+FlashAttn |
| `gfx1030`    | -                 |
| `gfx1031`    | -                 |
| `gfx1032`    | -                 |
| `gfx1011`    | -                 |
| `gfx1100`    | ROCWMMA+FlashAttn |
| `gfx1101`    | ROCWMMA+FlashAttn |
| `gfx1102`    | ROCWMMA+FlashAttn |
| `gfx1103`    | ROCWMMA+FlashAttn |
| `gfx1150`    | ROCWMMA+FlashAttn |
| `gfx1151`    | ROCWMMA+FlashAttn |
| `gfx1152`    | ROCWMMA+FlashAttn |
| `gfx1153`    | ROCWMMA+FlashAttn |
| `gfx1200`    | ROCWMMA+FlashAttn |
| `gfx1201`    | ROCWMMA+FlashAttn |

### SYCL (Intel)

| Suffix | Features |
| ------ | -------- |
| `fp16` | FP16     |

### Metal (Apple Silicon)

| Suffix | Architecture | Features |
| ------ | ------------ | -------- |
| `m1`   | Apple M1     | -        |
| `m2`   | Apple M2     | -        |
| `m3`   | Apple M3     | BF16     |
| `m4`   | Apple M4     | BF16     |
| `m5`   | Apple M5     | BF16     |
| `a18`  | Apple A18    | BF16     |