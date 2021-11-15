"""Support for numbers through the SmartThings cloud API."""
from __future__ import annotations

from collections.abc import Sequence

from homeassistant.components.select import SelectEntity

from . import SmartThingsEntity
from .const import DATA_BROKERS, DOMAIN

# Create a better system for generating numbers. Similar to sensor. All Number Entities have the same or similar properties

CAPABILITY_TO_SELECT = {
    "samsungce.dustFilterAlarm",
}


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add select for a config entries."""
    broker = hass.data[DOMAIN][DATA_BROKERS][config_entry.entry_id]
    selects = []
    for device in broker.devices.values():
        for capability in broker.get_assigned(device.device_id, "select"):
            if capability == "samsungce.dustFilterAlarm":
                selects.extend([SmartThingsSelect(device)])
    async_add_entities(selects)


def get_capabilities(capabilities: Sequence[str]) -> Sequence[str] | None:
    """Return all capabilities supported if minimum required are present."""
    # Must have a value that is selectable.
    return [
        capability for capability in CAPABILITY_TO_SELECT if capability in capabilities
    ]


class SmartThingsSelect(SmartThingsEntity, SelectEntity):
    """Define a SmartThings Select"""

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self._device.command(
            "main", "samsungce.dustFilterAlarm", "setAlarmThreshold", [int(option)]
        )
        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_write_ha_state()

    @property
    def name(self) -> str:
        """Return the name of the select entity."""
        return f"{self._device.label} Filter Alarm Threshold"

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self._device.device_id}_filter_alarm_threshold"

    @property
    def options(self) -> list[str]:
        """return valid options"""
        return [
            str(x)
            for x in self._device.status.attributes["supportedAlarmThresholds"].value
        ]

    @property
    def current_option(self) -> str | None:
        """return current option"""
        return str(self._device.status.attributes["alarmThreshold"].value)

    @property
    def unit_of_measurement(self) -> str | None:
        """Return unti of measurement"""
        return self._device.status.attributes["alarmThreshold"].unit
