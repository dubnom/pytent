"""Component for interfacing Tentalux scenes.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/tentalux/
"""
import logging
from homeassistant.components.tentalux import (
    TentaluxDevice, TENTALUX_CONTROLLER, TENTALUX_DEVICES)
from homeassistant.components.scene import Scene

DEPENDENCIES = ['tentalux']

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up Tentalux scenes."""
    devs = []
    controller = hass.data[TENTALUX_CONTROLLER]
    for (name, pose) in hass.data[TENTALUX_DEVICES]['scene']:
        dev = TentaluxScene(controller, name, pose)
        devs.append(dev)

    add_entities(devs, True)
    return True

class TentaluxScene(TentaluxDevice, Scene):
    """Tentalux Scene."""

    def __init__(self, controller, name, pose):
        """Create scene with addr, num, and name."""
        TentaluxDevice.__init__(self, controller, name)
        self._pose = pose

    async def async_activate(self):
        """Activate the scene."""
        self._controller.set_pose(self._pose)
