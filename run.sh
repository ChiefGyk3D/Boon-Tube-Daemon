#!/bin/bash
# Quick start script for Boon-Tube-Daemon

#!/bin/bash
# Quick start script for Boon-Tube-Daemon

# Change to script directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the daemon
python3 main.py
