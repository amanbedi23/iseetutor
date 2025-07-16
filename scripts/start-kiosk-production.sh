#!/bin/bash

# Production kiosk mode - assumes frontend is already built

# Disable screen blanking
export DISPLAY=:0
xset -dpms
xset s off
xset s noblank

# Start the API server with static file serving
cd /home/tutor/iseetutor
python3 - << 'EOF' &
import uvicorn
from src.api.main import app
from fastapi.staticfiles import StaticFiles

# Mount the React build directory
app.mount("/", StaticFiles(directory="frontend/build", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")
EOF
API_PID=$!

# Wait for server to be ready
echo "Waiting for server..."
while ! curl -s http://localhost:8000 > /dev/null 2>&1; do
    sleep 1
done
echo "Server ready!"

# Use Python to create a simple fullscreen webview
python3 - << 'EOF'
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, WebKit2, Gdk

class KioskWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="ISEE Tutor")
        self.fullscreen()
        self.connect("destroy", Gtk.main_quit)
        self.connect("realize", self.on_realize)
        
        # Create webview
        self.webview = WebKit2.WebView()
        self.webview.load_uri("http://localhost:8000")
        
        # Disable right-click menu
        self.webview.connect("context-menu", lambda w, cm, e, h: True)
        
        self.add(self.webview)
        self.show_all()
    
    def on_realize(self, widget):
        # Hide cursor after window is realized
        try:
            blank_cursor = Gdk.Cursor.new_for_display(self.get_display(), Gdk.CursorType.BLANK_CURSOR)
            self.get_window().set_cursor(blank_cursor)
        except:
            pass

win = KioskWindow()
Gtk.main()
EOF

# Keep script running
wait $API_PID