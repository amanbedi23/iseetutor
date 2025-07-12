"""
Hardware module for ISEE Tutor.

Provides interfaces for LED control, button handling, and GPIO operations
with automatic fallback to mock implementations for development.
"""

from .hardware_manager import (
    HardwareManager,
    HardwareConfig,
    get_hardware_manager,
    set_tutor_state,
    notify
)

from .led_patterns import (
    LEDController,
    TutorState,
    LEDPatterns,
    get_led_controller
)

from .button_handler import (
    ButtonHandler,
    ButtonEvent,
    TutorButtonManager
)

from .mock_hardware import (
    MockWS2812BController,
    MockButton,
    MockGPIO,
    get_hardware_interface
)


__all__ = [
    # Hardware Manager
    "HardwareManager",
    "HardwareConfig", 
    "get_hardware_manager",
    "set_tutor_state",
    "notify",
    
    # LED Control
    "LEDController",
    "TutorState",
    "LEDPatterns",
    "get_led_controller",
    
    # Button Handling
    "ButtonHandler",
    "ButtonEvent",
    "TutorButtonManager",
    
    # Mock Hardware
    "MockWS2812BController",
    "MockButton",
    "MockGPIO",
    "get_hardware_interface"
]