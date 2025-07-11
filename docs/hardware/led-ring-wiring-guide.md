# WS2812B LED Ring Wiring Guide for Jetson Orin Nano

## Your LED Ring Details
- Model: 16-bit WS2812B RGB LED Ring
- Connectors: 3-pin JST-SM connectors (both sides)
- One side: INPUT (connect here)
- Other side: OUTPUT (for daisy-chaining)

## Option 1: Direct Wiring (Easiest)

### What You Need:
1. **JST-SM 3-pin pigtail/connector** (male) OR
2. **Cut and strip the wires** from the INPUT connector
3. **Jumper wires** for GPIO connection
4. **Level shifter** (3.3V to 5V) - CRITICAL!
   - Options: 74AHCT125, TXS0108E, or similar
5. **330-470Ω resistor** (for data line)

### Wiring Connections:

```
LED Ring INPUT Side → Level Shifter → Jetson GPIO 40-pin Header
----------------------------------------------------------------
VCC (Red wire)    → Jetson Pin 2 or 4 (5V)
GND (Black wire)  → Jetson Pin 6 (GND)  
DIN (Green/White) → 470Ω resistor → Level Shifter HV Input
                    Level Shifter LV Output → Jetson Pin 32 (GPIO 12/SPI_CS0)

Level Shifter Power:
LV (Low Voltage)  → Jetson Pin 1 (3.3V)
HV (High Voltage) → Jetson Pin 2 (5V)
GND              → Jetson Pin 6 (GND)
```

## Option 2: Using a Breadboard

### Setup:
1. **Cut the INPUT connector** leaving ~3 inches of wire
2. **Strip wire ends** (~1/4 inch)
3. **Insert into breadboard**
4. **Add level shifter** to breadboard
5. **Use jumper wires** to connect to Jetson

### Breadboard Layout:
```
Jetson 5V (Pin 2)  ----→ [Breadboard +5V rail] ----→ LED VCC (Red)
Jetson GND (Pin 6) ----→ [Breadboard GND rail] ----→ LED GND (Black)
Jetson 3.3V (Pin 1) ---→ Level Shifter LV
Jetson Pin 32 ---------→ Level Shifter A1 (LV side)
Level Shifter B1 ------→ [470Ω resistor] ----→ LED DIN (Green/White)
```

## Option 3: No Level Shifter (Less Reliable)

**WARNING**: This may work but is not recommended for reliability

Some WS2812B LEDs accept 3.3V logic when powered by 5V, but it's not guaranteed.

```
Direct Connection (Use at your own risk):
VCC → Jetson Pin 2 (5V)
GND → Jetson Pin 6 (GND)
DIN → 470Ω resistor → Jetson Pin 32
```

## Testing Your Connection

1. **Install required libraries** (on Jetson):
```bash
# Install Python GPIO library
sudo apt-get update
sudo apt-get install python3-pip
sudo pip3 install Jetson.GPIO
sudo pip3 install adafruit-circuitpython-neopixel
```

2. **Create test script**:
```python
import time
import board
import neopixel

# Configure for Pin 32 (SPI CS0)
pixel_pin = board.SPICLK  # Pin 32
num_pixels = 16

pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.2)

# Test: All red
pixels.fill((255, 0, 0))
time.sleep(1)

# Test: All green
pixels.fill((0, 255, 0))
time.sleep(1)

# Test: All blue
pixels.fill((0, 0, 255))
time.sleep(1)

# Clear
pixels.fill((0, 0, 0))
```

3. **Run with sudo**:
```bash
sudo python3 test_led.py
```

## Troubleshooting

### LEDs don't light up:
- Check power connections (5V and GND)
- Verify you're connected to INPUT side (not OUTPUT)
- Ensure level shifter is powered correctly

### LEDs flicker or show wrong colors:
- Add 1000µF capacitor across 5V and GND
- Check data line resistor (330-470Ω)
- Ensure good ground connection

### First LED works, others don't:
- Level shifting issue - 3.3V logic not reliable
- Try shorter data wire
- Reduce brightness in code

## Recommended Level Shifters

1. **74AHCT125** - Quad level shifter, very reliable
2. **TXS0108E** - 8-channel bidirectional
3. **SN74LVC1T45** - Single channel, compact
4. **Sparkfun Level Shifter** - BOB-12009

## Where to Buy:
- Amazon: Search "3.3V to 5V level shifter"
- Adafruit: Product ID 1787
- SparkFun: BOB-12009

## Quick Shopping List:
```
□ 74AHCT125 level shifter (or similar)
□ 470Ω resistor
□ Jumper wires (female-to-male)
□ Small breadboard (optional)
□ 1000µF capacitor (optional but recommended)
```