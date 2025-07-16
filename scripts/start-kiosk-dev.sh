#!/bin/bash

# Development kiosk mode - runs React dev server and API separately

# Disable screen blanking
export DISPLAY=:0
xset -dpms
xset s off
xset s noblank

# Start the API server
cd /home/tutor/iseetutor
python3 start_api.py &
API_PID=$!

# Start the React dev server
cd /home/tutor/iseetutor/frontend
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Start React on port 3000
PORT=3000 BROWSER=none npm start &
FRONTEND_PID=$!

# Wait for API to be ready
echo "Waiting for API server..."
while ! curl -s http://localhost:8000/health > /dev/null 2>&1; do
    sleep 1
done
echo "API server ready!"

# Wait for frontend to be ready
echo "Waiting for React dev server..."
while ! curl -s http://localhost:3000 > /dev/null 2>&1; do
    sleep 2
done
echo "React dev server ready!"

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
        self.webview.load_uri("http://localhost:3000")
        
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

# Cleanup on exit
trap "kill $API_PID $FRONTEND_PID" EXIT
wait