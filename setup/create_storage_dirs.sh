#!/bin/bash
# Create storage directories for ISEE Tutor

echo "=== Creating Storage Directories ==="
echo ""
echo "This script needs sudo to create directories in /mnt/storage"
echo ""

# Create main storage directory
sudo mkdir -p /mnt/storage

# Create subdirectories
sudo mkdir -p /mnt/storage/{models,knowledge,content,user_data}
sudo mkdir -p /mnt/storage/knowledge/{databases,isee_content,general_knowledge}

# Set ownership to current user
sudo chown -R $USER:$USER /mnt/storage

# Create local directories (no sudo needed)
mkdir -p logs
mkdir -p data/{models,content,users}

echo "✅ Storage directories created successfully!"
echo ""
ls -la /mnt/storage/
echo ""
echo "You now have full access to /mnt/storage for storing models and data."