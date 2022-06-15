from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import POWER_WATT, POWER_KILO_WATT, ELECTRIC_CURRENT_AMPERE, ELECTRIC_POTENTIAL_VOLT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.util import Throttle
from datetime import timedelta

from datetime import datetime
# from .api import GsmApi


# MIDDLEWARE_SERVER_URL = ''

"middleware "
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the Glucose Sensor."""
    from .api import GsmApi
    api = GsmApi('http://127.0.0.1:5000/','apitest')
    Asensor = AmpereSensor(hass, api, 'mdi:sine-wave')
    Vsensor = VoltageSensor(hass, api, 'mdi:flash-triangle')
    SSensor = SignalSensor(hass, api, 'mdi:signal-2g')
    PSensor = PowerSensor(hass, api, 'mdi:power-socket-eu')
    kWHSensor = kWattHourSensor(hass, api, 'mdi:meter-electric')

    async_add_entities([Asensor, Vsensor, SSensor, PSensor, kWHSensor])
    


# Abstract class to implement the GSM sensors
# It defines the basic proprieties as name, if it's available, 
# a basic update function to get data from sensor
class GsmSenorEntity(SensorEntity):
    ROOT_MSG = 'msg'

    def __init__(self, hass, api, name, icon ) -> None:
        self.hass = hass
        self.api = api
        self._name = name
        self._unique_id = name
        self._state = 0
        self._attributes = None
        # self._unit_of_measurement = None
        self._icon = icon
        self._available = True if self.url_path != None else False
        #restoring last value
        self.hass.async_add_executor_job(self.update_data)
    
    
    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return self._unit_of_measurement

    @property
    def available(self):
        """Return if the sensor data are available."""
        return self._available

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return self._icon

    @property
    def unique_id(self):
        """Return the unique ID of the sensor."""
        return self._unique_id
    @property
    def should_poll(self):
        return True

    @Throttle(timedelta(minutes=30))
    def update_data(self):
        self._state = float(self.api.get_json_data()[self.url_path])
        if self.url_path == 'volt' or self.url_path == 'amper':
            self._state /= 10

    async def async_update(self):
        self.hass.async_add_executor_job(self.update_data)


class AmpereSensor(GsmSenorEntity):
    """Implementation of a Ampere GSM sensor."""
    def __init__(self, hass, api, icon) -> None:
        self._unit_of_measurement = ELECTRIC_CURRENT_AMPERE
        self.url_path = 'amper'
        super().__init__(hass, api, 'Gsm Ampere', icon)

class VoltageSensor(GsmSenorEntity):
    """Implementation of a Voltage GSM sensor."""
    def __init__(self, hass, api, icon) -> None:
        self._unit_of_measurement = ELECTRIC_POTENTIAL_VOLT
        self.url_path = 'volt'
        super().__init__(hass, api, 'Gsm Voltage', icon)

class SignalSensor(GsmSenorEntity):
    def __init__(self, hass, api, icon) -> None:
        self.url_path = 'signal'
        self._unit_of_measurement = ''
        super().__init__(hass, api, 'Gsm Signal', icon)

class PowerSensor(GsmSenorEntity):
    """Implementation of a Power GSM sensor."""
    def __init__(self, hass, api, icon) -> None:
        self._unit_of_measurement = POWER_WATT
        self.url_path = ''
        super().__init__(hass, api, 'Gsm Power', icon)

    # async def async_update(self):
    def update_data(self):
        data = self.api.get_json_data()
        # [self.ROOT_MSG]
        current = float(data['amper'])/10
        voltage = float(data['volt'])/10
        self._state = round(current * voltage, 2)


# from homeassistant.
class kWattHourSensor(GsmSenorEntity):
    def __init__(self, hass, api, icon) -> None:
        '''This sensor used the timestamp of the data to calculate the wh'''
        # to compare time
        self._old_data = {}
        name = 'kWattHour Sensor'
        self.url_path = ''
        self._unit_of_measurement = 'Kwh'
        super().__init__(hass, api, name, icon)

    #@Throttle(timedelta(minutes=1))
    def update_data(self):
        data = self.api.get_json_data()
        if self._old_data == {}:
            self._old_data = data
            return
        # [self.ROOT_MSG]
        current = float(data['amper'])/10
        voltage = float(data['volt'])/10
        watt = current * voltage
        kwatt = watt/1000
        #format "22/04/05,11:39:33"
        
        cur_time_data = datetime.strptime(data['data'], '%d/%m/%y,%H:%M:%S')
        prev_time_data = datetime.strptime(self._old_data['data'], '%d/%m/%y,%H:%M:%S')
        # prev_kwatt = self._old_data['']
        prev_current = float(self._old_data['amper'])/10
        prev_voltage = float(self._old_data['volt'])/10
        prev_watt = prev_current * prev_voltage
        prev_kwatt = prev_watt/1000
        
        delta_time_data = cur_time_data - prev_time_data
        delta_hours = (delta_time_data.seconds / 60) / 60
        rounded_status =round((kwatt - prev_kwatt) * delta_hours, 3)
        self._state = rounded_status if rounded_status >= 0.0 else 0.0
        
        #saving cur data as old data
        self._old_data = data



class LastCharge(GsmSenorEntity):
    def __init__(self, hass, api, name, kwhSensor, icon):
        self._old_data = {}
        name = 'LastChargeKwh Sensor'
        self.url_path = ''
        self._unit_of_measurement = 'Kwh'
        self.kwhSensor : kWattHourSensor = kwhSensor
        self.charging_values = []
        self.is_charging = self.kwhSensor._state >= 0.0
        super().__init__(hass, api, name, icon)


    def update_data(self):
        if self.is_charging:
            self.charging_values.append(self.kwhSensor._state)
        