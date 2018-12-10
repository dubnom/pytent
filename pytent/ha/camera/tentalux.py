"""Component for interfacing with Tentalux camera.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/tentalux/
"""
import asyncio
import logging

import aiohttp
import async_timeout
import requests

from homeassistant.components.tentalux import (
    TentaluxDevice, TENTALUX_CONTROLLER, TENTALUX_DEVICES)
from homeassistant.components.camera import (
    DEFAULT_CONTENT_TYPE, Camera)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util.async_ import run_coroutine_threadsafe

DEPENDENCIES = ['tentalux']

_LOGGER = logging.getLogger(__name__)

FRAMERATE = 1

async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    """Set up Tentalux camera."""
    devs = []
    controller = hass.data[TENTALUX_CONTROLLER]
    for (name, url) in hass.data[TENTALUX_DEVICES]['camera']:
        dev = TentaluxCamera(hass, controller, name, url)
        devs.append(dev)
    async_add_entities(devs)


class TentaluxCamera(TentaluxDevice, Camera):
    """A generic implementation of an IP camera."""

    def __init__(self, hass, controller, name, url):
        """Initialize the Tentalux camera."""
        TentaluxDevice.__init__(self, controller, name)
        Camera.__init__(self)
        self.hass = hass
        self._still_image_url = url
        self._frame_interval = 1 / FRAMERATE

        self._last_image = None

    @property
    def frame_interval(self):
        """Return the interval between frames."""
        return self._frame_interval

    def camera_image(self):
        """Return bytes of camera image."""
        return run_coroutine_threadsafe(
            self.async_camera_image(), self.hass.loop).result()

    async def async_camera_image(self):
        """Return a still image response from the camera."""
        url = self._still_image_url

        try:
            websession = async_get_clientsession(self.hass)
            with async_timeout.timeout(10, loop=self.hass.loop):
                response = await websession.get(url)
            self._last_image = await response.read()
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout getting camera image")
        except aiohttp.ClientError as err:
            _LOGGER.error("Error getting new camera image: %s", err)

        return self._last_image
