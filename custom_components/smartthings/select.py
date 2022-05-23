"""Support for select through the SmartThings cloud API."""
from __future__ import annotations

from collections import namedtuple
from collections.abc import Sequence

from homeassistant.components.select import SelectEntity

import asyncio

from pysmartthings import Attribute
from pysmartthings.device import DeviceEntity

from . import SmartThingsEntity
from .const import DATA_BROKERS, DOMAIN

Map = namedtuple(
    "map",
    "attribute select_options_attr select_command datatype name icon extra_state_attributes",
)

CAPABILITY_TO_SELECT = {
    "samsungce.lamp": [
        Map(
            "brightnessLevel",
            "supportedBrightnessLevel",
            "setBrightnessLevel",
            str,
            "Lamp Brightness Level",
            "mdi:brightness-6",
            None,
        )
    ],
    "samsungce.dustFilterAlarm": [
        Map(
            "alarmThreshold",
            "supportedAlarmThresholds",
            "setAlarmThreshold",
            int,
            "Filter Alarm Threshold",
            None,
            None,
        )
    ],
}


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add select for a config entries."""
    broker = hass.data[DOMAIN][DATA_BROKERS][config_entry.entry_id]
    selects = []
    for device in broker.devices.values():
        for capability in broker.get_assigned(device.device_id, "select"):
            maps = CAPABILITY_TO_SELECT[capability]
            selects.extend(
                [
                    SmartThingsSelect(
                        device,
                        capability,
                        m.attribute,
                        m.select_options_attr,
                        m.select_command,
                        m.datatype,
                        m.name,
                        m.icon,
                        m.extra_state_attributes,
                    )
                    for m in maps
                ]
            )

        if broker.any_assigned(device.device_id, "climate"):
            if (
                device.status.attributes[Attribute.mnmn].value == "Samsung Electronics"
                and device.type == "OCF"
            ):
                model = device.status.attributes[Attribute.mnmo].value.split("|")[0]
                supported_ac_optional_modes = [
                    str(x)
                    for x in device.status.attributes["supportedAcOptionalMode"].value
                ]
                if (
                    "motionDirect" in supported_ac_optional_modes
                    and "motionIndirect" in supported_ac_optional_modes
                ):
                    selects.extend([SamsungACMotionSensorSaver(device)])
                elif model in ("21K_REF_LCD_FHUB6.0", "ARTIK051_REF_17K"):
                    selects.extend([SamsungOcfDeliModeSelect(device)])
    async_add_entities(selects)


def get_capabilities(capabilities: Sequence[str]) -> Sequence[str] | None:
    """Return all capabilities supported if minimum required are present."""
    # Must have a value that is selectable.
    return [
        capability for capability in CAPABILITY_TO_SELECT if capability in capabilities
    ]


MOTION_SENSOR_SAVER_MODES = [
    "MotionMode_PowerSave",
    "MotionMode_Default",
    "MotionMode_Cooling",
    "MotionMode_PowerSaveOff",
    "MotionMode_DefaultOff",
    "MotionMode_CoolingOff",
]

MOTION_SENSOR_SAVER_TO_STATE = {
    "MotionMode_PowerSave": "Eco (Keeping Cool)",
    "MotionMode_Default": "Normal (Keeping Cool)",
    "MotionMode_Cooling": "Comfort (Keeping Cool)",
    "MotionMode_PowerSaveOff": "Eco (Off)",
    "MotionMode_DefaultOff": "Normal (Off)",
    "MotionMode_CoolingOff": "Comfort (Off)",
}
STATE_TO_MOTION_SENSOR_SAVER = {
    "Eco (Keeping Cool)": "MotionMode_PowerSave",
    "Normal (Keeping Cool)": "MotionMode_Default",
    "Comfort (Keeping Cool)": "MotionMode_Cooling",
    "Eco (Off)": "MotionMode_PowerSaveOff",
    "Normal (Off)": "MotionMode_DefaultOff",
    "Comfort (Off)": "MotionMode_CoolingOff",
}

DELI_OPTIONS_TO_STATE = {
    "CV_FDR_WINE": "Wine",
    "CV_FDR_DELI": "Deli",
    "CV_FDR_BEVERAGE": "Beverage",
    "CV_FDR_MEAT": "Meat",
}

STATE_TO_DELI_OPTIONS = {
    "Wine": "CV_FDR_WINE",
    "Deli": "CV_FDR_DELI",
    "Beverage": "CV_FDR_BEVERAGE",
    "Meat": "CV_FDR_MEAT",
}


class SmartThingsSelect(SmartThingsEntity, SelectEntity):
    """Define a SmartThings Select"""

    def __init__(
        self,
        device: DeviceEntity,
        capability: str,
        attribute: str,
        select_options_attr: str,
        select_command: str,
        datatype,
        name: str,
        icon: str | None,
        extra_state_attributes: str | None,
    ) -> None:
        """Init the class."""
        super().__init__(device)
        self._capability = capability
        self._attribute = attribute
        self._select_options_attr = select_options_attr
        self._select_command = select_command
        self._datatype = datatype
        self._name = name
        self._icon = icon
        self._extra_state_attributes = extra_state_attributes

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        result = await self._device.command(
            "main", self._capability, self._select_command, [self._datatype(option)]
        )
        if result:
            self._device.status.update_attribute_value(self._attribute, option)
        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_write_ha_state()

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return f"{self._device.label} {self._name}"

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self._device.device_id}.{self._attribute}"

    @property
    def options(self) -> list[str]:
        """return valid options"""
        return [
            str(x)
            for x in self._device.status.attributes[self._select_options_attr].value
        ]

    @property
    def current_option(self) -> str | None:
        """return current option"""
        return str(self._device.status.attributes[self._attribute].value)

    @property
    def unit_of_measurement(self) -> str | None:
        """Return unit of measurement"""
        return self._device.status.attributes[self._attribute].unit

    @property
    def icon(self) -> str | None:
        return self._icon


class SamsungACMotionSensorSaver(SmartThingsEntity, SelectEntity):
    """Define Samsung AC Motion Sensor Saver"""

    execute_state = str
    init_bool = False

    def startup(self):
        """Make sure that OCF page visits mode on startup"""
        tasks = []
        tasks.append(self._device.execute("/mode/vs/0"))
        asyncio.gather(*tasks)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        result = await self._device.execute(
            "/mode/vs/0",
            {"x.com.samsung.da.options": [STATE_TO_MOTION_SENSOR_SAVER[option]]},
        )
        if result:
            self._device.status.update_attribute_value(
                "data",
                {
                    "payload": {
                        "x.com.samsung.da.options": [
                            STATE_TO_MOTION_SENSOR_SAVER[option]
                        ]
                    }
                },
            )
            self.execute_state = option
        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_write_ha_state()

    @property
    def name(self) -> str:
        """Return the name of the select entity."""
        return f"{self._device.label} Motion Sensor Saver"

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self._device.device_id}_motion_sensor_saver"

    @property
    def options(self) -> list[str]:
        """return valid options"""
        modes = []
        for mode in MOTION_SENSOR_SAVER_MODES:
            if (state := MOTION_SENSOR_SAVER_TO_STATE.get(mode)) is not None:
                modes.append(state)
        return list(modes)

    @property
    def current_option(self) -> str | None:
        """return current option"""
        if not self.init_bool:
            self.startup()
        if self._device.status.attributes[Attribute.data].data["href"] == "/mode/vs/0":
            self.init_bool = True
            output = self._device.status.attributes[Attribute.data].value["payload"][
                "x.com.samsung.da.options"
            ]
            mode = [str(mode) for mode in MOTION_SENSOR_SAVER_MODES if mode in output]
            if len(mode) > 0:
                self.execute_state = MOTION_SENSOR_SAVER_TO_STATE[mode[0]]
        return self.execute_state


class SamsungOcfDeliModeSelect(SmartThingsEntity, SelectEntity):
    """Define Samsung AC Motion Sensor Saver"""

    execute_state = str
    init_bool = False

    def startup(self):
        """Make sure that OCF page visits mode on startup"""
        tasks = []
        tasks.append(self._device.execute("/mode/vs/0"))
        asyncio.gather(*tasks)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        result = await self._device.execute(
            "mode/vs/0",
            {"x.com.samsung.da.modes": [STATE_TO_DELI_OPTIONS[option]]},
        )
        if result:
            self._device.status.update_attribute_value(
                "data",
                {
                    "payload": {
                        "x.com.samsung.da.modes": [STATE_TO_DELI_OPTIONS[option]]
                    }
                },
            )
            self.execute_state = option
        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_write_ha_state()

    @property
    def name(self) -> str:
        """Return the name of the select entity."""
        return f"{self._device.label} FlexZone Mode"

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self._device.device_id}_flexzone_mode"

    @property
    def options(self) -> list[str]:
        """return valid options"""
        modes = []
        if self._device.status.attributes[Attribute.data].data["href"] == "/mode/vs/0":
            for mode in self._device.status.attributes[Attribute.data].value["payload"][
                "x.com.samsung.da.supportedOptions"
            ]:
                if (state := DELI_OPTIONS_TO_STATE.get(mode)) is not None:
                    modes.append(state)
        return list(modes)

    @property
    def current_option(self) -> str | None:
        """return current option"""
        if not self.init_bool:
            self.startup()
        if self._device.status.attributes[Attribute.data].data["href"] == "/mode/vs/0":
            self.init_bool = True
            output = self._device.status.attributes[Attribute.data].value["payload"][
                "x.com.samsung.da.modes"
            ]
            mode = [str(mode) for mode in self.options if mode in output]
            if len(mode) > 0:
                self.execute_state = DELI_OPTIONS_TO_STATE[mode[0]]
        return self.execute_state
