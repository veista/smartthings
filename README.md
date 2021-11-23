[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
# SmartThings Custom
A fork of the Home Assistant SmartThings Integration. This adds better support for Samsung OCF Air Conditioners.


## Fixed features:
  - AC Humidity (now shows as sensor and also in climate entity)
  - AC Power consumption is now a separate sensor (removed from climate entity)
  - AC fan only mode
  - Audio volume (audio volume is now a number entity instead of sensor)
 
## Added features:
  - AC Preset modes
  - AC Fan swing modes
  - AC Dust Filter: Reset and Capacity select
  - AC Display Light
  - AC Temperature Min, Max and step (mine has a step of 1 deg this is a fixed value)
  - AC Auto cleaning mode
  - AC Disabled Capabilities are now shown in climate entity and prevented from being added to HA
  - Sensors with null values are now shown as "unavailable" instead of "unknown"
  - OCF Device type now shows manufacturer and device model. Please note, this might be the SmartThings module model. 

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
- Copy to smartthings folder to custom_components\
- Restart Home Assistant
- Install `SmartThings` from the HA Integrations tab
- Enjoy!

## Notes:
- The only capability I omitted from my own AC is Motion Sensor Saver. At this time I have no use for this feature.
- Tested with Samsung AC AR12TXCACWKNEE ARTIK051_PRAC_20K
