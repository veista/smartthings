[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
# SmartThings Custom
A fork of the Home Assistant SmartThings Integration. This adds better support for Samsung OCF Devices.


## Fixed features:
  - AC Humidity (now shows as sensor and also in climate entity)
  - AC Power consumption is now a separate sensor (removed from climate entity)
  - AC fan only mode
  - Audio volume (audio volume is now a number entity instead of sensor)
  - Oven Operating State
 
## Added features:
  - AC Preset modes
  - AC Fan swing modes
  - AC Dust Filter: Reset and Capacity select
  - AC Display Light (Read Notes)
  - AC Temperature Min, Max and step (mine has a step of 1 deg this is a fixed value)
  - AC Auto cleaning mode
  - AC Disabled Capabilities are now shown in climate entity and prevented from being added to HA
  - Sensors with null values are now shown as "unavailable" instead of "unknown"
  - OCF Device type now shows manufacturer and device model. Please note, this might be the SmartThings module model.
  - AC Motion Sensor Saver
  - Firmware update availability sensor
  - Oven Lamp
  - Oven Meat Probe Sensor
  - Oven Kids Lock Sensor
  - Oven Door State Sensor
  - Oven Cooktop State Sensor
  - Oven Sound Switch (Read Notes)
  - Oven Remote Control Status
  - Oven Cooktop Center Warmer State (Read Notes)
  - Oven Cooktop Burner Sensors (Read Notes)

## Installation:
### HACS
- Remove your original smartthings integration if you have one set up (optional)
- Add `https://github.com/veista/smartthings` as a Custom Repository
- Install `SmartThings Custom` from the HACS Integrations tab
- Restart Home Assistant
- Install `SmartThings` from the HA Integrations tab
- Enjoy!

### Manually
- Remove your original smartthings integration if you have one set up (optional)
- Copy the smartthings folder to custom_components\
- Restart Home Assistant
- Install `SmartThings` from the HA Integrations tab
- Enjoy!

## Notes:
- If you have an extra switch called Light (you don't have a display in your AC), please give me your model number in issues so I can exclude it from the integration for your model
- If you are missing the sound switch, Cooktop Center Warmer or Cooktop Burner Sensors from your oven, please open an issue and give me your device Model number shown in HA 
- On some AC models not all features function properly before you cycle the power on them after adding them to HA
- I added all functions that were supported in my AC. If you want a feature that is missing, be welcome to open an issue and we'll find a solution together.
- If you like the integration please star this repository. You can also support me directly at https://www.buymeacoffee.com/veista
