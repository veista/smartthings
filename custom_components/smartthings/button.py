"""Support for buttons through the SmartThings cloud API."""
from __future__ import annotations

from collections import namedtuple
from collections.abc import Sequence

from pysmartthings.device import DeviceEntity

from homeassistant.components.button import ButtonEntity

from . import SmartThingsEntity
from .const import DATA_BROKERS, DOMAIN

Map = namedtuple(
    "map",
    "button_command name icon device_class extra_state_attributes",
)

CAPABILITY_TO_BUTTON = {
    "custom.dustFilter": [
        Map(
            "resetDustFilter",
            "Reset Dust Filter",
            "mdi:air-filter",
            None,
            [
                "dustFilterUsageStep",
                "dustFilterUsage",
                "dustFilterLastResetDate",
                "dustFilterStatus",
                "dustFilterCapacity",
                "dustFilterResetType",
            ],
        )
    ],
    "custom.waterFilter": [
        Map(
            "resetWaterFilter",
            "Reset Water Filter",
            "mdi:air-filter",
            None,
            [
                "waterFilterUsageStep",
                "waterFilterUsage",
                "waterFilterStatus",
                "waterFilterResetType",
            ],
        )
    ],
}


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add switches for a config entry."""
    broker = hass.data[DOMAIN][DATA_BROKERS][config_entry.entry_id]
    buttons = []
    for device in broker.devices.values():
        for capability in broker.get_assigned(device.device_id, "button"):
            maps = CAPABILITY_TO_BUTTON[capability]
            buttons.extend(
                [
                    SmartThingsButton(
                        device,
                        capability,
                        m.button_command,
                        m.name,
                        m.icon,
                        m.device_class,
                        m.extra_state_attributes,
                    )
                    for m in maps
                ]
            )

    async_add_entities(buttons)


def get_capabilities(capabilities: Sequence[str]) -> Sequence[str] | None:
    """Return all capabilities supported if minimum required are present."""
    # Must be able to be turned on.
    return [
        capability for capability in CAPABILITY_TO_BUTTON if capability in capabilities
    ]


class SmartThingsButton(SmartThingsEntity, ButtonEntity):
    """Define a SmartThings button."""

    def __init__(
        self,
        device: DeviceEntity,
        capability: str,
        button_command: str | None,
        name: str,
        icon: str | None,
        device_class: str | None,
        extra_state_attributes: str | None,
    ) -> None:
        """Init the class."""
        super().__init__(device)
        self._capability = capability
        self._button_command = button_command
        self._name = name
        self._icon = icon
        self._attr_device_class = device_class
        self._extra_state_attributes = extra_state_attributes

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._device.command("main", self._capability, self._button_command, [])

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return f"{self._device.label} {self._name}"

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self._device.device_id}.{self._name}"

    @property
    def icon(self) -> str | None:
        return self._icon

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes."""
        state_attributes = {}
        if self._extra_state_attributes is not None:
            attributes = self._extra_state_attributes
            for attribute in attributes:
                value = self._device.status.attributes[attribute].value
                if value is not None:
                    state_attributes[attribute] = value
        return state_attributes
