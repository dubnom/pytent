"""Platform for interfacing to Tentalux lighting fixtures.

light, scene, camera

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/tentalux/
"""
import logging
import voluptuous as vol
import requests
import json
import time
from threading import Thread
from homeassistant.const import (
    CONF_HOST, CONF_PORT, CONF_NAME, EVENT_HOMEASSISTANT_STOP)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import discovery
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

TENTALUX_CONTROLLER = 'tentalux_controller'
TENTALUX_DEVICES = 'tentalux_devices'

DOMAIN = 'tentalux'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PORT): cv.port,
    }),
}, extra=vol.ALLOW_EXTRA)

POLLING_FREQ = .5


def setup(hass, base_config):
    """Start Tentalux platform."""
    config = base_config.get(DOMAIN)
    host = config[CONF_HOST]
    port = config[CONF_PORT]
    name = 'tentalux'

    controller = TentaluxController(host, port)
    controller.connect()

    devs = {'light': [], 'scene': [], 'camera': []}
    # One light for every tentacle
    for arm in range(controller.arms):
        dev_name = '%s arm %d' % (name, arm)
        devs['light'].append((dev_name, arm))
        
    # Create scenes for each pose and movement
    for pose in controller.get_poses():
        devs['scene'].append(('%s %s' % (name, pose), pose))
    
    # Create camera
    devs['camera'].append(('%s camera' % name, controller.get_camera_url()))

    hass.data[TENTALUX_CONTROLLER] = controller
    hass.data[TENTALUX_DEVICES] = devs
    for component in devs.keys():
        discovery.load_platform(hass, component, DOMAIN, None, base_config)

    def cleanup(event):
        controller.close()

    hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, cleanup)
    return True


class TentaluxController(Thread):
    """Interface between HASS and Tentalux."""
    arms = None
    ARBs = None
    
    def __init__(self, host, port):
        """Host and port of Tentalux."""
        Thread.__init__(self)
        self._host = host
        self._port = port
        self._url = '%s:%d' % (host, port)
        self._subscribers = []
        self._running = False

    def connect(self):
        """Start the status polling."""
        self.status()
        self.start()

    def run(self):
        self._running = True
        while self._running:
            self.status()
            time.sleep(POLLING_FREQ)

    def subscribe(self, device):
        """Add a device to subscribe to events."""
        self._subscribers.append(device)

    def control_some(self, data = [{}]):
        """Send a command to Tentalux and get status."""
        response = requests.post(self._url + '/controlsome', data={'data': json.dumps(data)})
        self._process_state(response)

    def status(self):
        """Request status."""
        response = requests.post(self._url + '/status')
        data = response.json()
        self._process_state(response)

    def _process_state(self, response):
        """Process Tentalux state information."""
        data = response.json()
        self.ARBs = data['ARBs']
        self.arms = len(self.ARBs)

        # Tell all related components that data may have changed.
        for sub in self._subscribers:
            if sub.callback():
                sub.schedule_update_ha_state()

    def get_poses(self):
        """Query Tentalux poses."""
        response = requests.get(self._url + '/q_poses')
        data = response.json()
        return data

    def set_pose(self, pose):
        """Set a Tentalux pose (scene)."""
        response = requests.post(self._url + '/s_pose', data = {'pose': pose})
        self._process_state(response)

    def get_camera_url(self):
        """URL of the camera image."""
        return self._url + '/camera'

    def close(self):
        """Close the connection."""
        self._running = False
        time.sleep(POLLING_FREQ)


class TentaluxDevice(Entity):
    """Base class of a tentalux device."""

    def __init__(self, controller, name):
        """Controller and name of the device."""
        self._name = name
        self._controller = controller

    async def async_added_to_hass(self):
        """Register callback."""
        self.hass.async_add_job(self._controller.subscribe, self)

    @property
    def name(self):
        """Device name."""
        return self._name

    @property
    def should_poll(self):
        """No need to poll."""
        return False

    def callback(self):
        """Run when device potentially changes state."""
        return False
