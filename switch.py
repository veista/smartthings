"""Support for switches through the SmartThings cloud API."""
from __future__ import annotations

from collections import namedtuple
from collections.abc import Sequence

import json
import asyncio

from pysmartthings import Capability, Attribute
from pysmartthings.device import DeviceEntity

from homeassistant.components.switch import SwitchEntity

from . import SmartThingsEntity
from .const import DATA_BROKERS, DOMAIN

Map = namedtuple(
    "map",
    "attribute on_command off_command on_value off_value name extra_state_attributes",
)

CAPABILITY_TO_SWITCH = {
    Capability.switch: [
        Map(
            Attribute.switch,
            "switch_on",
            "switch_off",
            "on",
            "off",
            "Switch",
            None,
        )
    ],
    "custom.autoCleaningMode": [
        Map(
            "autoCleaningMode",
            "setAutoCleaningMode",
            "setAutoCleaningMode",
            "on",
            "off",
            "Auto Cleaning Mode",
            None,
        )
    ],
    "custom.dustFilter": [
        Map(
            None,
            "resetDustFilter",
            None,
            None,
            None,
            "Reset Dust Filter",
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
}


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add switches for a config entry."""
    broker = hass.data[DOMAIN][DATA_BROKERS][config_entry.entry_id]
    switches = []
    for device in broker.devices.values():
        for capability in broker.get_assigned(device.device_id, "switch"):
            maps = CAPABILITY_TO_SWITCH[capability]
            if capability == "custom.autoCleaningMode" or "custom.dustFilter":
                switches.extend(
                    [
                        SmartThingsCustomSwitch(
                            device,
                            capability,
                            m.attribute,
                            m.on_command,
                            m.off_command,
                            m.on_value,
                            m.off_value,
                            m.name,
                            m.extra_state_attributes,
                        )
                        for m in maps
                    ]
                )
            else:
                switches.extend(
                    [
                        SmartThingsSwitch(
                            device,
                            m.attribute,
                            m.on_command,
                            m.off_command,
                            m.on_value,
                            m.off_value,
                            m.name,
                            m.extra_state_attributes,
                        )
                        for m in maps
                    ]
                )
        if broker.any_assigned(device.device_id, "climate"):
            if Capability.execute:
                switches.extend([SamsungAcLight(device)])

    async_add_entities(switches)


def get_capabilities(capabilities: Sequence[str]) -> Sequence[str] | None:
    """Return all capabilities supported if minimum required are present."""
    # Must be able to be turned on/off.
    return [
        capability for capability in CAPABILITY_TO_SWITCH if capability in capabilities
    ]


class SmartThingsSwitch(SmartThingsEntity, SwitchEntity):
    """Define a SmartThings switch."""

    def __init__(
        self,
        device: DeviceEntity,
        attribute: str | None,
        on_command: str | None,
        off_command: str | None,
        on_value: str | int | None,
        off_value: str | int | None,
        name: str,
        extra_state_attributes: str | None,
    ) -> None:
        """Init the class."""
        super().__init__(device)
        self._attribute = attribute
        self._on_command = on_command
        self._off_command = off_command
        self._on_value = on_value
        self._off_value = off_value
        self._name = name
        self._extra_state_attributes = extra_state_attributes

    execute_state = False

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        await getattr(self._device, self._off_command)(set_status=True)
        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        await getattr(self._device, self._on_command)(set_status=True)
        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_write_ha_state()

    @property
    def name(self) -> str:
        """Return the name of the binary sensor."""
        return f"{self._device.label} {self._name}"

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        if self._attribute is not None:
            return f"{self._device.device_id}.{self._attribute}"
        return f"{self._device.device_id}.{self._name}"

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return getattr(self._device.status, self._attribute)

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


class SmartThingsCustomSwitch(SmartThingsEntity, SwitchEntity):
    """Define a SmartThings switch."""

    def __init__(
        self,
        device: DeviceEntity,
        capability: str,
        attribute: str | None,
        on_command: str | None,
        off_command: str | None,
        on_value: str | int | None,
        off_value: str | int | None,
        name: str,
        extra_state_attributes: str | None,
    ) -> None:
        """Init the class."""
        super().__init__(device)
        self._capability = capability
        self._attribute = attribute
        self._on_command = on_command
        self._off_command = off_command
        self._on_value = on_value
        self._off_value = off_value
        self._name = name
        self._extra_state_attributes = extra_state_attributes

    execute_state = False

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        if self._off_command is not None:
            if self._on_value is not None:
                await self._device.command(
                    "main", self._capability, self._off_command, [self._off_value]
                )
            else:
                await self._device.command(
                    "main", self._capability, self._off_command, []
                )
        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        if self._on_command is not None:
            if self._on_value is not None:
                await self._device.command(
                    "main", self._capability, self._on_command, [self._on_value]
                )
            else:
                await self._device.command(
                    "main", self._capability, self._on_command, []
                )

        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_write_ha_state()

    @property
    def name(self) -> str:
        """Return the name of the binary sensor."""
        return f"{self._device.label} {self._name}"

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        if self._attribute is not None:
            return f"{self._device.device_id}.{self._attribute}"
        return f"{self._device.device_id}.{self._name}"

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        if self._on_value is not None:
            if self._device.status.attributes[self._attribute].value == self._on_value:
                return True
            return False
        else:
            return self._device.status.attributes[self._attribute].value

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


class SamsungAcLight(SmartThingsEntity, SwitchEntity):
    """add samsung ocf ac light"""

    execute_state = False

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        await self._device.execute(
            "mode/vs/0", {"x.com.samsung.da.options": ["Light_On"]}
        )
        self.execute_state = False

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        await self._device.execute(
            "mode/vs/0", {"x.com.samsung.da.options": ["Light_Off"]}
        )
        self.execute_state = True

    @property
    def name(self) -> str:
        """Return the name of the binary sensor."""
        return f"{self._device.label} Light"

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self._device.device_id}.light"

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        tasks = []
        tasks.append(self._device.execute("mode/vs/0"))
        asyncio.gather(*tasks)
        output = json.dumps(self._device.status.attributes[Attribute.data].value)
        if "Light_Off" in output:
            self.execute_state = True
        elif "Light_On" in output:
            self.execute_state = False
        return self.execute_state
