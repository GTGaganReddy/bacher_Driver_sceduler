#!/bin/bash

# Cloudflare Pages Build Script
echo "Building Driver Scheduling API for Cloudflare Pages..."

# Install dependencies
pip install -r requirements.txt

# Create build output directory
mkdir -p dist

# Copy application files
cp -r . dist/
cd dist

# Remove unnecessary files
rm -rf .git .gitignore README.md

echo "Build complete - ready for Cloudflare Pages deployment"