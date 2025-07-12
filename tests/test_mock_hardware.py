#!/usr/bin/env python3
"""
Test script for mock hardware classes.
"""

import sys
import time
import logging
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.hardware import (
    get_hardware_manager,
    HardwareConfig,
    TutorState,
    ButtonEvent
)


def test_hardware_manager():
    """Test the hardware manager with mock components"""
    print("Testing Hardware Manager with Mock Components")
    print("=" * 50)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create hardware manager with mock components
    config = HardwareConfig(use_mock=True)
    hw_manager = get_hardware_manager(config)
    
    # Test 1: Startup sequence
    print("\n1. Testing startup sequence...")
    hw_manager.startup()
    time.sleep(2)
    
    # Test 2: LED states
    print("\n2. Testing LED states...")
    test_states = [
        (TutorState.IDLE, "Idle - gentle breathing"),
        (TutorState.LISTENING, "Listening - cyan breathing"),
        (TutorState.THINKING, "Thinking - blue spinner"),
        (TutorState.SPEAKING, "Speaking - orange spinner"),
        (TutorState.SUCCESS, "Success - green pulses"),
        (TutorState.ERROR, "Error - red pulses"),
    ]
    
    for state, description in test_states:
        print(f"   {description}")
        hw_manager.set_state(state)
        time.sleep(2)
    
    # Test 3: Notifications
    print("\n3. Testing notifications...")
    print("   Yellow notification")
    hw_manager.flash_notification((255, 255, 0), count=3)
    time.sleep(2)
    
    # Test 4: Button simulation
    print("\n4. Testing button events...")
    button_mgr = hw_manager._components.get('button')
    
    if button_mgr:
        button = button_mgr.button_handler
        
        print("   Short press (wake word)")
        button.simulate_press(0.1)
        time.sleep(1)
        
        print("   Double press (mode change)")
        button.simulate_press(0.1)
        time.sleep(0.2)
        button.simulate_press(0.1)
        time.sleep(2)
        
        print("   Long press (mute toggle)")
        button.simulate_press(1.5)
        time.sleep(2)
        
        print("   Triple press (emergency stop)")
        for _ in range(3):
            button.simulate_press(0.1)
            time.sleep(0.2)
        time.sleep(2)
    
    # Test 5: Status and health check
    print("\n5. Testing status and health check...")
    status = hw_manager.get_status()
    print(f"   Status: Mock mode = {status['mock_mode']}")
    print(f"   Components: {list(status['components'].keys())}")
    
    health = hw_manager.health_check()
    print(f"   Health: {'HEALTHY' if health['healthy'] else 'UNHEALTHY'}")
    for component, state in health['components'].items():
        print(f"     - {component}: {state}")
    
    # Test 6: Shutdown sequence
    print("\n6. Testing shutdown sequence...")
    hw_manager.shutdown()
    
    print("\n✅ All mock hardware tests completed successfully!")


def test_individual_components():
    """Test individual mock components"""
    print("\n\nTesting Individual Mock Components")
    print("=" * 50)
    
    from src.core.hardware.mock_hardware import (
        MockWS2812BController,
        MockButton,
        MockGPIO
    )
    
    # Test LED Controller
    print("\n1. Testing MockWS2812BController...")
    led = MockWS2812BController(count=16)
    led.solid_color((255, 0, 0))
    led.breathing((0, 255, 0), speed=0.01)
    time.sleep(0.5)
    led.stop_pattern()
    print("   ✓ LED controller working")
    
    # Test Button
    print("\n2. Testing MockButton...")
    button = MockButton(pin=18)
    
    press_count = 0
    def on_press(pin):
        nonlocal press_count
        press_count += 1
    
    button.add_callback(on_press, edge="falling")
    button.simulate_press()
    assert press_count == 1, "Button press not detected"
    print("   ✓ Button working")
    
    # Test GPIO
    print("\n3. Testing MockGPIO...")
    gpio = MockGPIO()
    gpio.setmode(gpio.BCM)
    gpio.setup(23, gpio.OUT)
    gpio.output(23, 1)
    gpio.setup(24, gpio.IN, pull_up_down=gpio.PUD_UP)
    value = gpio.input(24)
    assert value == 1, "GPIO input not working"
    gpio.cleanup()
    print("   ✓ GPIO working")
    
    print("\n✅ All individual component tests passed!")


def interactive_demo():
    """Interactive hardware demo"""
    print("\n\nInteractive Hardware Demo")
    print("=" * 50)
    print("This demo lets you interactively control the mock hardware")
    
    config = HardwareConfig(use_mock=True)
    hw_manager = get_hardware_manager(config)
    
    # Startup
    hw_manager.startup()
    
    print("\nCommands:")
    print("  1-9: Set different LED states")
    print("  n: Flash notification")
    print("  b: Simulate button press")
    print("  s: Show status")
    print("  q: Quit")
    
    state_map = {
        '1': TutorState.IDLE,
        '2': TutorState.LISTENING,
        '3': TutorState.THINKING,
        '4': TutorState.SPEAKING,
        '5': TutorState.SUCCESS,
        '6': TutorState.ERROR,
        '7': TutorState.LEARNING,
        '8': TutorState.QUIZ,
        '9': TutorState.CELEBRATION,
    }
    
    try:
        while True:
            cmd = input("\nEnter command: ").strip().lower()
            
            if cmd == 'q':
                break
            elif cmd in state_map:
                state = state_map[cmd]
                print(f"Setting state: {state.value}")
                hw_manager.set_state(state)
            elif cmd == 'n':
                print("Flashing notification...")
                hw_manager.flash_notification((255, 255, 0), count=2)
            elif cmd == 'b':
                button_mgr = hw_manager._components.get('button')
                if button_mgr:
                    print("Simulating button press...")
                    button_mgr.button_handler.simulate_press(0.1)
            elif cmd == 's':
                status = hw_manager.get_status()
                print(f"Status: {status}")
            else:
                print("Unknown command")
                
    except KeyboardInterrupt:
        pass
    
    # Shutdown
    print("\nShutting down...")
    hw_manager.shutdown()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test mock hardware components")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run interactive demo")
    parser.add_argument("--components", "-c", action="store_true", help="Test individual components")
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_demo()
    elif args.components:
        test_individual_components()
    else:
        test_hardware_manager()
        test_individual_components()