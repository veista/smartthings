"""Support for climate devices through the SmartThings cloud API."""
from __future__ import annotations

import asyncio
from collections.abc import Iterable, Sequence
import logging

from pysmartthings import Attribute, Capability

from homeassistant.components.climate import DOMAIN as CLIMATE_DOMAIN, ClimateEntity
from homeassistant.components.climate.const import (
    ATTR_HVAC_MODE,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    HVACAction,
    HVACMode,
    ClimateEntityFeature,
)
from homeassistant.const import ATTR_TEMPERATURE

from . import SmartThingsEntity
from .const import DATA_BROKERS, DOMAIN, UNIT_MAP

ATTR_OPERATION_STATE = "operation_state"
MODE_TO_STATE = {
    "auto": HVACMode.HEAT_COOL,
    "cool": HVACMode.COOL,
    "eco": HVACMode.AUTO,
    "rush hour": HVACMode.AUTO,
    "emergency heat": HVACMode.HEAT,
    "heat": HVACMode.HEAT,
    "off": HVACMode.OFF,
    "wind": HVACMode.FAN_ONLY,
}
STATE_TO_MODE = {
    HVACMode.HEAT_COOL: "auto",
    HVACMode.COOL: "cool",
    HVACMode.HEAT: "heat",
    HVACMode.OFF: "off",
    HVACMode.FAN_ONLY: "wind",
}

OPERATING_STATE_TO_ACTION = {
    "cooling": HVACAction.COOLING,
    "fan only": HVACAction.FAN,
    "heating": HVACAction.HEATING,
    "idle": HVACAction.IDLE,
    "pending cool": HVACAction.COOLING,
    "pending heat": HVACAction.HEATING,
    "vent economizer": HVACAction.FAN,
}

AC_MODE_TO_STATE = {
    "auto": HVACMode.HEAT_COOL,
    "cool": HVACMode.COOL,
    "dry": HVACMode.DRY,
    "coolClean": HVACMode.COOL,
    "dryClean": HVACMode.DRY,
    "heat": HVACMode.HEAT,
    "heatClean": HVACMode.HEAT,
    "fanOnly": HVACMode.FAN_ONLY,
    "wind": HVACMode.FAN_ONLY,
}
STATE_TO_AC_MODE = {
    HVACMode.HEAT_COOL: "auto",
    HVACMode.COOL: "cool",
    HVACMode.DRY: "dry",
    HVACMode.HEAT: "heat",
    HVACMode.FAN_ONLY: "wind",
}


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add climate entities for a config entry."""
    ac_capabilities = [
        Capability.air_conditioner_mode,
        Capability.air_conditioner_fan_mode,
        Capability.switch,
        Capability.temperature_measurement,
        Capability.thermostat_cooling_setpoint,
    ]

    broker = hass.data[DOMAIN][DATA_BROKERS][config_entry.entry_id]
    entities = []
    for device in broker.devices.values():
        if not broker.any_assigned(device.device_id, CLIMATE_DOMAIN):
            continue
        if all(capability in device.capabilities for capability in ac_capabilities):
            entities.append(SmartThingsAirConditioner(device))
        else:
            entities.append(SmartThingsThermostat(device))
    async_add_entities(entities, True)


def get_capabilities(capabilities: Sequence[str]) -> Sequence[str] | None:
    """Return all capabilities supported if minimum required are present."""
    supported = [
        Capability.air_conditioner_mode,
        Capability.air_conditioner_fan_mode,
        "fanOscillationMode",
        Capability.switch,
        Capability.temperature_measurement,
        Capability.thermostat,
        Capability.thermostat_cooling_setpoint,
        Capability.thermostat_fan_mode,
        Capability.thermostat_heating_setpoint,
        Capability.thermostat_mode,
        Capability.thermostat_operating_state,
        Capability.execute,
        "custom.airConditionerOptionalMode",
        "custom.thermostatSetpointControl",
    ]
    # Can have this legacy/deprecated capability
    if Capability.thermostat in capabilities:
        return supported
    # Or must have all of these thermostat capabilities
    thermostat_capabilities = [
        Capability.temperature_measurement,
        Capability.thermostat_cooling_setpoint,
        Capability.thermostat_heating_setpoint,
        Capability.thermostat_mode,
    ]
    if all(capability in capabilities for capability in thermostat_capabilities):
        return supported
    # Or must have all of these A/C capabilities
    ac_capabilities = [
        Capability.air_conditioner_mode,
        Capability.air_conditioner_fan_mode,
        Capability.switch,
        Capability.temperature_measurement,
        Capability.thermostat_cooling_setpoint,
    ]
    if all(capability in capabilities for capability in ac_capabilities):
        return supported
    return None


class SmartThingsThermostat(SmartThingsEntity, ClimateEntity):
    """Define a SmartThings climate entities."""

    def __init__(self, device):
        """Init the class."""
        super().__init__(device)
        self._supported_features = self._determine_features()
        self._hvac_mode = None
        self._hvac_modes = None

    def _determine_features(self):
        flags = ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        if self._device.get_capability(
            Capability.thermostat_fan_mode, Capability.thermostat
        ):
            flags |= ClimateEntityFeature.FAN_MODE
        return flags

    async def async_set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        await self._device.set_thermostat_fan_mode(fan_mode, set_status=True)

        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_schedule_update_ha_state(True)

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target operation mode."""
        mode = STATE_TO_MODE[hvac_mode]
        await self._device.set_thermostat_mode(mode, set_status=True)

        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_schedule_update_ha_state(True)

    async def async_set_temperature(self, **kwargs):
        """Set new operation mode and target temperatures."""
        # Operation state
        if operation_state := kwargs.get(ATTR_HVAC_MODE):
            mode = STATE_TO_MODE[operation_state]
            await self._device.set_thermostat_mode(mode, set_status=True)
            await self.async_update()

        # Heat/cool setpoint
        heating_setpoint = None
        cooling_setpoint = None
        if self.hvac_mode == HVACMode.HEAT:
            heating_setpoint = kwargs.get(ATTR_TEMPERATURE)
        elif self.hvac_mode == HVACMode.COOL:
            cooling_setpoint = kwargs.get(ATTR_TEMPERATURE)
        else:
            heating_setpoint = kwargs.get(ATTR_TARGET_TEMP_LOW)
            cooling_setpoint = kwargs.get(ATTR_TARGET_TEMP_HIGH)
        tasks = []
        if heating_setpoint is not None:
            tasks.append(
                self._device.set_heating_setpoint(
                    round(heating_setpoint, 3), set_status=True
                )
            )
        if cooling_setpoint is not None:
            tasks.append(
                self._device.set_cooling_setpoint(
                    round(cooling_setpoint, 3), set_status=True
                )
            )
        await asyncio.gather(*tasks)

        # State is set optimistically in the commands above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_schedule_update_ha_state(True)

    async def async_update(self):
        """Update the attributes of the climate device."""
        thermostat_mode = self._device.status.thermostat_mode
        self._hvac_mode = MODE_TO_STATE.get(thermostat_mode)
        if self._hvac_mode is None:
            _LOGGER.debug(
                "Device %s (%s) returned an invalid hvac mode: %s",
                self._device.label,
                self._device.device_id,
                thermostat_mode,
            )

        modes = set()
        supported_modes = self._device.status.supported_thermostat_modes
        if isinstance(supported_modes, Iterable):
            for mode in supported_modes:
                if (state := MODE_TO_STATE.get(mode)) is not None:
                    modes.add(state)
                else:
                    _LOGGER.debug(
                        "Device %s (%s) returned an invalid supported thermostat mode: %s",
                        self._device.label,
                        self._device.device_id,
                        mode,
                    )
        else:
            _LOGGER.debug(
                "Device %s (%s) returned invalid supported thermostat modes: %s",
                self._device.label,
                self._device.device_id,
                supported_modes,
            )
        self._hvac_modes = list(modes)

    @property
    def current_humidity(self):
        """Return the current humidity."""
        return self._device.status.humidity

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._device.status.temperature

    @property
    def fan_mode(self):
        """Return the fan setting."""
        return self._device.status.thermostat_fan_mode

    @property
    def fan_modes(self):
        """Return the list of available fan modes."""
        return self._device.status.supported_thermostat_fan_modes

    @property
    def hvac_action(self) -> str | None:
        """Return the current running hvac operation if supported."""
        return OPERATING_STATE_TO_ACTION.get(
            self._device.status.thermostat_operating_state
        )

    @property
    def hvac_mode(self):
        """Return current operation ie. heat, cool, idle."""
        return self._hvac_mode

    @property
    def hvac_modes(self):
        """Return the list of available operation modes."""
        return self._hvac_modes

    @property
    def supported_features(self):
        """Return the supported features."""
        return self._supported_features

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        if self.hvac_mode == HVACMode.COOL:
            return self._device.status.cooling_setpoint
        if self.hvac_mode == HVACMode.HEAT:
            return self._device.status.heating_setpoint
        return None

    @property
    def target_temperature_high(self):
        """Return the highbound target temperature we try to reach."""
        if self.hvac_mode == HVACMode.HEAT_COOL:
            return self._device.status.cooling_setpoint
        return None

    @property
    def target_temperature_low(self):
        """Return the lowbound target temperature we try to reach."""
        if self.hvac_mode == HVACMode.HEAT_COOL:
            return self._device.status.heating_setpoint
        return None

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return UNIT_MAP.get(self._device.status.attributes[Attribute.temperature].unit)


class SmartThingsAirConditioner(SmartThingsEntity, ClimateEntity):
    """Define a SmartThings Air Conditioner."""

    is_faulty_quiet = False

    def __init__(self, device):
        """Init the class."""
        super().__init__(device)
        self._hvac_modes = None

    async def async_set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        await self._device.set_fan_mode(fan_mode, set_status=True)
        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode):
        """Set new target fan mode."""
        if self.is_faulty_quiet and preset_mode == "quiet":
            result = await self._device.execute(
                "mode/convenient/vs/0", {"x.com.samsung.da.modes": "Quiet"}
            )
        else:
            result = await self._device.command(
                "main",
                "custom.airConditionerOptionalMode",
                "setAcOptionalMode",
                [preset_mode],
            )
        if result:
            self._device.status.update_attribute_value("acOptionalMode", preset_mode)
        self.async_write_ha_state()

    async def async_set_swing_mode(self, swing_mode):
        """Set new target swing mode."""
        # await self._device.set_fan_oscillation_mode(swing_mode, set_status=True)
        result = await self._device.command(
            "main",
            "fanOscillationMode",
            "setFanOscillationMode",
            [swing_mode],
        )
        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        if result:
            self._device.status.update_attribute_value("fanOscillationMode", swing_mode)
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target operation mode."""
        if hvac_mode == HVACMode.OFF:
            await self.async_turn_off()
            return
        tasks = []
        # Turn on the device if it's off before setting mode.
        if not self._device.status.switch:
            tasks.append(self._device.switch_on(set_status=True))
        tasks.append(
            self._device.set_air_conditioner_mode(
                STATE_TO_AC_MODE[hvac_mode], set_status=True
            )
        )
        await asyncio.gather(*tasks)
        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        tasks = []
        # operation mode
        if operation_mode := kwargs.get(ATTR_HVAC_MODE):
            if operation_mode == HVACMode.OFF:
                tasks.append(self._device.switch_off(set_status=True))
            else:
                if not self._device.status.switch:
                    tasks.append(self._device.switch_on(set_status=True))
                tasks.append(self.async_set_hvac_mode(operation_mode))
        # temperature
        tasks.append(
            self._device.set_cooling_setpoint(kwargs[ATTR_TEMPERATURE], set_status=True)
        )
        await asyncio.gather(*tasks)
        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_write_ha_state()

    async def async_turn_on(self):
        """Turn device on."""
        await self._device.switch_on(set_status=True)
        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_write_ha_state()

    async def async_turn_off(self):
        """Turn device off."""
        await self._device.switch_off(set_status=True)
        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_write_ha_state()

    async def async_update(self):
        """Update the calculated fields of the AC."""
        modes = {HVACMode.OFF}
        for mode in self._device.status.supported_ac_modes:
            if (state := AC_MODE_TO_STATE.get(mode)) is not None:
                modes.add(state)
            else:
                _LOGGER.debug(
                    "Device %s (%s) returned an invalid supported AC mode: %s",
                    self._device.label,
                    self._device.device_id,
                    mode,
                )
        self._hvac_modes = list(modes)

    @property
    def current_humidity(self):
        """Return the current humidity."""
        return self._device.status.humidity

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._device.status.temperature

    @property
    def extra_state_attributes(self):
        """
        Return device specific state attributes.
        """
        attributes = []
        custom_attributes = []
        state_attributes = {}
        for attribute in attributes:
            value = getattr(self._device.status, attribute)
            if value is not None:
                state_attributes[attribute] = value
        for attribute in custom_attributes:
            value = self._device.status.attributes[attribute].value
            if value is not None:
                state_attributes[attribute] = value
        return state_attributes

    @property
    def fan_mode(self):
        """Return the fan setting."""
        return self._device.status.fan_mode

    @property
    def fan_modes(self):
        """Return the list of available fan modes."""
        return self._device.status.supported_ac_fan_modes

    @property
    def swing_mode(self):
        """Return the swing setting."""
        return self._device.status.attributes["fanOscillationMode"].value

    @property
    def swing_modes(self):
        """Give all swing modes, if attribute is found it most likely works. Samsung gives null, work-around"""
        if (
            self._device.status.attributes["supportedFanOscillationModes"].value
            is not None
        ):
            fan_oscillation_modes = [
                str(x)
                for x in self._device.status.attributes[
                    "supportedFanOscillationModes"
                ].value
            ]
            return fan_oscillation_modes
        elif self._device.status.attributes["fanOscillationMode"].value is not None:
            return ["fixed", "all", "vertical", "horizontal"]
        else:
            return None

    @property
    def preset_mode(self):
        """Return the ac optional mode setting."""

        return self._device.status.attributes["acOptionalMode"].value

    @property
    def preset_modes(self):
        """Return the list of available ac optional modes, in samsung case check that windfree cannot be selected when in heating."""
        restricted_values = ["windFree"]
        model = self._device.status.attributes[Attribute.mnmo].value.split("|")[0]

        supported_ac_optional_modes = [
            str(x)
            for x in self._device.status.attributes["supportedAcOptionalMode"].value
        ]
        if "quiet" not in supported_ac_optional_modes and model == "ARTIK051_PRAC_20K":
            supported_ac_optional_modes.append("quiet")
            self.is_faulty_quiet = True

        if self._device.status.air_conditioner_mode in ("auto", "heat"):
            if any(
                restrictedvalue in supported_ac_optional_modes
                for restrictedvalue in restricted_values
            ):
                reduced_supported_optional_modes = supported_ac_optional_modes
                reduced_supported_optional_modes.remove("windFree")
                return reduced_supported_optional_modes
        else:
            return supported_ac_optional_modes

    @property
    def hvac_mode(self):
        """Return current operation ie. heat, cool, idle."""
        if not self._device.status.switch:
            return HVACMode.OFF
        return AC_MODE_TO_STATE.get(self._device.status.air_conditioner_mode)

    @property
    def hvac_modes(self):
        """Return the list of available operation modes."""
        return self._hvac_modes

    @property
    def supported_features(self):
        """Return the supported features."""
        supported_ac_optional_modes = [
            str(x)
            for x in self._device.status.attributes["supportedAcOptionalMode"].value
        ]
        if len(supported_ac_optional_modes) == 1 and supported_ac_optional_modes[0] == "off":
            return (
                ClimateEntityFeature.TARGET_TEMPERATURE
                | ClimateEntityFeature.FAN_MODE
                | ClimateEntityFeature.SWING_MODE
            )
        return (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.FAN_MODE
            | ClimateEntityFeature.SWING_MODE
            | ClimateEntityFeature.PRESET_MODE
        )

    @property
    def max_temp(self):
        """Return the maximum temperature limit"""
        return int(self._device.status.attributes["maximumSetpoint"].value)

    @property
    def min_temp(self):
        """Return the minimum temperature limit"""
        return int(self._device.status.attributes["minimumSetpoint"].value)

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._device.status.cooling_setpoint

    @property
    def target_temperature_step(self):
        """set the target temperature step size"""
        return 1.0

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return UNIT_MAP.get(self._device.status.attributes[Attribute.temperature].unit)
