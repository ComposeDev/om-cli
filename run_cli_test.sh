#!/bin/sh
# Run the CLI

# Get the directory of the current script
SCRIPT_DIR="$(dirname "$(realpath "$0")")"
export PYTHONPATH="$PYTHONPATH:$SCRIPT_DIR"
python -m src.om_cli -t custom/test_resources/mock_om_tree.json -m custom/test_resources/mock_api_responses.json