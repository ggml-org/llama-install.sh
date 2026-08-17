[ "$LLAMA_BUCKET" ] || LLAMA_BUCKET="ggml-org/install.sh"
REPO="https://huggingface.co/buckets/$LLAMA_BUCKET/resolve"

die() {
	printf "%s\n" "$@" >&2
	exit 111
}

info() {
	printf "%s\n" "$@" >&2
}

check_bin() {
	command -v "$1" >/dev/null 2>/dev/null
}

check_path() {
	case ":$1:" in
	(*":$HOME/.local/bin:"*) return 0 ;;
	esac
	return 1
}

curl() {
	if [ -n "$HF_TOKEN" ]
	then command curl -H "Authorization: Bearer $HF_TOKEN" "$@"
	else command curl "$@"
	fi
}

dl_bin() {
	[ -x "$1" ] && return
	check_bin curl || die "Please install curl"
	info "Downloading $1..."
	case "$2" in
	(*.zst) curl -fsSL "$REPO/$LLAMA_VERSION/$2" | unzstd ;;
	(*)     curl -fsSL "$REPO/$LLAMA_VERSION/$2" ;;
	esac > "$1.tmp" 2>/dev/null &&
	chmod +x "$1.tmp" && mv "$1.tmp" "$1" && return
	info "Failed to download"
	return 1
}

unzstd() (
	command -v zstd >/dev/null 2>/dev/null && exec zstd -d
	dl_bin unzstd "$ARCH/$OS/unzstd"
	exec ./unzstd
)

probe_cuda() {
	[ -z "$SKIP_CUDA" ] && info "Probing CUDA..." &&
	dl_bin cuda-probe "$ARCH/$OS/cuda/probe/probe.zst" &&
	CONFIG=$(./cuda-probe) 2>/dev/null &&
	info "Found: $CONFIG" &&
	CONFIG=${CONFIG%% *} &&
	dl_bin llama "$ARCH/$OS/cuda/$CONFIG/llama-app.zst"
}

probe_rocm() {
	[ -z "$SKIP_ROCM" ] && info "Probing ROCm..." &&
	dl_bin rocm-probe "$ARCH/$OS/rocm/probe/probe.zst" &&
	CONFIG=$(./rocm-probe) 2>/dev/null &&
	info "Found: $CONFIG" &&
	dl_bin llama "$ARCH/$OS/rocm/$CONFIG/llama-app.zst"
}

probe_vulkan() {
	[ -z "$SKIP_VULKAN" ] && info "Probing Vulkan..." &&
	dl_bin vulkan-probe "$ARCH/$OS/vulkan/probe/probe.zst" &&
	dl_bin featcode "$ARCH/$OS/featcode" &&
	CONFIG=$(./vulkan-probe && ./featcode) 2>/dev/null &&
	for F in $(./featcode "$CONFIG"); do info "Found: $F"; done &&
	dl_bin llama "$ARCH/$OS/vulkan/$CONFIG/llama-app.zst"
}

probe_cpu() {
	info "Probing CPU..." &&
	dl_bin featcode "$ARCH/$OS/featcode" &&
	CONFIG=$(./featcode) 2>/dev/null &&
	for F in $(./featcode "$CONFIG"); do info "Found: $F"; done &&
	dl_bin llama "$ARCH/$OS/cpu/$CONFIG/llama-app.zst"
}

probe_metal_cpu() {
	read -r apple cpu _
	[ "$apple" = Apple ] &&
	case "$cpu" in
	(M[12345]|A18) echo "$cpu" | tr '[:upper:]' '[:lower:]' ;;
	(*) return 1 ;;
	esac
}

probe_metal() {
	info "Probing Metal..." &&
	CONFIG=$(sysctl -n machdep.cpu.brand_string 2>/dev/null | probe_metal_cpu) &&
	info "Found: $CONFIG" &&
	dl_bin llama "$ARCH/$OS/metal/$CONFIG/llama-app.zst"
}

main() {
	case "$(uname -m)" in
	(arm64|aarch64) ARCH=aarch64 ;;
	(amd64|x86_64)  ARCH=x86_64  ;;
	(*) die "Arch not supported"
	esac

	case "$(uname -s)" in
	(Linux)   OS=linux ;;
	(FreeBSD) OS=freebsd ;;
	(Darwin)  OS=macos ;;
	(*) die "OS not supported"
	esac

	[ "$HOME" ] || die "No HOME, please check your OS"

	# Migrate from the old symlink-based install, remove later
	if [ "$(readlink ~/.local/bin/llama)" = "$HOME/.llama-app/llama" ]
	then
		if   cp -L ~/.local/bin/llama     ~/.local/bin/llama.fix 2>/dev/null
		then mv    ~/.local/bin/llama.fix ~/.local/bin/llama
		else rm -f ~/.local/bin/llama
		fi
	fi

	[ "$LLAMA_VERSION" ] || LLAMA_VERSION=$(curl -fsSL "$REPO/latest")
	[ "$LLAMA_VERSION" ] || die "No version found"
	info "Version: $LLAMA_VERSION"

	(
		rm -rf ~/.llama-app
		mkdir -p ~/.llama-app
		cd ~/.llama-app || exit 1

		case "$OS" in
		(macos)   [ -x llama ] || probe_metal ;;
		(linux)   [ -x llama ] || probe_cuda
		          [ -x llama ] || probe_rocm
		          [ -x llama ] || probe_vulkan
		          [ -x llama ] || probe_cpu ;;
		(freebsd) [ -x llama ] || probe_cpu ;;
		esac

		[ -x llama ] || die \
			"No prebuilt llama binary is available for your system." \
			"Please compile llama.cpp from source instead."
	) || exit

	if [ "$SKIP_INSTALL" ]; then
		info "Installation skipped, SKIP_INSTALL is set"
		return
	fi

	VERSION=$(~/.llama-app/llama version 2>/dev/null) || die \
		"Downloaded llama binary failed to run"

    case "$VERSION" in
    ("$LLAMA_VERSION"-*) ;;
    (*"build ${LLAMA_VERSION#b}"*) ;;
	(*) die "Version mismatch: expected build ${LLAMA_VERSION#b}, got $VERSION" ;;
	esac

	mkdir -p ~/.local/bin &&
	cp ~/.llama-app/llama ~/.local/bin/llama.tmp &&
	mv ~/.local/bin/llama.tmp ~/.local/bin/llama || die \
		"Couldn't install llama to ~/.local/bin"

	info "Installation completed successfully" ""

	if check_path "$PATH"; then
		cat <<-EOF
		Run the following command to start it:

		  llama serve

		EOF
		return
	fi

	LOGIN_SHELL="${SHELL:-/bin/sh}"
	LOGIN_PATH=$("$LOGIN_SHELL" -l -c 'echo $PATH' 2>/dev/null)

	if check_path "$LOGIN_PATH"; then
		cat <<-'EOF'
		Please open a new terminal window or restart your shell.

		  llama serve

		EOF
	else
		RC_FILE=
		case "${SHELL##*/}" in
		(bash) RC_FILE=".bash_profile" ;;
		(zsh)  RC_FILE=".zprofile" ;;
		esac
		if [ "$RC_FILE" ]; then
			cat <<-EOF
			To make llama available in future sessions, add ~/.local/bin to your PATH by running:

			  echo 'export PATH="\$HOME/.local/bin:\$PATH"' >> ~/${RC_FILE}

			EOF
		else
			cat <<-EOF
			Add this line to your shell profile to include ~/.local/bin to your PATH:

			  export PATH="\$HOME/.local/bin:\$PATH"

			EOF
		fi
		cat <<-EOF
		Then open a new terminal and run:

		  llama serve

		EOF
	fi
	cat <<-EOF
	To start it now without modifying your PATH, run:

	  ~/.llama-app/llama serve

	EOF
}

main "$@"
