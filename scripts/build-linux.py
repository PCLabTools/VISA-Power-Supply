from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def print_header() -> None:
    print("====================================")
    print("Building Linux executable for main.py")
    print("====================================")


def resolve_paths() -> tuple[Path, str, Path, Path, Path]:
    repo_root = Path(__file__).resolve().parent.parent
    app_name = repo_root.name
    dist_dir = repo_root / "dist"
    build_dir = repo_root / "build"
    main_py = repo_root / "src" / "main.py"
    return repo_root, app_name, dist_dir, build_dir, main_py


def run_command(command: list[str], *, env: dict[str, str], capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, env=env, text=True, capture_output=capture_output)


def build_wsl_command(distro_name: str, args: list[str]) -> list[str]:
    return ["wsl.exe", "-d", distro_name, *args]


def normalize_wsl_text_output(output: str) -> str:
    return output.replace("\x00", "")


def normalize_linux_environment_name(name: str) -> str:
    normalized = []
    for character in name.lower():
        if character.isalnum():
            normalized.append(character)
        else:
            normalized.append("-")
    return "".join(normalized).strip("-") or "native"


def resolve_wsl_distribution(env: dict[str, str]) -> str | None:
    preferred = env.get("PAF_WSL_DISTRO")
    if preferred:
        return preferred

    result = run_command(["wsl.exe", "-l", "-q"], env=env, capture_output=True)
    if result.returncode != 0:
        return None

    distro_names = [
        line.strip()
        for line in normalize_wsl_text_output(result.stdout).splitlines()
        if line.strip()
    ]
    non_docker_distros = [
        distro_name
        for distro_name in distro_names
        if not distro_name.lower().startswith("docker-desktop")
    ]
    if not non_docker_distros:
        return None

    if len(non_docker_distros) == 1:
        return non_docker_distros[0]

    for distro_name in non_docker_distros:
        if distro_name.lower() in {"ubuntu", "ubuntu-22.04", "ubuntu-24.04"}:
            return distro_name

    return non_docker_distros[0]


def detect_privilege_escalation_command(env: dict[str, str], prefix: list[str] | None = None) -> str | None:
    command_prefix = prefix or []
    result = run_command(
        command_prefix
        + [
            "sh",
            "-c",
            "if [ \"$(id -u)\" = '0' ]; then echo root; "
            "elif command -v sudo > /dev/null 2>&1; then echo sudo; "
            "elif command -v doas > /dev/null 2>&1; then echo doas; "
            "else echo none; fi",
        ],
        env=env,
        capture_output=True,
    )
    if result.returncode != 0:
        return None

    privilege_tool = result.stdout.strip()
    if privilege_tool == "root":
        return ""
    if privilege_tool in {"sudo", "doas"}:
        return f"{privilege_tool} "
    return None


def detect_package_manager(env: dict[str, str], prefix: list[str] | None = None) -> str:
    command_prefix = prefix or []
    result = run_command(
        command_prefix
        + [
            "sh",
            "-c",
            "if command -v apt-get > /dev/null 2>&1; then echo apt; "
            "elif command -v apk > /dev/null 2>&1; then echo apk; "
            "elif command -v dnf > /dev/null 2>&1; then echo dnf; "
            "elif command -v yum > /dev/null 2>&1; then echo yum; "
            "elif command -v zypper > /dev/null 2>&1; then echo zypper; "
            "else echo none; fi",
        ],
        env=env,
        capture_output=True,
    )
    if result.returncode != 0:
        return "none"

    return result.stdout.strip()


def build_package_install_command(package_manager: str, escalate: str, *, include_python: bool) -> str | None:
    if package_manager == "apt":
        packages = ["binutils"]
        if include_python:
            packages.extend(["python3", "python3-venv", "python3-pip"])
        return f"{escalate}apt-get update && {escalate}apt-get install -y {' '.join(packages)}"

    if package_manager == "apk":
        packages = ["binutils"]
        if include_python:
            packages.extend(["python3", "py3-pip"])
        return f"{escalate}apk update && {escalate}apk add {' '.join(packages)}"

    if package_manager in ("dnf", "yum"):
        packages = ["binutils"]
        if include_python:
            packages.extend(["python3", "python3-pip"])
        return f"{escalate}{package_manager} install -y {' '.join(packages)}"

    if package_manager == "zypper":
        packages = ["binutils"]
        if include_python:
            packages.extend(["python3", "python3-pip"])
        return f"{escalate}zypper install -y {' '.join(packages)}"

    return None


def ensure_linux_system_tool(tool_name: str, package_name: str, env: dict[str, str]) -> bool:
    print(f"Checking for required system tool: {tool_name}")
    if shutil.which(tool_name) is not None:
        print(f"Required system tool '{tool_name}' is already installed.")
        return True

    package_manager = detect_package_manager(env)
    if package_manager == "none":
        print("ERROR: Could not detect a supported package manager in Linux.")
        print(f"       Install '{package_name}' manually and re-run this script.")
        return False

    escalate = detect_privilege_escalation_command(env)
    if escalate is None:
        print("ERROR: Cannot escalate privileges in Linux (no sudo, doas, or root).")
        print(f"       Install '{package_name}' manually and re-run this script.")
        return False

    if escalate:
        print(f"Using '{escalate.strip()}' for privilege escalation.")
        print("You may be prompted for your Linux password.")

    install_command = build_package_install_command(package_manager, escalate, include_python=False)
    if install_command is None:
        print("ERROR: Could not construct a package installation command for Linux.")
        print(f"       Install '{package_name}' manually and re-run this script.")
        return False

    print(f"Installing '{package_name}' via {package_manager}...")
    install = subprocess.run(["sh", "-c", install_command], env=env)
    if install.returncode == 0 and shutil.which(tool_name) is not None:
        print(f"Required system tool '{tool_name}' installed successfully.")
        return True

    print(f"ERROR: Failed to install required system tool '{tool_name}'.")
    return False


def running_on_windows() -> bool:
    return os.name == "nt"


def running_in_wsl() -> bool:
    if sys.platform != "linux":
        return False

    try:
        release = Path("/proc/sys/kernel/osrelease").read_text(encoding="utf-8").lower()
    except OSError:
        return False

    return "microsoft" in release or "wsl" in release


def convert_windows_path_to_wsl(path: Path, distro_name: str | None = None) -> str:
    """Convert a Windows absolute path to its WSL equivalent.

    Asks WSL itself via 'wslpath' first (handles custom /etc/wsl.conf automount
    roots) and falls back to the standard /mnt/<drive>/... convention.
    """
    path = path.resolve()
    # Pass the path using forward slashes so the shell doesn't misinterpret
    # backslashes. wslpath accepts both 'C:\foo' and 'C:/foo'.
    posix_win_path = str(path).replace("\\", "/")
    try:
        command = ["wsl.exe", "wslpath", "-u", posix_win_path]
        if distro_name:
            command = build_wsl_command(distro_name, ["wslpath", "-u", posix_win_path])
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass

    # Fallback: standard /mnt/<drive>/... convention.
    drive_letter = path.drive[0].lower()   # e.g. 'c' from 'C:'
    rest = str(path)[len(path.drive):]     # everything after 'C:'
    rest = rest.replace("\\", "/")         # backslashes → forward slashes
    return f"/mnt/{drive_letter}{rest}"


def has_python_venv_support(command_prefix: list[str], env: dict[str, str]) -> bool:
    result = run_command(
        command_prefix + ["python3", "-c", "import ensurepip, venv"],
        env=env,
        capture_output=True,
    )
    return result.returncode == 0


def ensure_python3_in_wsl(distro_name: str, env: dict[str, str]) -> bool:
    """Install python3 and python3-venv inside WSL if not already present."""
    wsl_prefix = build_wsl_command(distro_name, [])
    python_check = run_command(
        wsl_prefix + ["sh", "-c", "command -v python3 > /dev/null 2>&1"],
        env=env,
        capture_output=True,
    )
    if python_check.returncode == 0 and has_python_venv_support(wsl_prefix, env):
        print("python3 and venv support are available in WSL.")
        return True

    if python_check.returncode == 0:
        print("python3 is available in WSL, but venv support is missing. Attempting installation...")
    else:
        print("python3 not found in WSL. Attempting installation...")

    escalate = detect_privilege_escalation_command(env, prefix=wsl_prefix)
    if escalate is None:
        print("ERROR: Cannot escalate privileges in WSL (no sudo, doas, or root).")
        print("       Install python3 manually inside WSL and re-run this script.")
        return False

    if escalate:
        print(f"Using '{escalate.strip()}' for privilege escalation.")
        print("You may be prompted for your WSL password.")

    package_manager = detect_package_manager(env, prefix=wsl_prefix)
    install_cmd = build_package_install_command(package_manager, escalate, include_python=True)
    if install_cmd is None:
        print("ERROR: Could not detect a supported package manager in WSL (apt/apk/dnf/yum/zypper).")
        print("       Install python3 manually inside WSL and re-run this script.")
        return False

    print(f"Detected package manager: {package_manager}")

    # Run interactively (no capture_output) so password prompts reach the user.
    install = subprocess.run(
        wsl_prefix + ["sh", "-c", install_cmd],
        env=env,
    )
    if install.returncode == 0 and has_python_venv_support(wsl_prefix, env):
        print("python3 and venv support are installed successfully in WSL.")
        return True

    # The install command may have partially succeeded (e.g. python3 installed
    # but pip ran out of disk space). Re-check whether python3 is now available
    # — if so, continue; pip inside the venv is all the build actually needs.
    if has_python_venv_support(wsl_prefix, env):
        print("Warning: package installation reported errors but python3 and venv support are available. Continuing.")
        return True

    print("ERROR: Failed to install python3 and venv support in WSL.")
    print("       Ensure your WSL distro has internet access.")
    return False


def delegate_to_wsl(env: dict[str, str]) -> int:
    print("Windows host detected. Delegating Linux build to WSL...")
    if shutil.which("wsl.exe") is None:
        print("ERROR: WSL is not available on this system.")
        return 1

    distro_name = resolve_wsl_distribution(env)
    if distro_name is None:
        print("ERROR: No suitable WSL distribution was found.")
        print("       Install a Linux distro such as Ubuntu, or set PAF_WSL_DISTRO.")
        return 1

    print(f"Using WSL distribution: {distro_name}")

    if not ensure_python3_in_wsl(distro_name, env):
        return 1

    script_path = convert_windows_path_to_wsl(Path(__file__).resolve(), distro_name)
    if not script_path:
        print("ERROR: Failed to translate the build script path for WSL.")
        return 1

    linux_env_name = normalize_linux_environment_name(distro_name)
    result = run_command(
        build_wsl_command(
            distro_name,
            ["python3", script_path, "--native-linux", "--linux-env-name", linux_env_name],
        ),
        env=env,
    )
    if result.returncode == 0:
        return 0

    print("ERROR: Linux build failed in WSL.")
    return result.returncode


def resolve_linux_python(repo_root: Path, env: dict[str, str]) -> str | None:
    env_name = env.get("PAF_LINUX_ENV_NAME") or "native"
    linux_venv_root = repo_root / ".venv-linux"
    linux_venv = linux_venv_root / env_name
    candidate_paths = [
        linux_venv / "bin" / "python",
        repo_root / ".venv" / "bin" / "python",
    ]
    for candidate in candidate_paths:
        if candidate.exists():
            return str(candidate)

    bootstrap_python = shutil.which("python3") or shutil.which("python")
    if bootstrap_python is None:
        print("ERROR: No Linux Python interpreter was found.")
        return None

    print(f"Linux virtual environment not found. Creating {linux_venv.relative_to(repo_root)}...")
    result = run_command([bootstrap_python, "-m", "venv", str(linux_venv)], env=env)
    if result.returncode != 0:
        print(f"ERROR: Failed to create {linux_venv.relative_to(repo_root)}.")
        return None

    return str(linux_venv / "bin" / "python")


def ensure_python_available(python_exe: str, env: dict[str, str]) -> bool:
    print(f"Using Python: {python_exe}")
    result = run_command([python_exe, "--version"], env=env)
    if result.returncode == 0:
        return True

    print("ERROR: Python is not available in this environment.")
    return False


def ensure_build_dependencies(python_exe: str, env: dict[str, str]) -> bool:
    print()
    print("Checking build dependencies...")
    result = run_command([python_exe, "-c", "import PyInstaller, setuptools, wheel"], env=env)
    if result.returncode != 0:
        print("Build dependencies are missing. Attempting installation...")
        install_result = run_command(
            [python_exe, "-m", "pip", "install", "--no-cache-dir", "pyinstaller", "setuptools", "wheel"],
            env=env,
        )
        if install_result.returncode != 0:
            print("ERROR: Failed to install required build dependencies.")
            return False

    if not ensure_linux_system_tool("objdump", "binutils", env):
        return False

    print("Required build dependencies are ready.")
    return True


def ensure_application_dependencies(python_exe: str, repo_root: Path, env: dict[str, str]) -> bool:
    requirements_file = repo_root / "requirements.txt"
    if not requirements_file.exists():
        print("No requirements.txt found. Continuing with the current environment.")
        return True

    print("Installing application dependencies from requirements.txt...")
    result = run_command([python_exe, "-m", "pip", "install", "--no-cache-dir", "-r", str(requirements_file)], env=env)
    if result.returncode == 0:
        return True

    print("ERROR: Failed to install application dependencies.")
    return False


def clean_previous_binary(dist_dir: Path, app_name: str) -> None:
    print()
    print("Cleaning previous executable...")
    binary_path = dist_dir / app_name
    if binary_path.exists():
        binary_path.unlink()


def run_pyinstaller(
    python_exe: str,
    repo_root: Path,
    dist_dir: Path,
    build_dir: Path,
    app_name: str,
    main_py: Path,
    env: dict[str, str],
) -> bool:
    print()
    print("Running PyInstaller...")
    result = run_command(
        [
            python_exe,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onefile",
            "--name",
            app_name,
            "--distpath",
            str(dist_dir),
            "--workpath",
            str(build_dir),
            "--specpath",
            str(build_dir),
            "--paths",
            str(repo_root / "src"),
            "--collect-submodules",
            "paf",
            str(main_py),
        ],
        env=env,
    )
    if result.returncode == 0:
        return True

    print("ERROR: Build failed.")
    return False


def build_linux_binary(env: dict[str, str] | None = None) -> int:
    print_header()

    repo_root, app_name, dist_dir, build_dir, main_py = resolve_paths()
    os.chdir(repo_root)

    env = env.copy() if env is not None else os.environ.copy()
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    env.setdefault("PAF_LINUX_ENV_NAME", normalize_linux_environment_name(env.get("PAF_WSL_DISTRO") or "native"))

    python_exe = resolve_linux_python(repo_root, env)
    if python_exe is None:
        return 1

    if not ensure_python_available(python_exe, env):
        return 1

    dist_dir.mkdir(parents=True, exist_ok=True)
    build_dir.mkdir(parents=True, exist_ok=True)

    if not ensure_build_dependencies(python_exe, env):
        return 1

    if not ensure_application_dependencies(python_exe, repo_root, env):
        return 1

    clean_previous_binary(dist_dir, app_name)

    if not run_pyinstaller(python_exe, repo_root, dist_dir, build_dir, app_name, main_py, env):
        return 1

    binary_path = dist_dir / app_name
    if binary_path.exists():
        print()
        print("Build completed successfully.")
        print("Executable created at:")
        print(binary_path)
        if running_in_wsl():
            print("This Linux binary was built inside WSL.")
        return 0

    print(f"ERROR: Build finished but {app_name} was not found in the dist folder.")
    return 1


def main() -> int:
    env = os.environ.copy()
    args = list(sys.argv[1:])
    while args:
        argument = args.pop(0)
        if argument == "--native-linux":
            continue
        if argument == "--linux-env-name" and args:
            env["PAF_LINUX_ENV_NAME"] = args.pop(0)
            continue

    if running_on_windows():
        return delegate_to_wsl(env)

    return build_linux_binary(env)


if __name__ == "__main__":
    raise SystemExit(main())