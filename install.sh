REPO="https://huggingface.co/buckets/ggml-org/install.sh/resolve"

die() {
	printf "%s\n" "$@" >&2
	exit 111
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

dl_bin() {
	[ -x "$1" ] && return
	check_bin curl || die "Please install curl"
	printf "Downloading %s...\n" "$1"
	case "$2" in
	(*.zst) curl -fsSL "$REPO/$VERSION/$2" | unzstd ;;
	(*)     curl -fsSL "$REPO/$VERSION/$2" ;;
	esac > "$1.tmp" 2>/dev/null &&
	chmod +x "$1.tmp" && mv "$1.tmp" "$1" && return
	printf "Failed to download\n" >&2
	return 1
}

unzstd() (
	command -v zstd >/dev/null 2>/dev/null && exec zstd -d
	dl_bin unzstd "$ARCH/$OS/unzstd"
	exec ./unzstd
)

probe_cuda() {
	[ -z "$SKIP_CUDA" ] && printf "Probing CUDA...\n" &&
	dl_bin cuda-probe "$ARCH/$OS/cuda/probe/probe.zst" &&
	CONFIG=$(./cuda-probe) 2>/dev/null &&
	printf "Found: %s\n" "$CONFIG" &&
	dl_bin llama "$ARCH/$OS/cuda/$CONFIG/llama-app.zst"
}

probe_rocm() {
	[ -z "$SKIP_ROCM" ] && printf "Probing ROCm...\n" &&
	dl_bin rocm-probe "$ARCH/$OS/rocm/probe/probe.zst" &&
	CONFIG=$(./rocm-probe) 2>/dev/null &&
	printf "Found: %s\n" "$CONFIG" &&
	dl_bin llama "$ARCH/$OS/rocm/$CONFIG/llama-app.zst"
}

probe_vulkan() {
	[ -z "$SKIP_VULKAN" ] && printf "Probing Vulkan...\n" &&
	dl_bin vulkan-probe "$ARCH/$OS/vulkan/probe/probe.zst" &&
	dl_bin featcode "$ARCH/$OS/featcode" &&
	CONFIG=$(./vulkan-probe && ./featcode) 2>/dev/null &&
	for F in $(./featcode "$CONFIG"); do printf "Found: %s\n" "$F"; done &&
	dl_bin llama "$ARCH/$OS/vulkan/$CONFIG/llama-app.zst"
}

probe_cpu() {
	printf "Probing CPU...\n" &&
	dl_bin featcode "$ARCH/$OS/featcode" &&
	CONFIG=$(./featcode) 2>/dev/null &&
	for F in $(./featcode "$CONFIG"); do printf "Found: %s\n" "$F"; done &&
	dl_bin llama "$ARCH/$OS/cpu/$CONFIG/llama-app.zst"
}

probe_metal() {
	printf "Probing Metal...\n" &&
	CONFIG=$(sysctl -n machdep.cpu.brand_string | grep -o "Apple M[1-5]") 2>/dev/null &&
	CONFIG=m${CONFIG##*M} &&
	printf "Found: %s\n" "$CONFIG" &&
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

	[ "$VERSION" ] || VERSION=$(curl -fsSL "$REPO/latest")
	[ "$VERSION" ] || die "No version found"
	printf "Version: %s\n" "$VERSION"

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

	[ $# -gt 0 ] && exec ~/.llama-app/llama "$@"

	mkdir -p "$HOME/.local/bin" &&
	ln -sf "$HOME/.llama-app/llama" "$HOME/.local/bin/llama" || die \
		"Couldn't install llama to ~/.local/bin"

	printf "Installation completed successfully\n\n"

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
