# Home Assistant GSM IOT device Integration


## Description:
Home Assistant integration for the Charging IOT GSM device.

It generates Home Assistant sensors which they get the data by the IOT device's middleware server to get the values of the GSM device's sensors.


## References:
* [Home Assistant](https://www.home-assistant.io/), Home Assistant home page
* [Here](https://developers.home-assistant.io/docs/creating_component_index/), references to implement custom integration for Home Assistant


## How does it work:
1. Home Assistant starts when the integration is added using the UI menu (Settings/integrations/add integration), searching "niu_gsm_iot"

2. Put the middleware host and api key

3. The integration starts from the __init__ file, where the it define which platform have to start:
    - in this example starts only the platform "sensor" linked to the file `sensors.py`.

    - To add new platform we have just to add a new python file called `[platform].py`, example: to implement a light object, which in Home Assistant is controlled by the light platform, because it implements commands for the lights devices, example: led light with RGB controls

4. The method `async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:` is called for each platform, here only once.

5. In this method the GsmApi object is instantiated, implemented into the `api.py` file, to put the GSM device middleware server apis into a single file. The object GsmApi is used to collect data from the middleware server using the module requests.

6. To implement the integrations' sensors is common to implement an abstract sensor object, in this case it is the GsmSenorEntity object which inherits the SensorEntity by Home Assistant to implement the sensors' common proprieties.

7. For each sensor exposed by the middleware server api's a new class which extends the `GsmSenorEntity` object is needed.
In the case a sensor needs to compute its own state in a different way,we have to override the `update_data` method

8. Finally its called the function `async_add_entities`, passing the list formed by all the sensor object instance generated, to integrate the sensors into Home Assistant.
Here:

        async_add_entities([Asensor, Vsensor, SSensor, PSensor, kWHSensor])
