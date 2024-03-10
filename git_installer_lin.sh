#!/bin/bash

# Function to check if Git is installed
is_git_installed() {
    if git --version 2>/dev/null; then
        true
    else
        false
    fi
}

# Function to install Git
install_git() {
    echo "Attempting to install Git..."
    if [ -x "$(command -v apt-get)" ]; then
        sudo apt-get update && sudo apt-get install -y git
    elif [ -x "$(command -v yum)" ]; then
        sudo yum update && sudo yum install -y git
    else
        echo "Package manager not supported. Please install Git manually."
        exit 1
    fi
}

# Main script logic
if is_git_installed; then
    echo "Git is already installed."
else
    install_git
    if is_git_installed; then
        echo "Git successfully installed."
    else
        echo "Failed to install Git."
    fi
fi
