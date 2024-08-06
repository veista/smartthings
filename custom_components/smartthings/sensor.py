"""Support for sensors through the SmartThings cloud API."""
from __future__ import annotations

from collections import namedtuple
from collections.abc import Sequence

import json

import asyncio

from pysmartthings import Attribute, Capability
from pysmartthings.device import DeviceEntity

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)

from homeassistant.const import (
    AREA_SQUARE_METERS,
    CONCENTRATION_PARTS_PER_MILLION,
    UnitOfElectricPotential,
    UnitOfEnergy,
    LIGHT_LUX,
    UnitOfMass,
    PERCENTAGE,
    UnitOfPower,
    UnitOfVolume,
)

from homeassistant.helpers.entity import EntityCategory
from homeassistant.util import dt as dt_util

from . import SmartThingsEntity
from .const import DATA_BROKERS, DOMAIN, UNIT_MAP

Map = namedtuple(
    "map", "attribute name default_unit device_class state_class entity_category"
)

CAPABILITY_TO_SENSORS = {
    Capability.activity_lighting_mode: [
        Map(
            Attribute.lighting_mode,
            "Activity Lighting Mode",
            None,
            None,
            None,
            EntityCategory.CONFIG,
        )
    ],
    Capability.air_conditioner_mode: [
        Map(
            Attribute.air_conditioner_mode,
            "Air Conditioner Mode",
            None,
            None,
            None,
            EntityCategory.CONFIG,
        )
    ],
    Capability.air_quality_sensor: [
        Map(
            Attribute.air_quality,
            "Air Quality",
            "CAQI",
            None,
            SensorStateClass.MEASUREMENT,
            None,
        )
    ],
    Capability.alarm: [Map(Attribute.alarm, "Alarm", None, None, None, None)],
    Capability.audio_volume: [
        Map(Attribute.volume, "Volume", PERCENTAGE, None, None, None)
    ],
    Capability.battery: [
        Map(
            Attribute.battery,
            "Battery",
            PERCENTAGE,
            SensorDeviceClass.BATTERY,
            None,
            EntityCategory.DIAGNOSTIC,
        )
    ],
    Capability.body_mass_index_measurement: [
        Map(
            Attribute.bmi_measurement,
            "Body Mass Index",
            f"{UnitOfMass.KILOGRAMS}/{AREA_SQUARE_METERS}",
            None,
            SensorStateClass.MEASUREMENT,
            None,
        )
    ],
    Capability.body_weight_measurement: [
        Map(
            Attribute.body_weight_measurement,
            "Body Weight",
            UnitOfMass.KILOGRAMS,
            None,
            SensorStateClass.MEASUREMENT,
            None,
        )
    ],
    Capability.carbon_dioxide_measurement: [
        Map(
            Attribute.carbon_dioxide,
            "Carbon Dioxide Measurement",
            CONCENTRATION_PARTS_PER_MILLION,
            SensorDeviceClass.CO2,
            SensorStateClass.MEASUREMENT,
            None,
        )
    ],
    Capability.carbon_monoxide_detector: [
        Map(
            Attribute.carbon_monoxide,
            "Carbon Monoxide Detector",
            None,
            None,
            None,
            None,
        )
    ],
    Capability.carbon_monoxide_measurement: [
        Map(
            Attribute.carbon_monoxide_level,
            "Carbon Monoxide Measurement",
            CONCENTRATION_PARTS_PER_MILLION,
            SensorDeviceClass.CO,
            SensorStateClass.MEASUREMENT,
            None,
        )
    ],
    Capability.dishwasher_operating_state: [
        Map(
            Attribute.machine_state, "Dishwasher Machine State", None, None, None, None
        ),
        Map(
            Attribute.dishwasher_job_state,
            "Dishwasher Job State",
            None,
            None,
            None,
            None,
        ),
        Map(
            Attribute.completion_time,
            "Dishwasher Completion Time",
            None,
            SensorDeviceClass.TIMESTAMP,
            None,
            None,
        ),
    ],
    Capability.dryer_mode: [
        Map(
            Attribute.dryer_mode,
            "Dryer Mode",
            None,
            None,
            None,
            EntityCategory.CONFIG,
        )
    ],
    Capability.dryer_operating_state: [
        Map(Attribute.machine_state, "Dryer Machine State", None, None, None, None),
        Map(Attribute.dryer_job_state, "Dryer Job State", None, None, None, None),
        Map(
            Attribute.completion_time,
            "Dryer Completion Time",
            None,
            SensorDeviceClass.TIMESTAMP,
            None,
            None,
        ),
    ],
    Capability.dust_sensor: [
        Map(
            Attribute.fine_dust_level,
            "Fine Dust Level",
            None,
            None,
            SensorStateClass.MEASUREMENT,
            None,
        ),
        Map(
            Attribute.dust_level,
            "Dust Level",
            None,
            None,
            SensorStateClass.MEASUREMENT,
            None,
        ),
    ],
    Capability.energy_meter: [
        Map(
            Attribute.energy,
            "Energy Meter",
            UnitOfEnergy.KILO_WATT_HOUR,
            SensorDeviceClass.ENERGY,
            SensorStateClass.TOTAL_INCREASING,
            None,
        )
    ],
    Capability.equivalent_carbon_dioxide_measurement: [
        Map(
            Attribute.equivalent_carbon_dioxide_measurement,
            "Equivalent Carbon Dioxide Measurement",
            CONCENTRATION_PARTS_PER_MILLION,
            None,
            SensorStateClass.MEASUREMENT,
            None,
        )
    ],
    Capability.formaldehyde_measurement: [
        Map(
            Attribute.formaldehyde_level,
            "Formaldehyde Measurement",
            CONCENTRATION_PARTS_PER_MILLION,
            None,
            SensorStateClass.MEASUREMENT,
            None,
        )
    ],
    Capability.gas_meter: [
        Map(
            Attribute.gas_meter,
            "Gas Meter",
            UnitOfEnergy.KILO_WATT_HOUR,
            None,
            SensorStateClass.MEASUREMENT,
            None,
        ),
        Map(
            Attribute.gas_meter_calorific, "Gas Meter Calorific", None, None, None, None
        ),
        Map(
            Attribute.gas_meter_time,
            "Gas Meter Time",
            None,
            SensorDeviceClass.TIMESTAMP,
            None,
            None,
        ),
        Map(
            Attribute.gas_meter_volume,
            "Gas Meter Volume",
            UnitOfVolume.CUBIC_METERS,
            None,
            SensorStateClass.MEASUREMENT,
            None,
        ),
    ],
    Capability.illuminance_measurement: [
        Map(
            Attribute.illuminance,
            "Illuminance",
            LIGHT_LUX,
            SensorDeviceClass.ILLUMINANCE,
            SensorStateClass.MEASUREMENT,
            None,
        )
    ],
    Capability.infrared_level: [
        Map(
            Attribute.infrared_level,
            "Infrared Level",
            PERCENTAGE,
            None,
            SensorStateClass.MEASUREMENT,
            None,
        )
    ],
    Capability.media_input_source: [
        Map(Attribute.input_source, "Media Input Source", None, None, None, None)
    ],
    Capability.media_playback_repeat: [
        Map(
            Attribute.playback_repeat_mode,
            "Media Playback Repeat",
            None,
            None,
            None,
            None,
        )
    ],
    Capability.media_playback_shuffle: [
        Map(
            Attribute.playback_shuffle, "Media Playback Shuffle", None, None, None, None
        )
    ],
    Capability.media_playback: [
        Map(Attribute.playback_status, "Media Playback Status", None, None, None, None)
    ],
    Capability.odor_sensor: [
        Map(Attribute.odor_level, "Odor Sensor", None, None, None, None)
    ],
    Capability.oven_mode: [
        Map(
            Attribute.oven_mode,
            "Mode",
            None,
            None,
            None,
            None,
        )
    ],
    Capability.oven_operating_state: [
        Map(Attribute.operation_time, "Operation Time", None, None, None, None),
        Map(Attribute.machine_state, "Machine State", None, None, None, None),
        Map(Attribute.oven_job_state, "Job State", None, None, None, None),
        Map(
            Attribute.completion_time,
            "Completion Time",
            None,
            SensorDeviceClass.TIMESTAMP,
            None,
            None,
        ),
        Map(Attribute.progress, "Progress", PERCENTAGE, None, None, None),
    ],
    Capability.oven_setpoint: [
        Map(
            Attribute.oven_setpoint,
            "Temperature Setpoint",
            None,
            SensorDeviceClass.TEMPERATURE,
            None,
            None,
        )
    ],
    Capability.power_consumption_report: [],
    Capability.power_meter: [
        Map(
            Attribute.power,
            "Power Meter",
            UnitOfPower.WATT,
            SensorDeviceClass.POWER,
            SensorStateClass.MEASUREMENT,
            None,
        )
    ],
    Capability.power_source: [
        Map(
            Attribute.power_source,
            "Power Source",
            None,
            None,
            None,
            EntityCategory.DIAGNOSTIC,
        )
    ],
    Capability.refrigeration_setpoint: [
        Map(
            Attribute.refrigeration_setpoint,
            "Refrigeration Setpoint",
            None,
            SensorDeviceClass.TEMPERATURE,
            None,
            None,
        )
    ],
    Capability.relative_humidity_measurement: [
        Map(
            Attribute.humidity,
            "Relative Humidity Measurement",
            PERCENTAGE,
            SensorDeviceClass.HUMIDITY,
            SensorStateClass.MEASUREMENT,
            None,
        )
    ],
    Capability.robot_cleaner_cleaning_mode: [
        Map(
            Attribute.robot_cleaner_cleaning_mode,
            "Robot Cleaner Cleaning Mode",
            None,
            None,
            None,
            EntityCategory.CONFIG,
        )
    ],
    Capability.robot_cleaner_movement: [
        Map(
            Attribute.robot_cleaner_movement,
            "Robot Cleaner Movement",
            None,
            None,
            None,
            None,
        )
    ],
    Capability.robot_cleaner_turbo_mode: [
        Map(
            Attribute.robot_cleaner_turbo_mode,
            "Robot Cleaner Turbo Mode",
            None,
            None,
            None,
            EntityCategory.CONFIG,
        )
    ],
    Capability.signal_strength: [
        Map(
            Attribute.lqi,
            "LQI Signal Strength",
            None,
            None,
            SensorStateClass.MEASUREMENT,
            EntityCategory.DIAGNOSTIC,
        ),
        Map(
            Attribute.rssi,
            "RSSI Signal Strength",
            None,
            SensorDeviceClass.SIGNAL_STRENGTH,
            SensorStateClass.MEASUREMENT,
            EntityCategory.DIAGNOSTIC,
        ),
    ],
    Capability.smoke_detector: [
        Map(Attribute.smoke, "Smoke Detector", None, None, None, None)
    ],
    Capability.temperature_measurement: [
        Map(
            Attribute.temperature,
            "Temperature Measurement",
            None,
            SensorDeviceClass.TEMPERATURE,
            SensorStateClass.MEASUREMENT,
            None,
        )
    ],
    Capability.thermostat_cooling_setpoint: [
        Map(
            Attribute.cooling_setpoint,
            "Thermostat Cooling Setpoint",
            None,
            SensorDeviceClass.TEMPERATURE,
            None,
            None,
        )
    ],
    Capability.thermostat_fan_mode: [
        Map(
            Attribute.thermostat_fan_mode,
            "Thermostat Fan Mode",
            None,
            None,
            None,
            EntityCategory.CONFIG,
        )
    ],
    Capability.thermostat_heating_setpoint: [
        Map(
            Attribute.heating_setpoint,
            "Thermostat Heating Setpoint",
            None,
            SensorDeviceClass.TEMPERATURE,
            None,
            EntityCategory.CONFIG,
        )
    ],
    Capability.thermostat_mode: [
        Map(
            Attribute.thermostat_mode,
            "Thermostat Mode",
            None,
            None,
            None,
            EntityCategory.CONFIG,
        )
    ],
    Capability.thermostat_operating_state: [
        Map(
            Attribute.thermostat_operating_state,
            "Thermostat Operating State",
            None,
            None,
            None,
            None,
        )
    ],
    Capability.thermostat_setpoint: [
        Map(
            Attribute.thermostat_setpoint,
            "Thermostat Setpoint",
            None,
            SensorDeviceClass.TEMPERATURE,
            None,
            EntityCategory.CONFIG,
        )
    ],
    Capability.three_axis: [],
    Capability.tv_channel: [
        Map(Attribute.tv_channel, "Tv Channel", None, None, None, None),
        Map(Attribute.tv_channel_name, "Tv Channel Name", None, None, None, None),
    ],
    Capability.tvoc_measurement: [
        Map(
            Attribute.tvoc_level,
            "Tvoc Measurement",
            CONCENTRATION_PARTS_PER_MILLION,
            None,
            SensorStateClass.MEASUREMENT,
            None,
        )
    ],
    Capability.ultraviolet_index: [
        Map(
            Attribute.ultraviolet_index,
            "Ultraviolet Index",
            None,
            None,
            SensorStateClass.MEASUREMENT,
            None,
        )
    ],
    Capability.voltage_measurement: [
        Map(
            Attribute.voltage,
            "Voltage Measurement",
            UnitOfElectricPotential.VOLT,
            SensorDeviceClass.VOLTAGE,
            SensorStateClass.MEASUREMENT,
            None,
        )
    ],
    Capability.washer_mode: [
        Map(
            Attribute.washer_mode,
            "Washer Mode",
            None,
            None,
            None,
            EntityCategory.CONFIG,
        )
    ],
    Capability.washer_operating_state: [
        Map(Attribute.machine_state, "Washer Machine State", None, None, None, None),
        Map(Attribute.washer_job_state, "Washer Job State", None, None, None, None),
        Map(
            Attribute.completion_time,
            "Washer Completion Time",
            None,
            SensorDeviceClass.TIMESTAMP,
            None,
            None,
        ),
    ],
    "custom.cooktopOperatingState": [
        Map("cooktopOperatingState", "Cooktop Operating State", None, None, None, None)
    ],
    "remoteControlStatus": [
        Map("remoteControlEnabled", "Remote Control", None, None, None, None)
    ],
    "samsungce.doorState": [Map("doorState", "Door State", None, None, None, None)],
    "samsungce.kidsLock": [Map("lockState", "Kids Lock State", None, None, None, None)],
    "samsungce.meatProbe": [
        Map(
            "temperatureSetpoint",
            "Meat Probe Setpoint",
            None,
            SensorDeviceClass.TEMPERATURE,
            None,
            None,
        ),
        Map("status", "Meat Probe Status", None, None, None, None),
    ],
    "samsungce.softwareUpdate": [
        Map(
            "newVersionAvailable",
            "Firmware Update Available",
            None,
            None,
            None,
            EntityCategory.DIAGNOSTIC,
        ),
    ],
}


THREE_AXIS_NAMES = ["X Coordinate", "Y Coordinate", "Z Coordinate"]
POWER_CONSUMPTION_REPORT_NAMES = [
    "energy",
    "power",
    "deltaEnergy",
    "powerEnergy",
    "energySaved",
]


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add binary sensors for a config entry."""
    broker = hass.data[DOMAIN][DATA_BROKERS][config_entry.entry_id]
    sensors = []
    for device in broker.devices.values():
        for capability in broker.get_assigned(device.device_id, "sensor"):
            if capability == Capability.three_axis:
                sensors.extend(
                    [
                        SmartThingsThreeAxisSensor(device, index)
                        for index in range(len(THREE_AXIS_NAMES))
                    ]
                )
            elif capability == Capability.power_consumption_report:
                reports = POWER_CONSUMPTION_REPORT_NAMES
                if device.status.attributes["energySavingSupport"].value is False:
                    if "energySaved" in reports:
                        reports.remove("energySaved")
                sensors.extend(
                    [
                        SmartThingsPowerConsumptionSensor(device, report_name)
                        for report_name in reports
                    ]
                )
            else:
                maps = CAPABILITY_TO_SENSORS[capability]
                sensors.extend(
                    [
                        SmartThingsSensor(
                            device,
                            m.attribute,
                            m.name,
                            m.default_unit,
                            m.device_class,
                            m.state_class,
                            m.entity_category,
                        )
                        for m in maps
                    ]
                )
        if (
            device.status.attributes[Attribute.mnmn].value == "Samsung Electronics"
            and device.type == "OCF"
        ):
            model = device.status.attributes[Attribute.mnmo].value.split("|")[0]
            if model in ("TP2X_DA-KS-RANGE-0101X",):
                sensors.extend(
                    [
                        SamsungOvenWarmingCenter(device),
                        SamsungOcfTemperatureSensor(
                            device, "Temperature", "/temperature/current/cook/0"
                        ),
                        SamsungOcfTemperatureSensor(
                            device,
                            "Meat Probe Temperature",
                            "/temperature/current/prob/0",
                        ),
                    ]
                )
            elif model in ("21K_REF_LCD_FHUB6.0", "ARTIK051_REF_17K","TP1X_REF_21K"):
                sensors.extend(
                    [
                        SamsungOcfTemperatureSensor(
                            device,
                            "Cooler Temperature",
                            "/temperature/current/cooler/0",
                        ),
                        SamsungOcfTemperatureSensor(
                            device,
                            "Freezer Temperature",
                            "/temperature/current/freezer/0",
                        ),
                    ]
                )

    async_add_entities(sensors)


def get_capabilities(capabilities: Sequence[str]) -> Sequence[str] | None:
    """Return all capabilities supported if minimum required are present."""
    return [
        capability for capability in CAPABILITY_TO_SENSORS if capability in capabilities
    ]


class SmartThingsSensor(SmartThingsEntity, SensorEntity):
    """Define a SmartThings Sensor."""

    def __init__(
        self,
        device: DeviceEntity,
        attribute: str,
        name: str,
        default_unit: str,
        device_class: str,
        state_class: str | None,
        entity_category: str | None,
    ) -> None:
        """Init the class."""
        super().__init__(device)
        self._attribute = attribute
        self._name = name
        self._device_class = device_class
        self._default_unit = default_unit
        self._attr_state_class = state_class
        self._attr_entity_category = entity_category

    @property
    def name(self) -> str:
        """Return the name of the binary sensor."""
        return f"{self._device.label} {self._name}"

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self._device.device_id}.{self._attribute}"

    @property
    def available(self) -> bool:
        """check if sensor value is available"""
        if self._device.status.attributes[self._attribute].value is None:
            return False
        return True

    @property
    def native_value(self):
        """Return the state of the sensor."""
        value = self._device.status.attributes[self._attribute].value
        if self._device_class != SensorDeviceClass.TIMESTAMP:
            return value

        return dt_util.parse_datetime(value)        

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return self._device_class

    @property
    def native_unit_of_measurement(self):
        """Return the unit this state is expressed in."""
        unit = self._device.status.attributes[self._attribute].unit
        return UNIT_MAP.get(unit) if unit else self._default_unit


class SmartThingsThreeAxisSensor(SmartThingsEntity, SensorEntity):
    """Define a SmartThings Three Axis Sensor."""

    def __init__(self, device, index):
        """Init the class."""
        super().__init__(device)
        self._index = index

    @property
    def name(self) -> str:
        """Return the name of the binary sensor."""
        return f"{self._device.label} {THREE_AXIS_NAMES[self._index]}"

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self._device.device_id}.{THREE_AXIS_NAMES[self._index]}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        three_axis = self._device.status.attributes[Attribute.three_axis].value
        try:
            return three_axis[self._index]
        except (TypeError, IndexError):
            return None


class SmartThingsPowerConsumptionSensor(SmartThingsEntity, SensorEntity):
    """Define a SmartThings Sensor."""

    def __init__(
        self,
        device: DeviceEntity,
        report_name: str,
    ) -> None:
        """Init the class."""
        super().__init__(device)
        self.report_name = report_name
        if self.report_name in ("energy", "energySaved"):
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        else:
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def name(self) -> str:
        """Return the name of the binary sensor."""
        return f"{self._device.label} {self.report_name}"

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self._device.device_id}.{self.report_name}_meter"

    @property
    def available(self) -> bool:
        """check if sensor value is available"""
        value = self._device.status.attributes[Attribute.power_consumption].value
        if value is None or value.get(self.report_name) is None:
            return False
        return True

    @property
    def native_value(self):
        """Return the state of the sensor."""
        value = self._device.status.attributes[Attribute.power_consumption].value
        if value is None or value.get(self.report_name) is None:
            return None
        if self.report_name == "power":
            return value[self.report_name]
        return value[self.report_name] / 1000

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        if self.report_name == "power":
            return SensorDeviceClass.POWER
        if self.report_name in ("energy", "energySaved"):
            return SensorDeviceClass.ENERGY
        return None

    @property
    def native_unit_of_measurement(self):
        """Return the unit this state is expressed in."""
        if self.report_name == "power":
            return UnitOfPower.WATT
        return UnitOfEnergy.KILO_WATT_HOUR

    @property
    def icon(self) -> str | None:
        if self.report_name in ("deltaEnergy", "powerEnergy"):
            return "mdi:current-ac"
        return None


class SamsungOvenWarmingCenter(SmartThingsEntity, SensorEntity):
    """Define Samsung Cooktop Warming Center Sensor"""

    execute_state = "Off"
    init_bool = False

    def startup(self):
        """Make sure that OCF page visits mode on startup"""
        tasks = []
        tasks.append(self._device.execute("mode/vs/0"))
        asyncio.gather(*tasks)
        self.init_bool = True

    @property
    def name(self) -> str:
        """Return the name of the binary sensor."""
        return f"{self._device.label} Warming Center"

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self._device.device_id}.warming_center"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if not self.init_bool:
            self.startup()
        output = json.dumps(self._device.status.attributes[Attribute.data].value)

        if "WarmingCenter_High" in output:
            self.execute_state = "High"
        elif "WarmingCenter_Mid" in output:
            self.execute_state = "Mid"
        elif "WarmingCenter_Low" in output:
            self.execute_state = "Low"
        elif "WarmingCenter_Off" in output:
            self.execute_state = "Off"
        return self.execute_state

    @property
    def icon(self):
        if self.execute_state in ("High", "Mid", "Low"):
            return "mdi:checkbox-blank-circle"
        return "mdi:checkbox-blank-circle-outline"


class SamsungOcfTemperatureSensor(SmartThingsEntity, SensorEntity):
    """Define Samsung OCF Temperature Sensor"""

    execute_state = 0
    unit_state = ""
    init_bool = False

    def __init__(
        self,
        device: DeviceEntity,
        name: str,
        page: str,
    ) -> None:
        """Init the class."""
        super().__init__(device)
        self._name = name
        self._page = page

    def startup(self):
        """Make sure that OCF page visits mode on startup"""
        tasks = []
        tasks.append(self._device.execute(self._page))
        asyncio.gather(*tasks)

    @property
    def name(self) -> str:
        """Return the name of the number."""
        return f"{self._device.label} {self._name}"

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        _unique_id = self._name.lower().replace(" ", "_")
        return f"{self._device.device_id}.{_unique_id}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if (
            not self.init_bool
            or self._device.status.attributes[Attribute.data].data["href"]
            == "/temperatures/vs/0"
        ):
            self.startup()

        if self._device.status.attributes[Attribute.data].data["href"] == self._page:
            self.init_bool = True
            self.execute_state = int(
                self._device.status.attributes[Attribute.data].value["payload"][
                    "temperature"
                ]
            )
        return self.execute_state

    @property
    def icon(self) -> str:
        """Return Icon."""
        return "mdi:thermometer"

    @property
    def device_class(self) -> str | None:
        """Return Device Class."""
        return SensorDeviceClass.TEMPERATURE

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return unit of measurement"""
        if self._device.status.attributes[Attribute.data].data["href"] == self._page:
            self.unit_state = self._device.status.attributes[Attribute.data].value[
                "payload"
            ]["units"]
        return UNIT_MAP.get(self.unit_state) if self.unit_state else None
