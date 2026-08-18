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
    if ($LASTEXITCODE) { return }
    "Found: $CONFIG"
    $parts  = -split $CONFIG
    $CONFIG = $parts[0]
    $MAJOR  = $parts[1]
    Download "llama.exe" "$ARCH/windows/cuda/$MAJOR/$CONFIG/llama-app.exe.zst" | Out-Null
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

    $INSTALL_DIR = Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps"
    $DIR = Join-Path $env:LOCALAPPDATA "llama-app"
    Remove-Item $DIR -Recurse -Force 2>$null
    New-Item -Path $DIR -Force -ItemType "Directory" | Out-Null

    if (!(Test-Path "$DIR\llama.exe")) { ProbeCUDA   }
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
    $Version = & "$DIR\llama.exe" version 2>&1

    if ($LASTEXITCODE) {
        Die "Downloaded llama binary failed to run"
    }
    $BUILD = $LLAMA_VERSION -replace "^b", ""
    if ("$Version" -notlike "$LLAMA_VERSION-*" -and "$Version" -notlike "*build $BUILD*") {
        Die "Version mismatch: expected build $BUILD, got $Version"
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
