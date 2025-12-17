#!/bin/bash
set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
EXAMPLES_DIR="$ROOT_DIR/examples"

# List of example folders that have a generate.sh script
EXAMPLE_FOLDERS=(
    "c-sharp-api-client"
    "php-api-client"
    "python-api-client"
    "typescript-api-client"
)

echo "=========================================="
echo "Running generate.sh for all API client examples"
echo "=========================================="

for folder in "${EXAMPLE_FOLDERS[@]}"; do
    example_path="$EXAMPLES_DIR/$folder"
    generate_script="$example_path/generate.sh"
    
    if [[ -f "$generate_script" ]]; then
        echo ""
        echo "=========================================="
        echo "Generating: $folder"
        echo "=========================================="
        
        cd "$example_path"
        bash generate.sh
        
        echo ""
        echo "✓ Completed: $folder"
    else
        echo ""
        echo "⚠ Warning: generate.sh not found in $folder, skipping..."
    fi
done

echo ""
echo "=========================================="
echo "All API client generation complete!"
echo "=========================================="

