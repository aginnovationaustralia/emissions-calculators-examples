#!/bin/bash

# Quick run script for testing the C# API client
# This script builds and runs the test program

set -e

# Check if .NET SDK is available
if ! command -v dotnet &> /dev/null; then
    echo "Error: .NET SDK is not installed or not in PATH"
    echo "Please install .NET SDK 9.0 or later from https://dotnet.microsoft.com/download"
    exit 1
fi

# Check if test project exists
if [ ! -f "TestApi.csproj" ]; then
    echo "Error: TestApi.csproj not found. Please run ./setup_local.sh first"
    exit 1
fi

# Build and run the test program
echo "Building and running API test program..."
dotnet run --project TestApi.csproj -p:WarningLevel=0

echo ""
echo "Test complete!"

