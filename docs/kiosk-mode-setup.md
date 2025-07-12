# Kiosk Mode Setup for ISEE Tutor

This guide configures the Jetson to boot directly into the ISEE Tutor app, similar to Alexa devices.

## Overview

The setup will:
1. Hide Ubuntu boot messages with custom splash screen
2. Auto-login without password prompt
3. Launch directly into fullscreen app
4. Disable desktop environment and unnecessary services
5. Prevent user from exiting the app

## Step 1: Configure Plymouth Boot Splash

```bash
# Install Plymouth themes
sudo apt-get install plymouth-theme-ubuntu-logo plymouth-theme-ubuntu-text

# Create custom theme directory
sudo mkdir -p /usr/share/plymouth/themes/isee-tutor

# Create theme files (we'll add logo later)
sudo tee /usr/share/plymouth/themes/isee-tutor/isee-tutor.plymouth << EOF
[Plymouth Theme]
Name=ISEE Tutor
Description=ISEE Tutor Boot Screen
ModuleName=script

[script]
ImageDir=/usr/share/plymouth/themes/isee-tutor
ScriptFile=/usr/share/plymouth/themes/isee-tutor/isee-tutor.script
EOF

# Create simple script
sudo tee /usr/share/plymouth/themes/isee-tutor/isee-tutor.script << 'EOF'
Window.SetBackgroundTopColor(0.0, 0.0, 0.0);
Window.SetBackgroundBottomColor(0.0, 0.0, 0.0);

logo.image = Image("logo.png");
logo.sprite = Sprite(logo.image);
logo.x = Window.GetX() + Window.GetWidth()  / 2 - logo.image.GetWidth()  / 2;
logo.y = Window.GetY() + Window.GetHeight() / 2 - logo.image.GetHeight() / 2;
logo.sprite.SetPosition(logo.x, logo.y, 0);
EOF

# Set as default theme
sudo update-alternatives --install /usr/share/plymouth/themes/default.plymouth default.plymouth /usr/share/plymouth/themes/isee-tutor/isee-tutor.plymouth 100
sudo update-alternatives --config default.plymouth

# Update initramfs
sudo update-initramfs -u
```

## Step 2: Configure Auto-login

```bash
# Create override for GDM (if using GNOME)
sudo mkdir -p /etc/systemd/system/getty@tty1.service.d/
sudo tee /etc/systemd/system/getty@tty1.service.d/override.conf << EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin tutor --noclear %I \$TERM
EOF

# For LightDM (lighter alternative)
sudo apt-get install lightdm
sudo tee /etc/lightdm/lightdm.conf << EOF
[Seat:*]
autologin-user=tutor
autologin-user-timeout=0
user-session=isee-tutor
EOF
```

## Step 3: Create Minimal X Session

```bash
# Create custom X session
sudo tee /usr/share/xsessions/isee-tutor.desktop << EOF
[Desktop Entry]
Name=ISEE Tutor Kiosk
Comment=ISEE Tutor Kiosk Mode
Exec=/home/tutor/iseetutor/scripts/start-kiosk.sh
Type=Application
EOF

# Create kiosk startup script
mkdir -p /home/tutor/iseetutor/scripts
tee /home/tutor/iseetutor/scripts/start-kiosk.sh << 'EOF'
#!/bin/bash

# Disable screen blanking and power management
xset -dpms
xset s off
xset s noblank

# Hide cursor after 3 seconds of inactivity
unclutter -idle 3 &

# Disable right-click context menu
xmodmap -e "pointer = 1 2 99 4 5 6 7 8 9"

# Start the API server in background
cd /home/tutor/iseetutor
python3 start_api.py &
API_PID=$!

# Wait for API to be ready
while ! curl -s http://localhost:8000/health > /dev/null; do
    sleep 1
done

# Start the React frontend
cd /home/tutor/iseetutor/frontend
npm start &
FRONTEND_PID=$!

# Wait for frontend to be ready
while ! curl -s http://localhost:3000 > /dev/null; do
    sleep 1
done

# Launch Chromium in kiosk mode
chromium-browser \
    --kiosk \
    --no-first-run \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-features=TranslateUI \
    --disable-pinch \
    --overscroll-history-navigation=0 \
    --disable-features=OverscrollHistoryNavigation \
    --app=http://localhost:3000 &

# If Chromium crashes, restart it
while true; do
    if ! pgrep chromium > /dev/null; then
        chromium-browser \
            --kiosk \
            --no-first-run \
            --disable-infobars \
            --app=http://localhost:3000 &
    fi
    sleep 5
done
EOF

chmod +x /home/tutor/iseetutor/scripts/start-kiosk.sh
```

## Step 4: Disable Unnecessary Services

```bash
# Disable desktop environment services
sudo systemctl disable gdm3 # or lightdm if using that
sudo systemctl disable NetworkManager-wait-online.service
sudo systemctl disable apt-daily.service
sudo systemctl disable apt-daily-upgrade.service

# Create minimal systemd service for kiosk
sudo tee /etc/systemd/system/isee-tutor-kiosk.service << EOF
[Unit]
Description=ISEE Tutor Kiosk Mode
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/bin/startx /home/tutor/iseetutor/scripts/start-kiosk.sh -- -nocursor
Restart=always
User=tutor
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=graphical.target
EOF

sudo systemctl enable isee-tutor-kiosk.service
```

## Step 5: Performance Optimizations

```bash
# Reduce boot time by disabling unnecessary services
sudo systemctl disable bluetooth.service
sudo systemctl disable cups.service
sudo systemctl disable avahi-daemon.service

# Set kernel parameters for faster boot
sudo tee -a /etc/default/grub << EOF
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash loglevel=0 rd.systemd.show_status=0 rd.udev.log_priority=0 vt.global_cursor_default=0"
GRUB_TIMEOUT=0
GRUB_HIDDEN_TIMEOUT=0
EOF

sudo update-grub
```

## Step 6: Frontend Considerations

For the React app, we'll need to:

1. **Full-screen responsive design**
   - No window chrome or browser UI
   - Touch-optimized interface
   - Handle all screen sizes

2. **Offline-first PWA**
   - Service workers for offline functionality
   - Local storage for user data
   - No external dependencies

3. **Kiosk-specific features**
   - Disable right-click
   - Prevent navigation away
   - Auto-recovery from crashes

## Alternative: Electron App

Instead of Chromium kiosk, consider Electron:

```javascript
// main.js
const { app, BrowserWindow } = require('electron')

function createWindow() {
  const win = new BrowserWindow({
    fullscreen: true,
    kiosk: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  })

  win.loadURL('http://localhost:3000')
  
  // Prevent app from closing
  win.on('closed', () => {
    createWindow()
  })
}

app.whenReady().then(createWindow)
```

## Testing Kiosk Mode

```bash
# Test without rebooting
sudo systemctl stop gdm3
sudo systemctl start isee-tutor-kiosk

# View logs
journalctl -u isee-tutor-kiosk -f
```

## Reverting to Normal Mode

```bash
# Re-enable desktop
sudo systemctl disable isee-tutor-kiosk
sudo systemctl enable gdm3
sudo reboot
```

## Security Considerations

1. **Disable TTY switching**: Prevent Ctrl+Alt+F* keys
2. **Disable Alt+Tab**: Window switching
3. **Password-protect GRUB**: Prevent boot modifications
4. **Read-only filesystem**: For production devices

## Next Steps

1. Design boot logo/animation
2. Create React app with kiosk-specific features
3. Test on actual hardware with touchscreen
4. Implement watchdog for auto-recovery