#!/usr/bin/env python3
"""
WS2812B LED Ring Control for Jetson Orin Nano
Requires: sudo pip3 install rpi-ws281x adafruit-circuitpython-neopixel
Note: Must run with sudo for GPIO access
"""

import time
import board
import neopixel
from enum import Enum

# Configuration
LED_COUNT = 16          # Number of LEDs in the ring
LED_PIN = board.D18     # GPIO 18 (Physical Pin 32)
LED_BRIGHTNESS = 0.3    # 0.0 to 1.0 (start low for safety)

class LEDPatterns(Enum):
    OFF = "off"
    SOLID = "solid"
    BREATHING = "breathing"
    SPINNER = "spinner"
    RAINBOW = "rainbow"
    PULSE = "pulse"
    THINKING = "thinking"
    SUCCESS = "success"
    ERROR = "error"

class WS2812BController:
    def __init__(self, pin=LED_PIN, count=LED_COUNT, brightness=LED_BRIGHTNESS):
        # Initialize NeoPixel
        self.pixels = neopixel.NeoPixel(
            pin, count, brightness=brightness, auto_write=False
        )
        self.led_count = count
        self.current_pattern = LEDPatterns.OFF
        
    def clear(self):
        """Turn off all LEDs"""
        self.pixels.fill((0, 0, 0))
        self.pixels.show()
        
    def set_brightness(self, brightness):
        """Set brightness (0.0 to 1.0)"""
        self.pixels.brightness = max(0.0, min(1.0, brightness))
        
    def solid_color(self, color):
        """Set all LEDs to a solid color"""
        self.pixels.fill(color)
        self.pixels.show()
        
    def breathing(self, color, speed=0.01):
        """Breathing effect"""
        base_brightness = self.pixels.brightness
        for i in range(100):
            brightness = (i / 100.0) * base_brightness
            self.pixels.brightness = brightness
            self.pixels.fill(color)
            self.pixels.show()
            time.sleep(speed)
        for i in range(100, 0, -1):
            brightness = (i / 100.0) * base_brightness
            self.pixels.brightness = brightness
            self.pixels.fill(color)
            self.pixels.show()
            time.sleep(speed)
        self.pixels.brightness = base_brightness
        
    def spinner(self, color, background=(0, 0, 0), speed=0.1):
        """Spinning effect"""
        for i in range(self.led_count):
            self.pixels.fill(background)
            # Create a trail effect
            for j in range(3):
                led_index = (i - j) % self.led_count
                fade = 1.0 - (j * 0.3)
                faded_color = tuple(int(c * fade) for c in color)
                self.pixels[led_index] = faded_color
            self.pixels.show()
            time.sleep(speed)
            
    def rainbow_cycle(self, speed=0.001):
        """Rainbow effect cycling through all LEDs"""
        for j in range(255):
            for i in range(self.led_count):
                pixel_index = (i * 256 // self.led_count) + j
                self.pixels[i] = self.wheel(pixel_index & 255)
            self.pixels.show()
            time.sleep(speed)
            
    def pulse(self, color, pulses=3, speed=0.1):
        """Quick pulse effect"""
        for _ in range(pulses):
            self.pixels.fill(color)
            self.pixels.show()
            time.sleep(speed)
            self.pixels.fill((0, 0, 0))
            self.pixels.show()
            time.sleep(speed)
            
    def thinking(self, speed=0.05):
        """Thinking pattern - gentle blue spinner"""
        self.spinner((0, 0, 100), speed=speed)
        
    def success(self):
        """Success pattern - green pulse"""
        self.pulse((0, 255, 0), pulses=2, speed=0.2)
        
    def error(self):
        """Error pattern - red pulse"""
        self.pulse((255, 0, 0), pulses=3, speed=0.1)
        
    def wheel(self, pos):
        """Generate rainbow colors across 0-255 positions"""
        if pos < 0 or pos > 255:
            r = g = b = 0
        elif pos < 85:
            r = int(pos * 3)
            g = int(255 - pos * 3)
            b = 0
        elif pos < 170:
            pos -= 85
            r = int(255 - pos * 3)
            g = 0
            b = int(pos * 3)
        else:
            pos -= 170
            r = 0
            g = int(pos * 3)
            b = int(255 - pos * 3)
        return (r, g, b)

# Test functions
def test_led_ring():
    """Test all LED patterns"""
    print("Testing WS2812B LED Ring...")
    
    # Initialize controller
    led = WS2812BController()
    
    try:
        print("1. Clear all LEDs")
        led.clear()
        time.sleep(1)
        
        print("2. Red solid")
        led.solid_color((255, 0, 0))
        time.sleep(2)
        
        print("3. Green solid")
        led.solid_color((0, 255, 0))
        time.sleep(2)
        
        print("4. Blue solid")
        led.solid_color((0, 0, 255))
        time.sleep(2)
        
        print("5. Breathing effect (blue)")
        led.breathing((0, 0, 255))
        
        print("6. Spinner effect (green)")
        for _ in range(3):
            led.spinner((0, 255, 0))
            
        print("7. Rainbow cycle")
        for _ in range(2):
            led.rainbow_cycle()
            
        print("8. Thinking pattern")
        for _ in range(5):
            led.thinking()
            
        print("9. Success pattern")
        led.success()
        time.sleep(1)
        
        print("10. Error pattern")
        led.error()
        time.sleep(1)
        
        print("Test complete! Clearing LEDs...")
        led.clear()
        
    except KeyboardInterrupt:
        print("\nTest interrupted")
        led.clear()
    except Exception as e:
        print(f"Error: {e}")
        led.clear()

if __name__ == "__main__":
    # Note: This script must be run with sudo
    print("WS2812B LED Ring Controller")
    print("Note: This script requires sudo privileges")
    print("Usage: sudo python3 ws2812b-led-control.py")
    test_led_ring()