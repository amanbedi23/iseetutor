#!/usr/bin/env python3
"""
LED pattern definitions and controller for ISEE Tutor.

This module provides a high-level interface for LED patterns that can work
with both real hardware (WS2812B) and mock implementations.
"""

import logging
import threading
import time
from typing import Optional, Dict, Any, Callable
from enum import Enum

from .mock_hardware import get_hardware_interface, LEDPatterns


logger = logging.getLogger(__name__)


class TutorState(Enum):
    """High-level tutor states that map to LED patterns"""
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    SUCCESS = "success"
    ERROR = "error"
    LEARNING = "learning"
    QUIZ = "quiz"
    CELEBRATION = "celebration"
    LOW_BATTERY = "low_battery"
    STARTUP = "startup"
    SHUTDOWN = "shutdown"


# Mapping of tutor states to LED patterns and colors
STATE_TO_PATTERN = {
    TutorState.IDLE: {
        "pattern": LEDPatterns.BREATHING,
        "color": (0, 0, 100),  # Gentle blue
        "speed": 0.03
    },
    TutorState.LISTENING: {
        "pattern": LEDPatterns.BREATHING,
        "color": (0, 255, 255),  # Cyan
        "speed": 0.02
    },
    TutorState.THINKING: {
        "pattern": LEDPatterns.SPINNER,
        "color": (0, 0, 255),  # Blue
        "speed": 0.05
    },
    TutorState.SPEAKING: {
        "pattern": LEDPatterns.SPINNER,
        "color": (255, 165, 0),  # Orange
        "speed": 0.08
    },
    TutorState.SUCCESS: {
        "pattern": LEDPatterns.SUCCESS,
        "color": (0, 255, 0)  # Green
    },
    TutorState.ERROR: {
        "pattern": LEDPatterns.ERROR,
        "color": (255, 0, 0)  # Red
    },
    TutorState.LEARNING: {
        "pattern": LEDPatterns.RAINBOW,
        "speed": 0.002
    },
    TutorState.QUIZ: {
        "pattern": LEDPatterns.PULSE,
        "color": (255, 255, 0),  # Yellow
        "pulses": 2,
        "speed": 0.3
    },
    TutorState.CELEBRATION: {
        "pattern": LEDPatterns.RAINBOW,
        "speed": 0.001
    },
    TutorState.LOW_BATTERY: {
        "pattern": LEDPatterns.PULSE,
        "color": (255, 0, 0),  # Red
        "pulses": 1,
        "speed": 1.0
    },
    TutorState.STARTUP: {
        "pattern": LEDPatterns.SPINNER,
        "color": (0, 255, 0),  # Green
        "speed": 0.03
    },
    TutorState.SHUTDOWN: {
        "pattern": LEDPatterns.BREATHING,
        "color": (255, 0, 0),  # Red
        "speed": 0.05
    }
}


class LEDController:
    """
    High-level LED controller for ISEE Tutor.
    
    Manages LED patterns based on tutor state and provides
    a simple interface for the application.
    """
    
    def __init__(self, mock: bool = True, led_count: int = 16, brightness: float = 0.3):
        """
        Initialize LED controller.
        
        Args:
            mock: Use mock hardware interface
            led_count: Number of LEDs in the ring
            brightness: Initial brightness (0.0-1.0)
        """
        self.mock = mock
        self.led_count = led_count
        self.current_state = TutorState.IDLE
        self.previous_state = None
        
        # Get appropriate hardware interface
        self.hardware = get_hardware_interface(
            "led",
            mock=mock,
            count=led_count,
            brightness=brightness
        )
        
        # State management
        self._state_lock = threading.Lock()
        self._pattern_thread = None
        self._running = False
        
        logger.info(f"LEDController initialized (mock={mock}, count={led_count})")
        
    def set_state(self, state: TutorState):
        """
        Set the tutor state and update LED pattern accordingly.
        
        Args:
            state: New tutor state
        """
        with self._state_lock:
            if state == self.current_state:
                return
                
            self.previous_state = self.current_state
            self.current_state = state
            
            logger.info(f"LED state change: {self.previous_state} -> {self.current_state}")
            
            # Apply the new pattern
            self._apply_pattern(state)
            
    def _apply_pattern(self, state: TutorState):
        """Apply the LED pattern for the given state"""
        if state not in STATE_TO_PATTERN:
            logger.warning(f"No LED pattern defined for state: {state}")
            return
            
        config = STATE_TO_PATTERN[state]
        pattern = config["pattern"]
        
        # Stop any existing pattern
        if hasattr(self.hardware, 'stop_pattern'):
            self.hardware.stop_pattern()
            
        # Apply the new pattern
        if pattern == LEDPatterns.BREATHING:
            self.hardware.breathing(
                color=config["color"],
                speed=config.get("speed", 0.01)
            )
        elif pattern == LEDPatterns.SPINNER:
            self.hardware.spinner(
                color=config["color"],
                speed=config.get("speed", 0.1)
            )
        elif pattern == LEDPatterns.RAINBOW:
            self.hardware.rainbow_cycle(
                speed=config.get("speed", 0.001)
            )
        elif pattern == LEDPatterns.PULSE:
            self.hardware.pulse(
                color=config["color"],
                pulses=config.get("pulses", 3),
                speed=config.get("speed", 0.1)
            )
        elif pattern == LEDPatterns.SUCCESS:
            self.hardware.success()
        elif pattern == LEDPatterns.ERROR:
            self.hardware.error()
        elif pattern == LEDPatterns.SOLID:
            self.hardware.solid_color(config["color"])
        elif pattern == LEDPatterns.OFF:
            self.hardware.clear()
            
    def flash_notification(self, color: tuple = (255, 255, 255), count: int = 2):
        """
        Flash a quick notification without changing state.
        
        Args:
            color: RGB color tuple
            count: Number of flashes
        """
        # Save current state
        saved_state = self.current_state
        
        # Flash
        self.hardware.pulse(color=color, pulses=count, speed=0.1)
        
        # Restore previous state after a delay
        def restore():
            time.sleep(0.5)
            self.set_state(saved_state)
            
        threading.Thread(target=restore, daemon=True).start()
        
    def set_brightness(self, brightness: float):
        """
        Set LED brightness.
        
        Args:
            brightness: Brightness level (0.0-1.0)
        """
        self.hardware.set_brightness(brightness)
        logger.debug(f"LED brightness set to {brightness}")
        
    def clear(self):
        """Turn off all LEDs"""
        self.hardware.clear()
        self.current_state = TutorState.IDLE
        
    def startup_sequence(self):
        """Play startup sequence"""
        logger.info("Playing LED startup sequence")
        
        # Set startup state
        self.set_state(TutorState.STARTUP)
        time.sleep(2)
        
        # Transition to idle
        self.set_state(TutorState.IDLE)
        
    def shutdown_sequence(self):
        """Play shutdown sequence"""
        logger.info("Playing LED shutdown sequence")
        
        # Set shutdown state
        self.set_state(TutorState.SHUTDOWN)
        time.sleep(2)
        
        # Clear LEDs
        self.clear()
        
    def test_all_patterns(self, duration: float = 2.0):
        """Test all LED patterns"""
        logger.info("Testing all LED patterns")
        
        for state in TutorState:
            logger.info(f"Testing pattern: {state}")
            self.set_state(state)
            time.sleep(duration)
            
        # Return to idle
        self.set_state(TutorState.IDLE)
        
    def get_status(self) -> Dict[str, Any]:
        """Get current LED controller status"""
        status = {
            "current_state": self.current_state.value,
            "previous_state": self.previous_state.value if self.previous_state else None,
            "mock_mode": self.mock,
            "led_count": self.led_count
        }
        
        # Add hardware state if available
        if hasattr(self.hardware, 'get_state'):
            status["hardware_state"] = self.hardware.get_state()
            
        return status


# Singleton instance
_controller_instance: Optional[LEDController] = None


def get_led_controller(mock: bool = True, **kwargs) -> LEDController:
    """
    Get the singleton LED controller instance.
    
    Args:
        mock: Use mock hardware interface
        **kwargs: Additional arguments for controller
        
    Returns:
        LEDController instance
    """
    global _controller_instance
    
    if _controller_instance is None:
        _controller_instance = LEDController(mock=mock, **kwargs)
        
    return _controller_instance


# Convenience functions for common operations
def set_tutor_state(state: TutorState):
    """Set the tutor state on the default controller"""
    controller = get_led_controller()
    controller.set_state(state)
    

def notify(color: tuple = (255, 255, 255), count: int = 2):
    """Flash a notification on the default controller"""
    controller = get_led_controller()
    controller.flash_notification(color=color, count=count)


# Example usage and testing
if __name__ == "__main__":
    import argparse
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description="LED Pattern Controller")
    parser.add_argument("--real", action="store_true", help="Use real hardware (requires sudo)")
    parser.add_argument("--test", action="store_true", help="Run pattern test")
    parser.add_argument("--state", choices=[s.value for s in TutorState], help="Set specific state")
    
    args = parser.parse_args()
    
    # Initialize controller
    controller = get_led_controller(mock=not args.real)
    
    if args.test:
        print("Running LED pattern test...")
        controller.test_all_patterns(duration=3.0)
    elif args.state:
        state = TutorState(args.state)
        print(f"Setting state to: {state}")
        controller.set_state(state)
        
        # Keep running to show pattern
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            controller.shutdown_sequence()
    else:
        print("LED Controller Interactive Demo")
        print("Available states:")
        for i, state in enumerate(TutorState):
            print(f"  {i}: {state.value}")
        print("  q: Quit")
        print("  t: Test all patterns")
        print("  n: Send notification")
        
        controller.startup_sequence()
        
        try:
            while True:
                choice = input("\nEnter choice: ").strip().lower()
                
                if choice == 'q':
                    break
                elif choice == 't':
                    controller.test_all_patterns()
                elif choice == 'n':
                    controller.flash_notification()
                elif choice.isdigit():
                    idx = int(choice)
                    states = list(TutorState)
                    if 0 <= idx < len(states):
                        controller.set_state(states[idx])
                    else:
                        print("Invalid state index")
                else:
                    print("Invalid choice")
                    
        except KeyboardInterrupt:
            pass
            
        print("\nShutting down...")
        controller.shutdown_sequence()