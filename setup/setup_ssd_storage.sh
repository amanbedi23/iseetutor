#!/bin/bash
# Script to set up 1TB SSD for ISEE Tutor storage
# Run with: sudo bash setup_ssd_storage.sh

set -e

echo "=== ISEE Tutor SSD Storage Setup ==="
echo "This script will set up your 1TB NVMe SSD for storage"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Check if SSD exists
if [ ! -e /dev/nvme0n1 ]; then
    echo "Error: NVMe SSD not found at /dev/nvme0n1"
    exit 1
fi

echo "Found NVMe SSD:"
lsblk /dev/nvme0n1

echo ""
echo "Current mount status:"
mount | grep nvme || echo "SSD is not currently mounted"

echo ""
echo "WARNING: This will set up the SSD for ISEE Tutor storage."
echo "If the SSD already has data, it will be preserved but we'll mount it at /mnt/ssd"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Check if SSD has partitions
PARTITIONS=$(lsblk -n /dev/nvme0n1 | grep -c part || true)

if [ "$PARTITIONS" -eq 0 ]; then
    echo ""
    echo "SSD has no partitions. Creating partition table..."
    
    # Create GPT partition table and single partition
    parted -s /dev/nvme0n1 mklabel gpt
    parted -s /dev/nvme0n1 mkpart primary ext4 0% 100%
    
    # Wait for partition to be recognized
    sleep 2
    
    # Format the partition
    echo "Formatting partition as ext4..."
    mkfs.ext4 -F /dev/nvme0n1p1
    
    PARTITION="/dev/nvme0n1p1"
else
    echo "SSD already has partitions:"
    lsblk /dev/nvme0n1
    
    # Assume first partition
    PARTITION="/dev/nvme0n1p1"
    
    # Check filesystem
    FS_TYPE=$(lsblk -no FSTYPE $PARTITION)
    echo "Partition $PARTITION has filesystem: $FS_TYPE"
fi

# Create mount point
echo ""
echo "Creating mount point at /mnt/ssd..."
mkdir -p /mnt/ssd

# Mount the SSD
echo "Mounting SSD..."
mount $PARTITION /mnt/ssd || {
    echo "Failed to mount. Checking filesystem..."
    fsck -y $PARTITION
    mount $PARTITION /mnt/ssd
}

# Get UUID for permanent mounting
UUID=$(blkid -s UUID -o value $PARTITION)
echo "SSD UUID: $UUID"

# Add to fstab for automatic mounting
echo "Adding to /etc/fstab for automatic mounting..."
if ! grep -q "$UUID" /etc/fstab; then
    echo "UUID=$UUID /mnt/ssd ext4 defaults,noatime 0 2" >> /etc/fstab
    echo "Added to fstab"
else
    echo "Already in fstab"
fi

# Create ISEE Tutor storage structure on SSD
echo ""
echo "Creating ISEE Tutor storage directories..."
mkdir -p /mnt/ssd/iseetutor/{models,knowledge,content,user_data,cache,logs}
mkdir -p /mnt/ssd/iseetutor/knowledge/{databases,vectors,documents}
mkdir -p /mnt/ssd/iseetutor/models/{llm,whisper,tts,embeddings}

# Set ownership
echo "Setting ownership to user 'tutor'..."
chown -R tutor:tutor /mnt/ssd/iseetutor

# Create symlink from /mnt/storage to SSD location
echo "Creating symlink from /mnt/storage to SSD..."
if [ -L /mnt/storage ]; then
    rm /mnt/storage
elif [ -d /mnt/storage ]; then
    # Backup existing data
    if [ "$(ls -A /mnt/storage)" ]; then
        echo "Moving existing /mnt/storage data to SSD..."
        cp -r /mnt/storage/* /mnt/ssd/iseetutor/ || true
    fi
    rm -rf /mnt/storage
fi
ln -s /mnt/ssd/iseetutor /mnt/storage

# Show results
echo ""
echo "=== Storage Setup Complete ==="
echo ""
echo "SSD mounted at: /mnt/ssd"
echo "ISEE Tutor storage at: /mnt/ssd/iseetutor"
echo "Symlink created: /mnt/storage -> /mnt/ssd/iseetutor"
echo ""
echo "Storage structure:"
tree -L 2 /mnt/ssd/iseetutor || ls -la /mnt/ssd/iseetutor

echo ""
echo "Disk usage:"
df -h /mnt/ssd

echo ""
echo "The SSD will automatically mount on boot."
echo "All ISEE Tutor data should be stored in /mnt/storage/"