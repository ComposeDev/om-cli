#!/bin/sh
# Run the CLI

# Get the directory of the current script
SCRIPT_DIR="$(dirname "$(realpath "$0")")"
export PYTHONPATH="$PYTHONPATH:$SCRIPT_DIR"
python -m src.om_cli