#!/bin/bash

# Script to mount the NVMe SSD on new Jetson
# Run this BEFORE the restore script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== ISEE Tutor SSD Mount Script ===${NC}"
echo "This script will help mount your NVMe SSD"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}This script must be run as root (sudo)${NC}"
    exit 1
fi

# List available disks
echo -e "${GREEN}1. Detecting NVMe drives...${NC}"
echo "Available drives:"
lsblk -d -o NAME,SIZE,TYPE,MODEL | grep -E "disk|nvme"

# Find NVMe devices
NVME_DEVICES=$(lsblk -d -o NAME,TYPE | grep nvme | awk '{print "/dev/"$1}')

if [ -z "$NVME_DEVICES" ]; then
    echo -e "${RED}No NVMe drives found!${NC}"
    echo "Please check:"
    echo "  - SSD is properly connected"
    echo "  - Power to the SSD"
    echo "  - Try: sudo nvme list"
    exit 1
fi

# If multiple NVMe devices, let user choose
NVME_COUNT=$(echo "$NVME_DEVICES" | wc -l)
if [ $NVME_COUNT -gt 1 ]; then
    echo -e "\n${YELLOW}Multiple NVMe drives found:${NC}"
    echo "$NVME_DEVICES"
    echo -n "Enter the device path (e.g., /dev/nvme0n1): "
    read NVME_DEVICE
else
    NVME_DEVICE=$(echo "$NVME_DEVICES" | head -1)
    echo -e "\nFound NVMe drive: ${GREEN}$NVME_DEVICE${NC}"
fi

# List partitions
echo -e "\n${GREEN}2. Checking partitions on $NVME_DEVICE...${NC}"
lsblk $NVME_DEVICE -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINT

# Find the data partition (usually the largest ext4 partition)
PARTITION=$(lsblk $NVME_DEVICE -ln -o NAME,SIZE,FSTYPE | grep ext4 | sort -k2 -hr | head -1 | awk '{print "/dev/"$1}')

if [ -z "$PARTITION" ]; then
    echo -e "${YELLOW}No ext4 partition found. Listing all partitions:${NC}"
    lsblk $NVME_DEVICE -o NAME,SIZE,FSTYPE
    echo -n "Enter the partition to mount (e.g., /dev/nvme0n1p1): "
    read PARTITION
else
    echo -e "Found data partition: ${GREEN}$PARTITION${NC}"
    echo -n "Use this partition? (y/n): "
    read CONFIRM
    if [ "$CONFIRM" != "y" ]; then
        echo -n "Enter the partition to mount: "
        read PARTITION
    fi
fi

# Check if partition exists
if [ ! -b "$PARTITION" ]; then
    echo -e "${RED}Error: Partition $PARTITION does not exist${NC}"
    exit 1
fi

# Create mount point
echo -e "\n${GREEN}3. Creating mount point...${NC}"
mkdir -p /mnt/storage

# Check if already mounted
if mount | grep -q "$PARTITION"; then
    CURRENT_MOUNT=$(mount | grep "$PARTITION" | awk '{print $3}')
    echo -e "${YELLOW}Warning: $PARTITION is already mounted at $CURRENT_MOUNT${NC}"
    
    if [ "$CURRENT_MOUNT" = "/mnt/storage" ]; then
        echo -e "${GREEN}Already mounted correctly!${NC}"
        exit 0
    else
        echo -n "Unmount and remount at /mnt/storage? (y/n): "
        read CONFIRM
        if [ "$CONFIRM" = "y" ]; then
            umount "$PARTITION"
        else
            echo "Exiting without changes"
            exit 0
        fi
    fi
fi

# Mount the partition
echo -e "\n${GREEN}4. Mounting $PARTITION to /mnt/storage...${NC}"
mount "$PARTITION" /mnt/storage

# Verify mount
if mount | grep -q "/mnt/storage"; then
    echo -e "${GREEN}✓ Successfully mounted!${NC}"
    echo ""
    echo "Mounted filesystem info:"
    df -h /mnt/storage
    echo ""
    echo "Contents:"
    ls -la /mnt/storage/
else
    echo -e "${RED}Mount failed!${NC}"
    exit 1
fi

# Get UUID for permanent mounting
echo -e "\n${GREEN}5. Setting up permanent mount...${NC}"
UUID=$(blkid -s UUID -o value "$PARTITION")

if [ ! -z "$UUID" ]; then
    # Check if already in fstab
    if grep -q "$UUID" /etc/fstab; then
        echo -e "${YELLOW}UUID already in /etc/fstab, updating...${NC}"
        sed -i "/$UUID/d" /etc/fstab
    fi
    
    # Add to fstab
    echo "UUID=$UUID /mnt/storage ext4 defaults,nofail 0 2" >> /etc/fstab
    echo -e "${GREEN}✓ Added to /etc/fstab for automatic mounting${NC}"
else
    echo -e "${YELLOW}Warning: Could not get UUID. Manual fstab entry needed.${NC}"
fi

# Set permissions
echo -e "\n${GREEN}6. Setting permissions...${NC}"
JETSON_USER=${SUDO_USER:-jetson}
chown -R $JETSON_USER:$JETSON_USER /mnt/storage
echo -e "✓ Ownership set to $JETSON_USER"

# Verify expected directories
echo -e "\n${GREEN}7. Verifying ISEE Tutor data...${NC}"
echo "Checking for expected directories:"

for dir in models knowledge content; do
    if [ -d "/mnt/storage/$dir" ]; then
        echo -e "  ✓ /mnt/storage/$dir exists"
        # Show some contents
        if [ "$dir" = "models" ]; then
            echo "    Models found:"
            find /mnt/storage/models -name "*.gguf" -o -name "*.bin" 2>/dev/null | head -5 | sed 's/^/      - /'
        fi
    else
        echo -e "  ${YELLOW}✗ /mnt/storage/$dir not found${NC}"
    fi
done

# Create missing directories
echo -e "\n${GREEN}8. Creating any missing directories...${NC}"
for dir in models knowledge content; do
    if [ ! -d "/mnt/storage/$dir" ]; then
        mkdir -p "/mnt/storage/$dir"
        chown $JETSON_USER:$JETSON_USER "/mnt/storage/$dir"
        echo "  Created /mnt/storage/$dir"
    fi
done

# Summary
echo -e "\n${GREEN}=== SSD Mount Complete ===${NC}"
echo ""
echo "SSD mounted at: /mnt/storage"
echo "Filesystem: $(df -h /mnt/storage | tail -1 | awk '{print $1 " - " $2 " total, " $4 " free"}')"
echo ""
echo "The SSD will automatically mount on boot."
echo ""
echo -e "${GREEN}You can now run the restore script!${NC}"