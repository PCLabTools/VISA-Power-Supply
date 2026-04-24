from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def print_header() -> None:
    print("======================================")
    print("Building Windows executable for main.py")
    print("======================================")


def resolve_paths() -> tuple[Path, str, Path, Path, Path]:
    repo_root = Path(__file__).resolve().parent.parent
    app_name = repo_root.name
    dist_dir = repo_root / "dist"
    build_dir = repo_root / "build"
    main_py = repo_root / "src" / "main.py"
    return repo_root, app_name, dist_dir, build_dir, main_py


def resolve_python_executable(repo_root: Path) -> str:
    venv_python = repo_root / ".venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        return str(venv_python)

    print("Virtual environment not found. Falling back to system Python.")
    system_python = shutil.which("python")
    return system_python or "python"


def run_command(command: list[str], *, env: dict[str, str], check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, env=env, text=True, check=check)


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
    if result.returncode == 0:
        print("Required build dependencies are already installed.")
        return True

    print("Build dependencies are missing. Attempting installation...")
    install_result = run_command(
        [python_exe, "-m", "pip", "install", "pyinstaller", "setuptools", "wheel"],
        env=env,
    )
    if install_result.returncode == 0:
        return True

    print("ERROR: Failed to install required build dependencies.")
    return False


def ensure_application_dependencies(python_exe: str, repo_root: Path, env: dict[str, str]) -> bool:
    requirements_file = repo_root / "requirements.txt"
    if not requirements_file.exists():
        print("No requirements.txt found. Continuing with the current environment.")
        return True

    print("Installing application dependencies from requirements.txt...")
    result = run_command([python_exe, "-m", "pip", "install", "-r", str(requirements_file)], env=env)
    if result.returncode == 0:
        return True

    print("ERROR: Failed to install application dependencies.")
    return False


def clean_previous_executable(dist_dir: Path, app_name: str) -> None:
    print()
    print("Cleaning previous executable...")
    exe_path = dist_dir / f"{app_name}.exe"
    if exe_path.exists():
        exe_path.unlink()


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


def main() -> int:
    print_header()

    repo_root, app_name, dist_dir, build_dir, main_py = resolve_paths()
    os.chdir(repo_root)

    python_exe = resolve_python_executable(repo_root)
    env = os.environ.copy()
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"

    if not ensure_python_available(python_exe, env):
        return 1

    dist_dir.mkdir(parents=True, exist_ok=True)
    build_dir.mkdir(parents=True, exist_ok=True)

    if not ensure_build_dependencies(python_exe, env):
        return 1

    if not ensure_application_dependencies(python_exe, repo_root, env):
        return 1

    clean_previous_executable(dist_dir, app_name)

    if not run_pyinstaller(python_exe, repo_root, dist_dir, build_dir, app_name, main_py, env):
        return 1

    exe_path = dist_dir / f"{app_name}.exe"
    if exe_path.exists():
        print()
        print("Build completed successfully.")
        print("Executable created at:")
        print(exe_path)
        return 0

    print(f"ERROR: Build finished but {app_name}.exe was not found in the dist folder.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())