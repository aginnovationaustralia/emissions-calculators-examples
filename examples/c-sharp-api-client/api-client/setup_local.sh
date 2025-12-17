#!/bin/bash

# Setup script for local development and testing of the C# API client
# This script checks for .NET runtime and restores dependencies

set -e

echo "Setting up C# API client for local development..."

# Check if .NET SDK is available
if ! command -v dotnet &> /dev/null; then
    echo "Error: .NET SDK is not installed or not in PATH"
    echo "Please install .NET SDK 9.0 or later from https://dotnet.microsoft.com/download"
    exit 1
fi

# Check .NET version
dotnet_version=$(dotnet --version 2>&1)
echo "Found .NET SDK version: $dotnet_version"

# Check if .NET 9.0+ is available (required by the generated client)
required_major=9
actual_major=$(echo $dotnet_version | cut -d. -f1)

if [ "$actual_major" -lt "$required_major" ]; then
    echo "Warning: .NET SDK 9.0+ is recommended. Found version $dotnet_version"
    echo "The generated client targets .NET 9.0"
fi

# Restore dependencies for the API client library
echo "Restoring dependencies for API client library..."
cd src/Org.OpenAPITools
dotnet restore
cd ../..

# Restore dependencies for the test program
if [ -f "TestApi.csproj" ]; then
    echo "Restoring dependencies for test program..."
    dotnet restore TestApi.csproj
fi

echo ""
echo "Setup complete! To use the API client:"
echo "1. Run the test script: ./run_test.sh"
echo "2. Or manually: dotnet run --project TestApi.csproj"
echo ""
echo "Note: Make sure you have cert.pem and key.pem files in the api-client directory"
echo "      for mTLS authentication, or update the paths in Program.cs"

