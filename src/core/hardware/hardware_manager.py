#!/usr/bin/env python3
"""
Hardware manager for ISEE Tutor.

Provides a unified interface for all hardware components (LEDs, buttons, GPIO)
with automatic fallback to mock implementations when hardware is unavailable.
"""

import logging
import os
import threading
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass

from .led_patterns import LEDController, TutorState, get_led_controller
from .button_handler import TutorButtonManager
from .mock_hardware import MockGPIO


logger = logging.getLogger(__name__)


@dataclass
class HardwareConfig:
    """Hardware configuration settings"""
    use_mock: bool = True
    led_count: int = 16
    led_brightness: float = 0.3
    button_pin: int = 18
    audio_enabled: bool = True
    gpio_warnings: bool = False


class HardwareManager:
    """
    Unified hardware manager for ISEE Tutor.
    
    Features:
    - Automatic detection of hardware availability
    - Fallback to mock implementations
    - Thread-safe operation
    - Health monitoring
    - Event coordination between components
    """
    
    def __init__(self, config: Optional[HardwareConfig] = None):
        """
        Initialize hardware manager.
        
        Args:
            config: Hardware configuration (uses defaults if None)
        """
        self.config = config or HardwareConfig()
        
        # Detect if we're on actual hardware
        self._detect_hardware()
        
        # Initialize components
        self._lock = threading.Lock()
        self._components = {}
        self._callbacks = {
            "hardware_event": [],
            "state_change": [],
            "error": []
        }
        
        # Initialize hardware components
        self._init_components()
        
        logger.info(f"HardwareManager initialized (mock={self.config.use_mock})")
        
    def _detect_hardware(self):
        """Detect if running on actual Jetson hardware"""
        # Check for Jetson indicators
        jetson_indicators = [
            "/proc/device-tree/model",  # Jetson model info
            "/sys/module/tegra_fuse",   # Tegra module
            "/dev/nvmap"                 # NVIDIA memory mapping
        ]
        
        is_jetson = any(os.path.exists(path) for path in jetson_indicators)
        
        # Check if GPIO is available and functional
        gpio_available = False
        try:
            import Jetson.GPIO
            # Try to actually use it to see if it works
            Jetson.GPIO.setmode(Jetson.GPIO.BCM)
            Jetson.GPIO.cleanup()
            gpio_available = True
        except Exception as e:
            logger.debug(f"GPIO not functional: {e}")
            gpio_available = False
            
        # Override mock setting if hardware not available
        if not self.config.use_mock and not (is_jetson and gpio_available):
            logger.warning("Hardware not detected, forcing mock mode")
            self.config.use_mock = True
        elif is_jetson and gpio_available and self.config.use_mock:
            logger.info("Jetson hardware detected but mock mode requested")
            
    def _init_components(self):
        """Initialize hardware components"""
        try:
            # Initialize LED controller
            self._components['led'] = get_led_controller(
                mock=self.config.use_mock,
                led_count=self.config.led_count,
                brightness=self.config.led_brightness
            )
            
            # Initialize button manager
            self._components['button'] = TutorButtonManager(
                button_pin=self.config.button_pin,
                mock=self.config.use_mock
            )
            
            # Set up button callbacks to coordinate with LEDs
            self._setup_button_callbacks()
            
            # Initialize GPIO if needed
            if not self.config.use_mock:
                try:
                    import Jetson.GPIO as GPIO
                    GPIO.setmode(GPIO.BCM)
                    GPIO.setwarnings(self.config.gpio_warnings)
                    self._components['gpio'] = GPIO
                except ImportError:
                    logger.warning("Jetson.GPIO not available, using mock")
                    self._components['gpio'] = MockGPIO()
            else:
                self._components['gpio'] = MockGPIO()
                
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            self._trigger_event("error", error=str(e))
            
    def _setup_button_callbacks(self):
        """Set up button callbacks for hardware coordination"""
        button_mgr = self._components.get('button')
        if not button_mgr:
            return
            
        # Mode change updates LED state
        def on_mode_change(old_mode, new_mode):
            logger.info(f"Hardware: Mode change {old_mode} -> {new_mode}")
            if new_mode == "tutor":
                self.set_state(TutorState.LEARNING)
            else:
                self.set_state(TutorState.IDLE)
            self._trigger_event("state_change", old_mode=old_mode, new_mode=new_mode)
            
        # Mute toggle shows visual feedback
        def on_mute_toggle(is_muted):
            logger.info(f"Hardware: Mute toggled to {is_muted}")
            led = self._components.get('led')
            if led and is_muted:
                led.flash_notification((255, 0, 0), count=1)  # Red flash
            elif led:
                led.flash_notification((0, 255, 0), count=1)  # Green flash
                
        # Wake word trigger
        def on_wake_word():
            logger.info("Hardware: Wake word triggered via button")
            self.set_state(TutorState.LISTENING)
            self._trigger_event("hardware_event", event="wake_word_button")
            
        # Emergency stop
        def on_emergency_stop():
            logger.warning("Hardware: Emergency stop!")
            self.set_state(TutorState.ERROR)
            self._trigger_event("hardware_event", event="emergency_stop")
            
        # Register callbacks
        button_mgr.add_callback("mode_change", on_mode_change)
        button_mgr.add_callback("mute_toggle", on_mute_toggle)
        button_mgr.add_callback("wake_word_trigger", on_wake_word)
        button_mgr.add_callback("emergency_stop", on_emergency_stop)
        
    def set_state(self, state: TutorState):
        """
        Set the tutor state and update hardware accordingly.
        
        Args:
            state: New tutor state
        """
        with self._lock:
            led = self._components.get('led')
            if led:
                led.set_state(state)
                
    def flash_notification(self, color: tuple = (255, 255, 255), count: int = 2):
        """Flash LED notification"""
        led = self._components.get('led')
        if led:
            led.flash_notification(color=color, count=count)
            
    def set_brightness(self, brightness: float):
        """Set LED brightness"""
        led = self._components.get('led')
        if led:
            led.set_brightness(brightness)
            
    def add_callback(self, event_type: str, callback: Callable):
        """Add callback for hardware events"""
        if event_type in self._callbacks:
            self._callbacks[event_type].append(callback)
            
    def _trigger_event(self, event_type: str, **kwargs):
        """Trigger callbacks for an event"""
        for callback in self._callbacks.get(event_type, []):
            try:
                callback(**kwargs)
            except Exception as e:
                logger.error(f"Error in {event_type} callback: {e}")
                
    def startup(self):
        """Perform hardware startup sequence"""
        logger.info("Hardware startup sequence")
        
        # LED startup sequence
        led = self._components.get('led')
        if led:
            led.startup_sequence()
            
        self._trigger_event("hardware_event", event="startup_complete")
        
    def shutdown(self):
        """Perform hardware shutdown sequence"""
        logger.info("Hardware shutdown sequence")
        
        # LED shutdown sequence
        led = self._components.get('led')
        if led:
            led.shutdown_sequence()
            
        # Cleanup GPIO
        gpio = self._components.get('gpio')
        if gpio and hasattr(gpio, 'cleanup'):
            gpio.cleanup()
            
        self._trigger_event("hardware_event", event="shutdown_complete")
        
    def get_status(self) -> Dict[str, Any]:
        """Get hardware status"""
        status = {
            "mock_mode": self.config.use_mock,
            "components": {}
        }
        
        # Get LED status
        led = self._components.get('led')
        if led and hasattr(led, 'get_status'):
            status["components"]["led"] = led.get_status()
            
        # Get button status
        button = self._components.get('button')
        if button and hasattr(button, 'get_status'):
            status["components"]["button"] = button.get_status()
            
        return status
        
    def health_check(self) -> Dict[str, Any]:
        """Perform hardware health check"""
        health = {
            "healthy": True,
            "components": {}
        }
        
        # Check each component
        for name, component in self._components.items():
            try:
                if hasattr(component, 'get_status'):
                    component.get_status()
                health["components"][name] = "OK"
            except Exception as e:
                health["components"][name] = f"ERROR: {str(e)}"
                health["healthy"] = False
                
        return health


# Singleton instance
_hardware_manager: Optional[HardwareManager] = None


def get_hardware_manager(config: Optional[HardwareConfig] = None) -> HardwareManager:
    """
    Get the singleton hardware manager instance.
    
    Args:
        config: Hardware configuration (only used on first call)
        
    Returns:
        HardwareManager instance
    """
    global _hardware_manager
    
    if _hardware_manager is None:
        _hardware_manager = HardwareManager(config)
        
    return _hardware_manager


# Convenience functions
def set_tutor_state(state: TutorState):
    """Set tutor state on default hardware manager"""
    manager = get_hardware_manager()
    manager.set_state(state)
    

def notify(color: tuple = (255, 255, 255), count: int = 2):
    """Flash notification on default hardware manager"""
    manager = get_hardware_manager()
    manager.flash_notification(color=color, count=count)


# Example usage and testing
if __name__ == "__main__":
    import time
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Hardware Manager Demo")
    print("-" * 40)
    
    # Create hardware manager
    config = HardwareConfig(use_mock=True)
    manager = get_hardware_manager(config)
    
    # Add event callbacks
    def on_hardware_event(**kwargs):
        print(f"Hardware event: {kwargs}")
        
    def on_state_change(**kwargs):
        print(f"State change: {kwargs}")
        
    manager.add_callback("hardware_event", on_hardware_event)
    manager.add_callback("state_change", on_state_change)
    
    # Perform startup
    print("\n1. Startup sequence")
    manager.startup()
    time.sleep(3)
    
    # Test states
    print("\n2. Testing states")
    states = [
        TutorState.LISTENING,
        TutorState.THINKING,
        TutorState.SPEAKING,
        TutorState.SUCCESS,
        TutorState.IDLE
    ]
    
    for state in states:
        print(f"   Setting state: {state.value}")
        manager.set_state(state)
        time.sleep(2)
        
    # Test notification
    print("\n3. Testing notification")
    manager.flash_notification((255, 255, 0), count=3)
    time.sleep(2)
    
    # Get status
    print("\n4. Hardware status")
    status = manager.get_status()
    print(f"   Status: {status}")
    
    # Health check
    print("\n5. Health check")
    health = manager.health_check()
    print(f"   Health: {health}")
    
    # Test button interactions
    print("\n6. Testing button interactions")
    print("   Simulating button presses...")
    
    button = manager._components.get('button')
    if button and hasattr(button.button_handler, 'simulate_press'):
        print("   - Short press (wake word)")
        button.button_handler.simulate_press(0.1)
        time.sleep(2)
        
        print("   - Double press (mode change)")
        button.button_handler.simulate_press(0.1)
        time.sleep(0.2)
        button.button_handler.simulate_press(0.1)
        time.sleep(2)
        
        print("   - Long press (mute toggle)")
        button.button_handler.simulate_press(1.5)
        time.sleep(2)
        
    # Shutdown
    print("\n7. Shutdown sequence")
    manager.shutdown()
    
    print("\nDemo complete!")