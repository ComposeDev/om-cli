#!/bin/bash
 
# Navigate to the project root directory
cd "$(dirname "$0")/.."
 
# Activate virtual environment
source .venv/bin/activate
 
# Backup requirements.txt
cp requirements.txt requirements_backup.txt
 
# Read the libraries from requirements.txt
libraries=$(awk -F '==' '{print $1}' requirements.txt)
 
# Update each library and run tests
for lib in $libraries; do
    echo "Updating $lib..."
    pip install --upgrade "$lib"
    if pytest; then
        echo "$lib updated successfully."
        pip freeze | grep -E "$(echo $libraries | tr ' ' '|')" > requirements.txt
    else
        echo "Tests failed after updating $lib. Reverting changes."
        cp requirements_backup.txt requirements.txt
        pip install -r requirements.txt
        exit 1
    fi
done
 
echo "All libraries updated successfully."