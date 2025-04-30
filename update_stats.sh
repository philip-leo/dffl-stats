#!/bin/bash

# Get the directory of the script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the project directory
cd "$DIR"

# Activate Python environment if you're using one
# source /path/to/your/venv/bin/activate  # Uncomment and modify if using a virtual environment

# Run the update script and log output
echo "Starting stats update at $(date)" >> update_log.txt
python3 update_2025_stats.py >> update_log.txt 2>&1
echo "Update completed at $(date)" >> update_log.txt
echo "----------------------------------------" >> update_log.txt 