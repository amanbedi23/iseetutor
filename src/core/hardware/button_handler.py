#!/usr/bin/env python3
"""
Button handler for ISEE Tutor.

Manages physical button input with support for different press types
(short press, long press, double press) and provides a high-level
interface for button actions.
"""

import logging
import time
import threading
from typing import Optional, Callable, Dict, Any, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta

from .mock_hardware import get_hardware_interface


logger = logging.getLogger(__name__)


class ButtonEvent(Enum):
    """Types of button events"""
    PRESS = "press"
    RELEASE = "release"
    SHORT_PRESS = "short_press"
    LONG_PRESS = "long_press"
    DOUBLE_PRESS = "double_press"
    TRIPLE_PRESS = "triple_press"
    HOLD_START = "hold_start"
    HOLD_END = "hold_end"


@dataclass
class ButtonPress:
    """Record of a button press"""
    timestamp: datetime
    duration: float = 0.0
    event_type: ButtonEvent = ButtonEvent.PRESS


class ButtonHandler:
    """
    High-level button handler with support for various press patterns.
    
    Features:
    - Short press detection
    - Long press detection (configurable threshold)
    - Double/triple press detection
    - Hold detection with callbacks
    - Debouncing
    """
    
    # Default timing configurations (in seconds)
    DEFAULT_LONG_PRESS_TIME = 1.0
    DEFAULT_DOUBLE_PRESS_TIME = 0.5
    DEFAULT_DEBOUNCE_TIME = 0.05
    
    def __init__(
        self,
        pin: int,
        mock: bool = True,
        long_press_time: float = DEFAULT_LONG_PRESS_TIME,
        double_press_time: float = DEFAULT_DOUBLE_PRESS_TIME,
        debounce_time: float = DEFAULT_DEBOUNCE_TIME
    ):
        """
        Initialize button handler.
        
        Args:
            pin: GPIO pin number for the button
            mock: Use mock hardware interface
            long_press_time: Time threshold for long press
            double_press_time: Maximum time between presses for multi-press
            debounce_time: Debounce time to ignore noise
        """
        self.pin = pin
        self.mock = mock
        self.long_press_time = long_press_time
        self.double_press_time = double_press_time
        self.debounce_time = debounce_time
        
        # State tracking
        self.press_start_time: Optional[datetime] = None
        self.last_release_time: Optional[datetime] = None
        self.press_count = 0
        self.is_pressed = False
        self.hold_triggered = False
        
        # Callbacks
        self.callbacks: Dict[ButtonEvent, List[Callable]] = {
            event: [] for event in ButtonEvent
        }
        
        # Threading
        self._lock = threading.Lock()
        self._hold_timer: Optional[threading.Timer] = None
        self._multi_press_timer: Optional[threading.Timer] = None
        
        # Initialize hardware
        self.button = get_hardware_interface(
            "button",
            mock=mock,
            pin=pin,
            pull_up=True,
            bounce_time=int(debounce_time * 1000)  # Convert to ms
        )
        
        # Set up hardware callbacks
        self.button.add_callback(self._on_press, edge="falling")
        self.button.add_callback(self._on_release, edge="rising")
        
        logger.info(f"ButtonHandler initialized on pin {pin} (mock={mock})")
        
    def add_handler(self, event: ButtonEvent, callback: Callable):
        """
        Add a callback for a specific button event.
        
        Args:
            event: Button event type
            callback: Function to call when event occurs
        """
        self.callbacks[event].append(callback)
        logger.debug(f"Added handler for {event.value}")
        
    def remove_handler(self, event: ButtonEvent, callback: Callable):
        """Remove a callback for a specific button event"""
        if callback in self.callbacks[event]:
            self.callbacks[event].remove(callback)
            logger.debug(f"Removed handler for {event.value}")
            
    def _trigger_event(self, event: ButtonEvent, **kwargs):
        """Trigger callbacks for an event"""
        logger.info(f"Button event: {event.value}")
        for callback in self.callbacks[event]:
            try:
                callback(event, **kwargs)
            except Exception as e:
                logger.error(f"Error in button callback: {e}")
                
    def _on_press(self, pin: int):
        """Handle button press (falling edge)"""
        with self._lock:
            current_time = datetime.now()
            
            # Debounce check
            if self.is_pressed:
                return
                
            self.is_pressed = True
            self.press_start_time = current_time
            self.hold_triggered = False
            
            # Cancel any pending multi-press timer
            if self._multi_press_timer:
                self._multi_press_timer.cancel()
                
            # Trigger press event
            self._trigger_event(ButtonEvent.PRESS)
            
            # Start hold detection timer
            self._hold_timer = threading.Timer(
                self.long_press_time,
                self._on_hold_threshold
            )
            self._hold_timer.start()
            
    def _on_release(self, pin: int):
        """Handle button release (rising edge)"""
        with self._lock:
            if not self.is_pressed:
                return
                
            current_time = datetime.now()
            self.is_pressed = False
            
            # Cancel hold timer if running
            if self._hold_timer:
                self._hold_timer.cancel()
                
            # Calculate press duration
            if self.press_start_time:
                duration = (current_time - self.press_start_time).total_seconds()
            else:
                duration = 0
                
            # Trigger release event
            self._trigger_event(ButtonEvent.RELEASE, duration=duration)
            
            # Handle hold end if it was triggered
            if self.hold_triggered:
                self._trigger_event(ButtonEvent.HOLD_END, duration=duration)
                self.press_count = 0  # Reset for next press
            else:
                # Not a hold, check for short/long press
                if duration >= self.long_press_time:
                    self._trigger_event(ButtonEvent.LONG_PRESS, duration=duration)
                    self.press_count = 0  # Reset for next press
                else:
                    # Short press - check for multi-press
                    self.press_count += 1
                    
                    # Set timer to finalize press count
                    self._multi_press_timer = threading.Timer(
                        self.double_press_time,
                        self._finalize_press_count
                    )
                    self._multi_press_timer.start()
                    
            self.last_release_time = current_time
            
    def _on_hold_threshold(self):
        """Called when button is held past the long press threshold"""
        with self._lock:
            if self.is_pressed and not self.hold_triggered:
                self.hold_triggered = True
                self._trigger_event(ButtonEvent.HOLD_START)
                
    def _finalize_press_count(self):
        """Finalize the press count and trigger appropriate event"""
        with self._lock:
            if self.press_count == 1:
                self._trigger_event(ButtonEvent.SHORT_PRESS)
            elif self.press_count == 2:
                self._trigger_event(ButtonEvent.DOUBLE_PRESS)
            elif self.press_count >= 3:
                self._trigger_event(ButtonEvent.TRIPLE_PRESS, count=self.press_count)
                
            self.press_count = 0
            
    def simulate_press(self, duration: float = 0.1):
        """
        Simulate a button press (for testing).
        
        Args:
            duration: How long to hold the button
        """
        if self.mock and hasattr(self.button, 'simulate_press'):
            self.button.simulate_press(duration)
        else:
            logger.warning("Simulate press only available in mock mode")
            
    def get_status(self) -> Dict[str, Any]:
        """Get current button status"""
        with self._lock:
            return {
                "pin": self.pin,
                "is_pressed": self.is_pressed,
                "press_count": self.press_count,
                "mock_mode": self.mock,
                "handlers": {
                    event.value: len(callbacks)
                    for event, callbacks in self.callbacks.items()
                }
            }


class TutorButtonManager:
    """
    High-level button manager for ISEE Tutor functionality.
    
    Maps button events to tutor actions like mode switching,
    volume control, etc.
    """
    
    def __init__(self, button_pin: int = 18, mock: bool = True):
        """
        Initialize tutor button manager.
        
        Args:
            button_pin: GPIO pin for the main button
            mock: Use mock hardware
        """
        self.button_handler = ButtonHandler(pin=button_pin, mock=mock)
        
        # State
        self.current_mode = "companion"  # companion or tutor
        self.is_muted = False
        self.callbacks = {
            "mode_change": [],
            "mute_toggle": [],
            "emergency_stop": [],
            "wake_word_trigger": []
        }
        
        # Set up button event handlers
        self._setup_handlers()
        
        logger.info(f"TutorButtonManager initialized (pin={button_pin}, mock={mock})")
        
    def _setup_handlers(self):
        """Set up button event handlers"""
        # Short press - trigger wake word / pause
        self.button_handler.add_handler(
            ButtonEvent.SHORT_PRESS,
            self._on_short_press
        )
        
        # Double press - toggle mode
        self.button_handler.add_handler(
            ButtonEvent.DOUBLE_PRESS,
            self._on_double_press
        )
        
        # Long press - mute/unmute
        self.button_handler.add_handler(
            ButtonEvent.LONG_PRESS,
            self._on_long_press
        )
        
        # Triple press - emergency stop
        self.button_handler.add_handler(
            ButtonEvent.TRIPLE_PRESS,
            self._on_triple_press
        )
        
    def _on_short_press(self, event: ButtonEvent, **kwargs):
        """Handle short press - trigger wake word"""
        logger.info("Short press: Triggering wake word")
        self._trigger_callbacks("wake_word_trigger")
        
    def _on_double_press(self, event: ButtonEvent, **kwargs):
        """Handle double press - toggle mode"""
        old_mode = self.current_mode
        self.current_mode = "tutor" if self.current_mode == "companion" else "companion"
        logger.info(f"Double press: Mode changed from {old_mode} to {self.current_mode}")
        self._trigger_callbacks("mode_change", old_mode=old_mode, new_mode=self.current_mode)
        
    def _on_long_press(self, event: ButtonEvent, **kwargs):
        """Handle long press - toggle mute"""
        self.is_muted = not self.is_muted
        logger.info(f"Long press: Mute toggled to {self.is_muted}")
        self._trigger_callbacks("mute_toggle", is_muted=self.is_muted)
        
    def _on_triple_press(self, event: ButtonEvent, **kwargs):
        """Handle triple press - emergency stop"""
        logger.warning("Triple press: Emergency stop triggered!")
        self._trigger_callbacks("emergency_stop")
        
    def add_callback(self, action: str, callback: Callable):
        """Add callback for tutor actions"""
        if action in self.callbacks:
            self.callbacks[action].append(callback)
            logger.debug(f"Added callback for {action}")
        else:
            logger.warning(f"Unknown action: {action}")
            
    def _trigger_callbacks(self, action: str, **kwargs):
        """Trigger callbacks for an action"""
        for callback in self.callbacks.get(action, []):
            try:
                callback(**kwargs)
            except Exception as e:
                logger.error(f"Error in {action} callback: {e}")
                
    def get_status(self) -> Dict[str, Any]:
        """Get current status"""
        return {
            "button_status": self.button_handler.get_status(),
            "current_mode": self.current_mode,
            "is_muted": self.is_muted
        }


# Example usage and testing
if __name__ == "__main__":
    import sys
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Button Handler Test")
    print("-" * 40)
    
    # Create button handler
    button = ButtonHandler(pin=18, mock=True)
    
    # Add event handlers
    def on_event(event: ButtonEvent, **kwargs):
        print(f"Event: {event.value}", kwargs if kwargs else "")
    
    for event in ButtonEvent:
        button.add_handler(event, on_event)
    
    # Test tutor button manager
    print("\nTesting TutorButtonManager:")
    manager = TutorButtonManager(mock=True)
    
    # Add callbacks
    def on_mode_change(old_mode, new_mode):
        print(f"Mode changed: {old_mode} -> {new_mode}")
    
    def on_mute_toggle(is_muted):
        print(f"Mute toggled: {'ON' if is_muted else 'OFF'}")
    
    def on_wake_word():
        print("Wake word triggered!")
    
    def on_emergency_stop():
        print("EMERGENCY STOP!")
    
    manager.add_callback("mode_change", on_mode_change)
    manager.add_callback("mute_toggle", on_mute_toggle)
    manager.add_callback("wake_word_trigger", on_wake_word)
    manager.add_callback("emergency_stop", on_emergency_stop)
    
    # Interactive test
    print("\nInteractive test:")
    print("Commands:")
    print("  s: Simulate short press")
    print("  l: Simulate long press")
    print("  d: Simulate double press")
    print("  t: Simulate triple press")
    print("  h: Simulate hold (3 seconds)")
    print("  q: Quit")
    
    try:
        while True:
            cmd = input("\nEnter command: ").strip().lower()
            
            if cmd == 'q':
                break
            elif cmd == 's':
                print("Simulating short press...")
                button.simulate_press(0.1)
            elif cmd == 'l':
                print("Simulating long press...")
                button.simulate_press(1.5)
            elif cmd == 'd':
                print("Simulating double press...")
                button.simulate_press(0.1)
                time.sleep(0.2)
                button.simulate_press(0.1)
            elif cmd == 't':
                print("Simulating triple press...")
                for _ in range(3):
                    button.simulate_press(0.1)
                    time.sleep(0.2)
            elif cmd == 'h':
                print("Simulating hold...")
                button.simulate_press(3.0)
            else:
                print("Unknown command")
                
            # Give time for events to process
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        pass
    
    print("\nTest complete!")
    print("Status:", manager.get_status())