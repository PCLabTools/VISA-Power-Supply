#!/usr/bin/env sh

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)

PYTHON_EXE="$REPO_ROOT/.venv/bin/python"
if [ ! -x "$PYTHON_EXE" ]; then
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_EXE=python3
    else
        PYTHON_EXE=python
    fi
fi

while true; do
    clear
    echo "======================================"
    echo "PAF Template Project Build Menu"
    echo "======================================"
    echo
    echo "  1. Build Linux executable"
    echo "  2. Exit"
    echo
    printf "Select an option [1-2]: "
    IFS= read -r build_choice

    case "$build_choice" in
        1)
            echo
            echo "Running Linux build..."
            "$PYTHON_EXE" "$REPO_ROOT/scripts/build-linux.py"
            build_exit_code=$?
            echo
            if [ "$build_exit_code" -eq 0 ]; then
                echo "Build completed successfully."
            else
                echo "Build failed with exit code $build_exit_code."
            fi
            echo
            printf "Press Enter to continue..."
            IFS= read -r _
            ;;
        2)
            exit 0
            ;;
        *)
            echo
            echo "Invalid selection."
            printf "Press Enter to continue..."
            IFS= read -r _
            ;;
    esac
done