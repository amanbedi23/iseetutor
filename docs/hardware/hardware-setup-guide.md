# Hardware Setup Guide for ISEE Tutor Device

## Components Checklist
- [ ] Jetson Orin Nano Dev Kit
- [ ] 10.1" Touchscreen Monitor with HDMI cable
- [ ] DisplayPort to HDMI adapter/cable (REQUIRED - Jetson has DP, not HDMI)
- [ ] ReSpeaker USB Mic Array
- [ ] USB Computer Speaker
- [ ] Arduino Nicla Voice
- [ ] AX1800 WiFi 6 USB Adapter
- [ ] 256GB MicroSD Card
- [ ] 1TB NVMe SSD (SABRENT Rocket 5)
- [ ] 16-bit RGB LED Ring
- [ ] Momentary Push Button Switch
- [ ] Power supplies for Jetson and Monitor
- [ ] USB hub (recommended for multiple USB devices)

## Assembly Steps

### 1. Prepare the Jetson Orin Nano
1. **Install NVMe SSD**
   - Power off the Jetson
   - Locate the M.2 Key M slot on the carrier board
   - Insert the SABRENT Rocket 5 SSD at a 30-degree angle
   - Secure with the mounting screw

2. **Insert MicroSD Card**
   - Flash JetPack OS to the 256GB MicroSD card (instructions in next guide)
   - Insert the MicroSD card into the slot on the carrier board

### 2. Connect Display
1. **DisplayPort to HDMI Connection**
   - The Jetson Orin Nano has a DisplayPort output, not HDMI
   - You'll need a DisplayPort to HDMI adapter/cable
   - Connect DisplayPort end to Jetson
   - Connect HDMI end to your touchscreen monitor
2. **Touch Input**
   - Connect the touchscreen USB cable to a USB port on Jetson
   - This enables touch functionality
3. **Power**
   - Power on the monitor using its power adapter

### 3. Set Up Audio Components
1. **ReSpeaker USB Mic Array**
   - Connect to USB 3.0 port on Jetson
   - Note the LED indicators on the array

2. **USB Speaker**
   - Connect to another USB port
   - May require powered USB hub if running out of ports

3. **Arduino Nicla Voice** (for later integration)
   - Keep separate for now
   - Will be integrated after basic setup

### 4. Network and Storage
1. **WiFi Adapter**
   - Plug the AX1800 adapter into a USB 3.0 port
   - Position for optimal signal reception

### 5. LED Ring Setup (WS2812B)
1. **Understanding the Connectors**
   - Your LED ring has JST-SM 3-pin connectors
   - Pinout: VCC (5V), DATA, GND
   - One side is INPUT, other is OUTPUT (for chaining)

2. **Required Materials**
   - JST-SM 3-pin male connector OR
   - Cut one connector and use jumper wires
   - 1000µF capacitor (recommended for power stability)
   - 470Ω resistor (for data line protection)
   - Level shifter (3.3V to 5V) - IMPORTANT!

3. **Wiring to Jetson GPIO (40-pin header)**
   ```
   LED Ring → Jetson Orin Nano
   --------------------------
   VCC (Red)   → Pin 2 or 4 (5V)
   GND (Black) → Pin 6 (GND)
   DIN (Green) → Level Shifter → Pin 32 (GPIO 124)
   ```

4. **CRITICAL: Level Shifting**
   - Jetson GPIO outputs 3.3V
   - WS2812B needs 5V logic
   - Use a level shifter like 74AHCT125 or similar
   - Connect: Jetson Pin 32 → Level Shifter Input
   - Level Shifter Output → 470Ω resistor → LED Data In

5. **Power Considerations**
   - 16 LEDs at full brightness = ~960mA
   - Jetson 5V pins can supply this, but:
   - Add 1000µF capacitor between 5V and GND near LED
   - For production, consider separate 5V power supply

### 6. Push Button Integration
1. **Wire the Momentary Button**
   - Connect to GPIO pins:
     - One side to Pin 18 (GPIO 24)
     - Other side to GND (Pin 14)
   - The button has built-in pull-up

### 7. Final Assembly
1. **Organize cables** using cable ties
2. **Ensure proper ventilation** for the Jetson
3. **Test all connections** before powering on

## Power-On Sequence
1. Connect all components first
2. Power on the monitor
3. Power on the Jetson Orin Nano
4. Wait for boot (first boot takes longer)

## Troubleshooting
- **No display**: Check HDMI connection and monitor power
- **Touch not working**: Ensure USB cable from monitor is connected
- **No audio**: Check USB connections and power
- **WiFi not detected**: May need drivers (covered in software setup)