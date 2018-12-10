"""Component for interfacing Tentalux lights.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/tentalux/
"""
import logging
import voluptuous as vol
from homeassistant.components.tentalux import (
    TentaluxDevice, TENTALUX_CONTROLLER, TENTALUX_DEVICES)
from homeassistant.components.light import (
    ATTR_BRIGHTNESS, SUPPORT_BRIGHTNESS, Light, PLATFORM_SCHEMA)
import homeassistant.helpers.config_validation as cv

DEPENDENCIES = ['tentalux']

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up Tentalux lights."""
    devs = []
    controller = hass.data[TENTALUX_CONTROLLER]
    for (name, addr) in hass.data[TENTALUX_DEVICES]['light']:
        dev = TentaluxLight(controller, name, addr)
        devs.append(dev)

    add_entities(devs, True)
    return True

class TentaluxLight(TentaluxDevice, Light):
    """Tentalux Light."""

    def __init__(self, controller, name, addr):
        """Create device with Addr and name."""
        TentaluxDevice.__init__(self, controller, name)
        self._addr = addr
        self._name = name
        self._level = None

    @property
    def supported_features(self):
        """Supported features."""
        return SUPPORT_BRIGHTNESS

    def turn_on(self, **kwargs):
        """Turn on the light."""
        if ATTR_BRIGHTNESS in kwargs:
            self._set_brightness(kwargs[ATTR_BRIGHTNESS])
        else:
            self._set_brightness(255)

    def turn_off(self, **kwargs):
        """Turn off the light."""
        self._set_brightness(0)

    @property
    def brightness(self):
        """Control the brightness."""
        return self._level

    def _set_brightness(self, level):
        self._controller.control_some([{'number': self._addr, 'brightness': level}])

    @property
    def is_on(self):
        """Is the light on/off."""
        return self._level != 0

    def callback(self):
        """Process potential updates."""
        if self._controller.ARBs[self._addr][2] != self._level:
            self._level = self._controller.ARBs[self._addr][2]
            return True
        return False
