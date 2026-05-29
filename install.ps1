$REPO = "https://huggingface.co/buckets/ggml-org/install.sh/resolve"

function Die {
    param([string[]]$Messages)
    $Messages | % { [Console]::Error.WriteLine($_) }
    exit 111
}

function Download {
    param($FILE, $URL)
    if (Test-Path "$DIR\$FILE") {
        return
    }
    "Downloading $FILE..."
    try {
        if ($URL -like "*.zst") {
            Download "unzstd.exe" "$ARCH/windows/unzstd.exe"
            Invoke-RestMethod "$REPO/$VERSION/$URL" -OutFile "$DIR\tmp.zst"
            Start-Process -FilePath "$DIR\unzstd.exe" -RedirectStandardInput "$DIR\tmp.zst" -RedirectStandardOutput "$DIR\$FILE" -NoNewWindow -Wait
            Remove-Item "$DIR\tmp.zst"
        } else {
            Invoke-RestMethod "$REPO/$VERSION/$URL" -OutFile "$DIR\$FILE"
        }
    } catch {
        Die "Failed to download"
    }
}

function ProbeVulkan {
    if ($env:SKIP_VULKAN) { return }
    "Probing Vulkan..."
    Download "vulkan-probe.exe" "$ARCH/windows/vulkan/probe/probe.zst"
    Download "featcode.exe" "$ARCH/windows/featcode.exe"
    & "$DIR\vulkan-probe.exe" 2>$null
    if ($LASTEXITCODE) { return }
    $CONFIG = & "$DIR\featcode.exe" 2>$null
    & "$DIR\featcode.exe" $CONFIG 2>$null | % { "Found: $_" }
    Download "llama.exe" "$ARCH/windows/vulkan/$CONFIG/llama-app.zst"
}

function ProbeCPU {
    "Probing CPU..."
    Download "featcode.exe" "$ARCH/windows/featcode.exe"
    $CONFIG = & "$DIR\featcode.exe" 2>$null
    & "$DIR\featcode.exe" $CONFIG 2>$null | % { "Found: $_" }
    Download "llama.exe" "$ARCH/windows/cpu/$CONFIG/llama-app.zst"
}

function Main {
    switch ($env:PROCESSOR_ARCHITECTURE) {
        "ARM64" { $ARCH = "aarch64" }
        "AMD64" { $ARCH = "x86_64"  }
        default { Die "Arch not supported" }
    }

    if (!$VERSION) { $VERSION = $env:VERSION }
    if (!$VERSION) { $VERSION = Invoke-RestMethod "$REPO/latest" }
    if (!$VERSION) { Die "No version found" }
    "Version: $VERSION"

    $INSTALL_DIR = Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps"
    $DIR = Join-Path $env:TEMP "llama-app-tmp"
    Remove-Item $DIR -Recurse -Force 2>$null
    New-Item -Path $DIR -Force -ItemType "Directory" | Out-Null

    if (!(Test-Path "$DIR\llama.exe")) { ProbeVulkan }
    if (!(Test-Path "$DIR\llama.exe")) { ProbeCPU    }
    if (!(Test-Path "$DIR\llama.exe")) {
        Die "No prebuilt llama binary is available for your system." `
            "Please compile llama.cpp from source instead."
    }

    if (Test-Path "$INSTALL_DIR\llama.exe") {
        Move-Item "$INSTALL_DIR\llama.exe" "$INSTALL_DIR\llama.exe.old" -Force
    }
    Move-Item "$DIR\llama.exe" "$INSTALL_DIR\llama.exe" -Force
    Remove-Item $DIR -Recurse -Force 2>$null

    if ($args.Length -gt 0) {
        & llama.exe @args
        exit $LASTEXITCODE
    }
    "Installation completed successfully"
    ""
    "Please run the following command to start it:"
    ""
    "  llama.exe serve"
    ""
}

Main @args
