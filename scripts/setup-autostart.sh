#!/bin/bash
# Setup ISEE Tutor to auto-start on boot in kiosk mode

echo "Setting up ISEE Tutor auto-start..."

# Create systemd service for kiosk mode
sudo tee /etc/systemd/system/iseetutor-kiosk.service > /dev/null << 'EOF'
[Unit]
Description=ISEE Tutor Kiosk Mode
After=multi-user.target

[Service]
Type=simple
ExecStart=/home/tutor/iseetutor/scripts/start-kiosk-minimal.sh
Restart=always
User=tutor
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Create auto-login for tutor user
sudo mkdir -p /etc/systemd/system/getty@tty1.service.d/
sudo tee /etc/systemd/system/getty@tty1.service.d/override.conf > /dev/null << EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin tutor --noclear %I \$TERM
EOF

# Create .profile entry to start kiosk on login (backup method)
echo "# Auto-start ISEE Tutor Kiosk" >> /home/tutor/.profile
echo 'if [ -z "$DISPLAY" ] && [ "$XDG_VTNR" = 1 ]; then' >> /home/tutor/.profile
echo '    exec /home/tutor/iseetutor/scripts/start-kiosk-minimal.sh' >> /home/tutor/.profile
echo 'fi' >> /home/tutor/.profile

# Enable the service
sudo systemctl daemon-reload
sudo systemctl enable iseetutor-kiosk.service

echo
echo "Auto-start configured!"
echo "The system will now:"
echo "1. Boot to terminal (no desktop)"
echo "2. Auto-login as 'tutor' user"
echo "3. Start ISEE Tutor in kiosk mode"
echo
echo "To test without rebooting:"
echo "  sudo systemctl start iseetutor-kiosk.service"
echo
echo "To disable auto-start:"
echo "  sudo systemctl disable iseetutor-kiosk.service"