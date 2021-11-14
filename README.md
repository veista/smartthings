# smartthings
A fork of the Home Assistant SmartThings Integration. This adds better support for Samsung OCF Air Conditioners.

Fixed features:
  - AC Humidity
  - AC Power consumption
  - AC fan only mode
  - Audio volume
 
Added features:
  - AC Preset modes
  - AC Fan swing modes
  - AC Dust Filter: Reset and Capacity select
  - AC Light
  - AC Temperature Min, Max and step (mine has a step of 1 deg this is a fixed value)
  - AC Auto cleaning mode

Installation:
- Copy to custom_components\smartthings folder and enjoy.

Notes:
- The only capability I omitted from my own AC is Motion Sensor Saver. At this time I have no use for this feature.
- Tested with Samsung AC AR12TXCACWKNEE ARTIK051_PRAC_20K
