#!/bin/bash

# Script to create a zip file of the project, excluding files in .gitignore

# Get the project directory name
PROJECT_DIR=$(basename "$PWD")
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
ZIP_NAME="${PROJECT_DIR}_${TIMESTAMP}.zip"

echo "Creating zip file: $ZIP_NAME"
echo "Excluding files from .gitignore..."

# Create a temporary file to store exclusion patterns
TEMP_EXCLUDE=$(mktemp)

# Read .gitignore and convert patterns to zip-compatible exclusions
if [ -f .gitignore ]; then
    while IFS= read -r line || [ -n "$line" ]; do
        # Skip empty lines and comments
        if [[ -z "$line" || "$line" =~ ^# ]]; then
            continue
        fi
        # Remove trailing slashes and add to exclusion list
        pattern=$(echo "$line" | sed 's:/$::')
        echo "$pattern" >> "$TEMP_EXCLUDE"
    done < .gitignore
fi

# Add common exclusions
echo ".git" >> "$TEMP_EXCLUDE"
echo "*.zip" >> "$TEMP_EXCLUDE"
echo ".DS_Store" >> "$TEMP_EXCLUDE"

# Create the zip file using git ls-files (respects .gitignore)
if git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Using git to determine files to include..."
    # Use git ls-files to get only tracked and untracked files (respecting .gitignore)
    git ls-files --cached --others --exclude-standard | zip -@ "../$ZIP_NAME"
else
    echo "Not a git repository. Using manual exclusion..."
    # Fallback: use zip with exclusions
    zip -r "../$ZIP_NAME" . -x@"$TEMP_EXCLUDE" -x "*.zip" -x ".git/*"
fi

# Clean up
rm -f "$TEMP_EXCLUDE"

# Check if zip was created successfully
if [ -f "../$ZIP_NAME" ]; then
    FILE_SIZE=$(du -h "../$ZIP_NAME" | cut -f1)
    echo ""
    echo "✅ Zip file created successfully!"
    echo "📦 File: ../$ZIP_NAME"
    echo "📊 Size: $FILE_SIZE"
    echo ""
    echo "Location: $(cd .. && pwd)/$ZIP_NAME"
else
    echo "❌ Error: Failed to create zip file"
    exit 1
fi
