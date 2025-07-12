#!/usr/bin/env python3
"""
Mock hardware classes for development without physical hardware.

These classes simulate the behavior of hardware components (LEDs, buttons, GPIO)
allowing development and testing on non-Jetson systems.
"""

import time
import logging
import threading
from typing import Optional, Callable, Tuple, Dict, Any
from enum import Enum
from dataclasses import dataclass


logger = logging.getLogger(__name__)


class LEDPatterns(Enum):
    """LED pattern definitions matching the actual hardware"""
    OFF = "off"
    SOLID = "solid"
    BREATHING = "breathing"
    SPINNER = "spinner"
    RAINBOW = "rainbow"
    PULSE = "pulse"
    THINKING = "thinking"
    SUCCESS = "success"
    ERROR = "error"
    LISTENING = "listening"
    SPEAKING = "speaking"


@dataclass
class MockLEDState:
    """Track the current state of mock LEDs"""
    pattern: LEDPatterns = LEDPatterns.OFF
    color: Tuple[int, int, int] = (0, 0, 0)
    brightness: float = 0.3
    pixels: list = None
    
    def __post_init__(self):
        if self.pixels is None:
            self.pixels = [(0, 0, 0)] * 16  # Default 16 LEDs


class MockWS2812BController:
    """
    Mock implementation of WS2812B LED controller.
    
    Simulates LED operations by logging actions and maintaining state.
    """
    
    def __init__(self, pin=None, count=16, brightness=0.3):
        """Initialize mock LED controller"""
        self.led_count = count
        self.state = MockLEDState(
            brightness=brightness,
            pixels=[(0, 0, 0)] * count
        )
        self.running = False
        self.pattern_thread = None
        
        logger.info(f"MockWS2812BController initialized with {count} LEDs, brightness={brightness}")
        
    def clear(self):
        """Turn off all LEDs"""
        self.stop_pattern()
        self.state.pixels = [(0, 0, 0)] * self.led_count
        self.state.pattern = LEDPatterns.OFF
        self.state.color = (0, 0, 0)
        logger.debug("LEDs cleared")
        
    def set_brightness(self, brightness: float):
        """Set brightness (0.0 to 1.0)"""
        self.state.brightness = max(0.0, min(1.0, brightness))
        logger.debug(f"Brightness set to {self.state.brightness}")
        
    def solid_color(self, color: Tuple[int, int, int]):
        """Set all LEDs to a solid color"""
        self.stop_pattern()
        self.state.pixels = [color] * self.led_count
        self.state.pattern = LEDPatterns.SOLID
        self.state.color = color
        logger.info(f"LEDs set to solid color: RGB{color}")
        
    def breathing(self, color: Tuple[int, int, int], speed: float = 0.01):
        """Simulate breathing effect"""
        self.stop_pattern()
        self.state.pattern = LEDPatterns.BREATHING
        self.state.color = color
        logger.info(f"Breathing effect started with color RGB{color}, speed={speed}")
        
        def _breathing_loop():
            while self.running:
                # Simulate breathing by logging brightness changes
                for i in range(0, 100, 10):
                    if not self.running:
                        break
                    brightness = (i / 100.0) * self.state.brightness
                    logger.debug(f"Breathing: brightness={brightness:.2f}")
                    time.sleep(speed)
                for i in range(100, 0, -10):
                    if not self.running:
                        break
                    brightness = (i / 100.0) * self.state.brightness
                    logger.debug(f"Breathing: brightness={brightness:.2f}")
                    time.sleep(speed)
        
        self._start_pattern(_breathing_loop)
        
    def spinner(self, color: Tuple[int, int, int], background: Tuple[int, int, int] = (0, 0, 0), speed: float = 0.1):
        """Simulate spinning effect"""
        self.stop_pattern()
        self.state.pattern = LEDPatterns.SPINNER
        self.state.color = color
        logger.info(f"Spinner effect started with color RGB{color}, speed={speed}")
        
        def _spinner_loop():
            position = 0
            while self.running:
                # Simulate spinner position
                logger.debug(f"Spinner at position {position}/{self.led_count}")
                position = (position + 1) % self.led_count
                time.sleep(speed)
        
        self._start_pattern(_spinner_loop)
        
    def rainbow_cycle(self, speed: float = 0.001):
        """Simulate rainbow effect"""
        self.stop_pattern()
        self.state.pattern = LEDPatterns.RAINBOW
        logger.info(f"Rainbow cycle started with speed={speed}")
        
        def _rainbow_loop():
            hue = 0
            while self.running:
                logger.debug(f"Rainbow: hue={hue}")
                hue = (hue + 1) % 360
                time.sleep(speed * 255)  # Approximate timing
        
        self._start_pattern(_rainbow_loop)
        
    def pulse(self, color: Tuple[int, int, int], pulses: int = 3, speed: float = 0.1):
        """Simulate pulse effect"""
        self.stop_pattern()
        self.state.pattern = LEDPatterns.PULSE
        self.state.color = color
        logger.info(f"Pulse effect: {pulses} pulses of RGB{color}")
        
        for i in range(pulses):
            logger.debug(f"Pulse {i+1}/{pulses}: ON")
            self.state.pixels = [color] * self.led_count
            time.sleep(speed)
            logger.debug(f"Pulse {i+1}/{pulses}: OFF")
            self.state.pixels = [(0, 0, 0)] * self.led_count
            time.sleep(speed)
            
    def thinking(self, speed: float = 0.05):
        """Thinking pattern - gentle blue spinner"""
        logger.info("Thinking pattern started")
        self.spinner((0, 0, 100), speed=speed)
        
    def success(self):
        """Success pattern - green pulse"""
        logger.info("Success pattern")
        self.pulse((0, 255, 0), pulses=2, speed=0.2)
        
    def error(self):
        """Error pattern - red pulse"""
        logger.info("Error pattern")
        self.pulse((255, 0, 0), pulses=3, speed=0.1)
        
    def listening(self):
        """Listening pattern - cyan breathing"""
        logger.info("Listening pattern started")
        self.breathing((0, 255, 255), speed=0.02)
        
    def speaking(self):
        """Speaking pattern - orange spinner"""
        logger.info("Speaking pattern started")
        self.spinner((255, 165, 0), speed=0.08)
        
    def _start_pattern(self, pattern_func: Callable):
        """Start a pattern in a background thread"""
        self.running = True
        self.pattern_thread = threading.Thread(target=pattern_func, daemon=True)
        self.pattern_thread.start()
        
    def stop_pattern(self):
        """Stop any running pattern"""
        self.running = False
        if self.pattern_thread and self.pattern_thread.is_alive():
            self.pattern_thread.join(timeout=0.5)
            
    def get_state(self) -> Dict[str, Any]:
        """Get current LED state for debugging"""
        return {
            "pattern": self.state.pattern.value,
            "color": self.state.color,
            "brightness": self.state.brightness,
            "pixel_summary": f"First pixel: RGB{self.state.pixels[0]}" if self.state.pixels else "No pixels"
        }


class MockButton:
    """
    Mock implementation of a GPIO button.
    
    Simulates button presses and callbacks.
    """
    
    def __init__(self, pin: int, pull_up: bool = True, bounce_time: int = 200):
        """Initialize mock button"""
        self.pin = pin
        self.pull_up = pull_up
        self.bounce_time = bounce_time
        self.callbacks = []
        self.pressed = False
        self.enabled = True
        
        logger.info(f"MockButton initialized on pin {pin}, pull_up={pull_up}, bounce_time={bounce_time}ms")
        
    def add_callback(self, callback: Callable, edge: str = "falling"):
        """Add a callback for button events"""
        self.callbacks.append((callback, edge))
        logger.debug(f"Added callback for {edge} edge on pin {self.pin}")
        
    def simulate_press(self, duration: float = 0.1):
        """Simulate a button press"""
        if not self.enabled:
            logger.warning("Button disabled, ignoring press")
            return
            
        logger.info(f"Button {self.pin} pressed (simulated)")
        self.pressed = True
        
        # Trigger falling edge callbacks
        for callback, edge in self.callbacks:
            if edge in ["falling", "both"]:
                callback(self.pin)
                
        # Simulate hold duration
        time.sleep(duration)
        
        self.pressed = False
        logger.info(f"Button {self.pin} released (simulated)")
        
        # Trigger rising edge callbacks
        for callback, edge in self.callbacks:
            if edge in ["rising", "both"]:
                callback(self.pin)
                
    def simulate_long_press(self, duration: float = 2.0):
        """Simulate a long button press"""
        logger.info(f"Button {self.pin} long press started (simulated)")
        self.simulate_press(duration)
        
    def is_pressed(self) -> bool:
        """Check if button is currently pressed"""
        return self.pressed
        
    def enable(self):
        """Enable the button"""
        self.enabled = True
        logger.debug(f"Button {self.pin} enabled")
        
    def disable(self):
        """Disable the button"""
        self.enabled = False
        logger.debug(f"Button {self.pin} disabled")


class MockGPIO:
    """
    Mock implementation of GPIO interface.
    
    Provides a compatible interface for GPIO operations without hardware.
    """
    
    # Pin modes
    IN = "in"
    OUT = "out"
    
    # Pull resistors
    PUD_UP = "pull_up"
    PUD_DOWN = "pull_down"
    PUD_OFF = "pull_off"
    
    # Edge detection
    RISING = "rising"
    FALLING = "falling"
    BOTH = "both"
    
    # Pin numbering
    BCM = "bcm"
    BOARD = "board"
    
    def __init__(self):
        """Initialize mock GPIO"""
        self.mode = None
        self.pins = {}
        self.warnings = True
        logger.info("MockGPIO initialized")
        
    def setmode(self, mode: str):
        """Set pin numbering mode"""
        self.mode = mode
        logger.debug(f"GPIO mode set to {mode}")
        
    def setwarnings(self, warnings: bool):
        """Enable/disable warnings"""
        self.warnings = warnings
        logger.debug(f"GPIO warnings set to {warnings}")
        
    def setup(self, pin: int, mode: str, pull_up_down: Optional[str] = None):
        """Setup a GPIO pin"""
        self.pins[pin] = {
            "mode": mode,
            "pull": pull_up_down,
            "value": 0 if mode == self.OUT else 1 if pull_up_down == self.PUD_UP else 0,
            "callbacks": []
        }
        logger.debug(f"Pin {pin} configured as {mode}, pull={pull_up_down}")
        
    def output(self, pin: int, value: int):
        """Set output pin value"""
        if pin in self.pins and self.pins[pin]["mode"] == self.OUT:
            self.pins[pin]["value"] = value
            logger.debug(f"Pin {pin} output set to {value}")
        else:
            logger.warning(f"Pin {pin} not configured as output")
            
    def input(self, pin: int) -> int:
        """Read input pin value"""
        if pin in self.pins:
            value = self.pins[pin]["value"]
            logger.debug(f"Pin {pin} input read as {value}")
            return value
        logger.warning(f"Pin {pin} not configured")
        return 0
        
    def add_event_detect(self, pin: int, edge: str, callback: Optional[Callable] = None, bouncetime: int = 200):
        """Add edge detection to a pin"""
        if pin in self.pins:
            self.pins[pin]["edge"] = edge
            self.pins[pin]["bouncetime"] = bouncetime
            if callback:
                self.pins[pin]["callbacks"].append(callback)
            logger.debug(f"Edge detection added to pin {pin}: {edge}, bounce={bouncetime}ms")
        else:
            logger.warning(f"Pin {pin} not configured")
            
    def remove_event_detect(self, pin: int):
        """Remove edge detection from a pin"""
        if pin in self.pins:
            self.pins[pin].pop("edge", None)
            self.pins[pin]["callbacks"] = []
            logger.debug(f"Edge detection removed from pin {pin}")
            
    def cleanup(self, pins: Optional[list] = None):
        """Cleanup GPIO resources"""
        if pins:
            for pin in pins:
                self.pins.pop(pin, None)
            logger.debug(f"Cleaned up pins: {pins}")
        else:
            self.pins.clear()
            logger.debug("All GPIO pins cleaned up")
            
    def simulate_pin_change(self, pin: int, value: int):
        """Simulate a pin state change (for testing)"""
        if pin in self.pins:
            old_value = self.pins[pin]["value"]
            self.pins[pin]["value"] = value
            
            # Trigger callbacks if edge detected
            if "edge" in self.pins[pin]:
                edge = self.pins[pin]["edge"]
                if (edge == self.RISING and value > old_value) or \
                   (edge == self.FALLING and value < old_value) or \
                   (edge == self.BOTH and value != old_value):
                    for callback in self.pins[pin]["callbacks"]:
                        callback(pin)
                    logger.info(f"Pin {pin} edge detected: {old_value} -> {value}")


# Convenience function to get appropriate hardware class
def get_hardware_interface(hardware_type: str, mock: bool = True, **kwargs):
    """
    Get appropriate hardware interface (mock or real).
    
    Args:
        hardware_type: Type of hardware ("led", "button", "gpio")
        mock: Whether to use mock implementation
        **kwargs: Arguments to pass to hardware constructor
        
    Returns:
        Hardware interface instance
    """
    if mock:
        if hardware_type == "led":
            return MockWS2812BController(**kwargs)
        elif hardware_type == "button":
            return MockButton(**kwargs)
        elif hardware_type == "gpio":
            return MockGPIO()
        else:
            raise ValueError(f"Unknown hardware type: {hardware_type}")
    else:
        # Import real hardware classes when not mocking
        if hardware_type == "led":
            from .ws2812b_led_control import WS2812BController
            return WS2812BController(**kwargs)
        elif hardware_type == "button":
            # TODO: Implement real button class when hardware is available
            logger.warning("Real button hardware not implemented, using mock")
            return MockButton(**kwargs)
        elif hardware_type == "gpio":
            try:
                import Jetson.GPIO as GPIO
                return GPIO
            except ImportError:
                logger.warning("Jetson.GPIO not available, using mock")
                return MockGPIO()
        else:
            raise ValueError(f"Unknown hardware type: {hardware_type}")


# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Testing Mock Hardware Classes\n")
    
    # Test LED controller
    print("1. Testing LED Controller")
    led = MockWS2812BController(count=16)
    
    print("   - Solid red")
    led.solid_color((255, 0, 0))
    time.sleep(1)
    
    print("   - Thinking pattern")
    led.thinking()
    time.sleep(2)
    led.stop_pattern()
    
    print("   - Success pattern")
    led.success()
    
    print("   - LED State:", led.get_state())
    print()
    
    # Test Button
    print("2. Testing Button")
    button = MockButton(pin=18)
    
    def button_callback(pin):
        print(f"   - Button {pin} pressed!")
    
    button.add_callback(button_callback, edge="falling")
    
    print("   - Simulating button press")
    button.simulate_press()
    
    print("   - Simulating long press")
    button.simulate_long_press(duration=1.0)
    print()
    
    # Test GPIO
    print("3. Testing GPIO")
    gpio = MockGPIO()
    gpio.setmode(gpio.BCM)
    
    # Setup output pin
    gpio.setup(23, gpio.OUT)
    gpio.output(23, 1)
    
    # Setup input pin with callback
    gpio.setup(24, gpio.IN, pull_up_down=gpio.PUD_UP)
    
    def gpio_callback(pin):
        print(f"   - GPIO {pin} edge detected!")
    
    gpio.add_event_detect(24, gpio.FALLING, callback=gpio_callback)
    
    print("   - Simulating pin change")
    gpio.simulate_pin_change(24, 0)  # Falling edge
    
    print("   - Cleaning up")
    gpio.cleanup()
    
    print("\nMock hardware testing complete!")