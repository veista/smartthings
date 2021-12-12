"""Support for numbers through the SmartThings cloud API."""
from __future__ import annotations

from collections import namedtuple
from collections.abc import Sequence

from typing import Literal

from pysmartthings import Attribute, Capability
from pysmartthings.device import DeviceEntity

from homeassistant.components.number import NumberEntity, NumberMode

from . import SmartThingsEntity
from .const import DATA_BROKERS, DOMAIN

from homeassistant.const import PERCENTAGE

Map = namedtuple(
    "map",
    "attribute command name unit_of_measurement icon min_value max_value step mode",
)

UNITS = {"%": PERCENTAGE}

CAPABILITY_TO_NUMBER = {
    Capability.audio_volume: [
        Map(
            Attribute.volume,
            "set_volume",
            "Audio Volume",
            PERCENTAGE,
            "mdi:volume-high",
            0,
            100,
            1,
            NumberMode.AUTO,
        )
    ],
}


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add numbers for a config entries."""
    broker = hass.data[DOMAIN][DATA_BROKERS][config_entry.entry_id]
    numbers = []
    for device in broker.devices.values():
        for capability in broker.get_assigned(device.device_id, "number"):
            maps = CAPABILITY_TO_NUMBER[capability]
            numbers.extend(
                [
                    SmartThingsNumber(
                        device,
                        m.attribute,
                        m.command,
                        m.name,
                        m.unit_of_measurement,
                        m.icon,
                        m.min_value,
                        m.max_value,
                        m.step,
                        m.mode,
                    )
                    for m in maps
                ]
            )
    async_add_entities(numbers)


def get_capabilities(capabilities: Sequence[str]) -> Sequence[str] | None:
    """Return all capabilities supported if minimum required are present."""
    # Must have a numeric value that is selectable.
    return [
        capability for capability in CAPABILITY_TO_NUMBER if capability in capabilities
    ]


class SmartThingsNumber(SmartThingsEntity, NumberEntity):
    """Define a SmartThings Number."""

    def __init__(
        self,
        device: DeviceEntity,
        attribute: str,
        command: str,
        name: str,
        unit_of_measurement: str | None,
        icon: str | None,
        min_value: str | None,
        max_value: str | None,
        step: str | None,
        mode: str | None,
    ) -> None:
        """Init the class."""
        super().__init__(device)
        self._attribute = attribute
        self._command = command
        self._name = name
        self._attr_unit_of_measurement = unit_of_measurement
        self._icon = icon
        self._attr_min_value = min_value
        self._attr_max_value = max_value
        self._attr_step = step
        self._attr_mode = mode

    async def async_set_value(self, value: float) -> None:
        """Set the number value."""
        await getattr(self._device, self._command)(int(value), set_status=True)

    @property
    def name(self) -> str:
        """Return the name of the number."""
        return f"{self._device.label} {self._name}"

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self._device.device_id}.{self._attribute}"

    @property
    def value(self) -> float:
        """Return  Value."""
        return self._device.status.attributes[self._attribute].value
        
    @property
    def icon(self) -> str:
        """Return Icon."""
        return self._icon

    @property
    def min_value(self) -> float:
        """Define mimimum level."""
        return self._attr_min_value

    @property
    def max_value(self) -> float:
        """Define maximum level."""
        return self._attr_max_value

    @property
    def step(self) -> float:
        """Define stepping size"""
        return self._attr_step

    @property
    def unit_of_measurement(self) -> str | None:
        """Return unit of measurement"""
        unit = self._device.status.attributes[self._attribute].unit
        return UNITS.get(unit, unit) if unit else self._attr_unit_of_measurement

    @property
    def mode(self) -> Literal["auto", "slider", "box"]:
        """Return representation mode"""
        return self._attr_mode
