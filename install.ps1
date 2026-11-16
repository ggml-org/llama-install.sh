if (!$LLAMA_BUCKET) { $LLAMA_BUCKET = $env:LLAMA_BUCKET }
if (!$LLAMA_BUCKET) { $LLAMA_BUCKET = "ggml-org/install.sh" }
$REPO = "https://huggingface.co/buckets/$LLAMA_BUCKET/resolve"
$WebParams = @{}

if ($env:HF_TOKEN) {
    $WebParams["Headers"] = @{ "Authorization" = "Bearer $env:HF_TOKEN" }
}

function Die {
    param([string[]]$Messages)
    $Messages | % { [Console]::Error.WriteLine($_) }
    exit 111
}

function Download {
    param($FILE, [string[]]$URL)
    if (Test-Path "$DIR\$FILE") {
        return $true
    }
    Write-Host "Downloading $FILE..."
    foreach ($U in $URL) {
        try {
            if ($U -like "*.zst") {
                if (!(Download "unzstd.exe" "$ARCH/windows/unzstd.exe")) { return $false }
                Invoke-RestMethod "$REPO/$LLAMA_VERSION/$U" -OutFile "$DIR\tmp.zst" @WebParams
                Start-Process -FilePath "$DIR\unzstd.exe" -RedirectStandardInput "$DIR\tmp.zst" -RedirectStandardOutput "$DIR\$FILE" -NoNewWindow -Wait
                Remove-Item "$DIR\tmp.zst"
            } else {
                Invoke-RestMethod "$REPO/$LLAMA_VERSION/$U" -OutFile "$DIR\$FILE" @WebParams
            }
            if (Test-Path "$DIR\$FILE") { return $true }
        } catch {
            if ($U -eq $URL[-1]) { [Console]::Error.WriteLine("Failed to download") }
        }
    }
    return $false
}

function ProbeCUDA {
    if ($env:SKIP_CUDA) { return }
    "Probing CUDA..."
    if (!(Download "cuda-probe.exe" "$ARCH/windows/cuda/probe/probe.exe.zst")) { return }
    $CONFIG = & "$DIR\cuda-probe.exe" 2>$null
    if ($LASTEXITCODE -eq 5) {
        "NVIDIA GPU detected, but the CUDA Toolkit is not installed."
        "To enable CUDA acceleration, install it from:"
        ""
        "  https://developer.nvidia.com/cuda-downloads"
        ""
        "or run:"
        ""
        "  winget install Nvidia.CUDA"
        ""
        return
    }
    if ($LASTEXITCODE) { return }
    "Found: $CONFIG"
    $parts  = -split $CONFIG
    $CONFIG = $parts[0]
    $MAJOR  = $parts[1]
    Download "llama.exe" "$ARCH/windows/cuda/$MAJOR/$CONFIG/llama-app.exe.zst" | Out-Null
}

function ProbeROCm {
    if ($env:SKIP_ROCM) { return }
    "Probing ROCm..."
    if (!(Download "rocm-probe.exe" "$ARCH/windows/rocm/probe/probe.exe.zst")) { return }
    $CONFIG = & "$DIR\rocm-probe.exe" 2>$null
    if ($LASTEXITCODE -eq 5) {
        "AMD GPU detected, but the HIP SDK is not installed."
        "To enable ROCm acceleration, install it from:"
        ""
        "  https://rocm.docs.amd.com/projects/install-on-windows/en/latest/install/install.html"
        ""
        return
    }
    if ($LASTEXITCODE) { return }
    "Found: $CONFIG"
    Download "llama.exe" "$ARCH/windows/rocm/$CONFIG/llama-app.exe.zst" | Out-Null
}

function ProbeVulkan {
    if ($env:SKIP_VULKAN) { return }
    "Probing Vulkan..."
    if (!(Download "vulkan-probe.exe" @("$ARCH/windows/vulkan/probe/probe.exe.zst", "$ARCH/windows/vulkan/probe/probe.zst"))) { return }
    if (!(Download "featcode.exe" "$ARCH/windows/featcode.exe")) { return }
    & "$DIR\vulkan-probe.exe" 2>$null
    if ($LASTEXITCODE) { return }
    $CONFIG = & "$DIR\featcode.exe" 2>$null
    & "$DIR\featcode.exe" $CONFIG 2>$null | % { "Found: $_" }
    Download "llama.exe" @("$ARCH/windows/vulkan/$CONFIG/llama-app.exe.zst", "$ARCH/windows/vulkan/$CONFIG/llama-app.zst") | Out-Null
}

function ProbeCPU {
    "Probing CPU..."
    if (!(Download "featcode.exe" "$ARCH/windows/featcode.exe")) { return }
    $CONFIG = & "$DIR\featcode.exe" 2>$null
    & "$DIR\featcode.exe" $CONFIG 2>$null | % { "Found: $_" }
    Download "llama.exe" @("$ARCH/windows/cpu/$CONFIG/llama-app.exe.zst", "$ARCH/windows/cpu/$CONFIG/llama-app.zst") | Out-Null
}

function Main {
    switch ($env:PROCESSOR_ARCHITECTURE) {
        "ARM64" { $ARCH = "aarch64" }
        "AMD64" { $ARCH = "x86_64"  }
        default { Die "Arch not supported" }
    }

    if (!$LLAMA_VERSION) { $LLAMA_VERSION = $env:LLAMA_VERSION }
    if (!$LLAMA_VERSION) { $LLAMA_VERSION = Invoke-RestMethod "$REPO/latest" @WebParams }
    if (!$LLAMA_VERSION) { Die "No version found" }
    "Version: $LLAMA_VERSION"

    if ($LLAMA_VERSION -match "^b([0-9]+)$") {
        $STAMP = "build $($Matches[1]),"
    } elseif ($LLAMA_VERSION -match "^g([0-9a-f]+)$") {
        $STAMP = "commit $($Matches[1]))"
    } else {
        Die "Invalid version: $LLAMA_VERSION"
    }
    $INSTALL_DIR = Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps"
    if (!$env:FORCE_UPDATE -and Test-Path "$INSTALL_DIR\llama.exe" -and (& "$INSTALL_DIR\llama.exe" version | Out-String).Contains($STAMP)) {
        "Already up to date"
        ""
        "To force an update, run:"
        ""
        "  `$env:FORCE_UPDATE = '1'"
        "  irm https://llama.app/install.ps1 | iex"
        ""
        return
    }
    $DIR = Join-Path $env:LOCALAPPDATA "llama-app"
    Remove-Item $DIR -Recurse -Force 2>$null
    New-Item -Path $DIR -Force -ItemType "Directory" | Out-Null

    if (!(Test-Path "$DIR\llama.exe")) { ProbeCUDA   }
    if (!(Test-Path "$DIR\llama.exe")) { ProbeROCm   }
    if (!(Test-Path "$DIR\llama.exe")) { ProbeVulkan }
    if (!(Test-Path "$DIR\llama.exe")) { ProbeCPU    }
    if (!(Test-Path "$DIR\llama.exe")) {
        Die "No prebuilt llama binary is available for your system." `
            "Please compile llama.cpp from source instead."
    }
    if ($env:SKIP_INSTALL) {
        "Installation skipped, SKIP_INSTALL is set"
        return
    }
    $Version = (& "$DIR\llama.exe" version) | Out-String

    if ($LASTEXITCODE) {
        Die "Downloaded llama binary failed to run"
    }
    if (!$Version.Contains($STAMP)) {
        Die "Version mismatch: expected $LLAMA_VERSION, got $Version"
    }
    if (Test-Path "$INSTALL_DIR\llama.exe") {
        Move-Item "$INSTALL_DIR\llama.exe" "$DIR\llama.exe.old" -Force
    }
    Move-Item "$DIR\llama.exe" "$INSTALL_DIR\llama.exe" -Force
    Remove-Item $DIR -Recurse -Force 2>$null

    "Installation completed successfully"
    ""
    "Please run the following command to start it:"
    ""
    "  llama.exe serve"
    ""
}

Main @args
