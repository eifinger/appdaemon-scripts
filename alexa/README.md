# Alexa Intents

Intents for [Alexa-Appdaemon-App](https://github.com/ReneTode/Alexa-Appdaemon-App) from [Rene Tode](https://github.com/ReneTode).

To set it up for yourself follow [this](https://github.com/ReneTode/Alexa-Appdaemon-App/blob/master/alexa%20skill%20tutorial.md) tutorial

## listService
Supply friendly names and known entities for other alexa skills.
This is needed as this is a custom Alexa App and has nothing to do with HA Cloud / Alexa integration
## turnEntityOffInX
Ask Alexa to turn something off in a set amount of minutes.

Only works with entities defined in under *switchable* in [listService.yaml](https://github.com/eifinger/appdaemon-scripts/blob/master/alexa/listService/listService.yaml)

``Alexa tell Home Assistant to turn off Ventilator in 10 Minutes``

## windowsOpen
Will tell you if any windows / doors are open and/or tilted

Only works with entities defined in under *window*/*door*/*door_tilted* in [listService.yaml](https://github.com/eifinger/appdaemon-scripts/blob/master/alexa/listService/listService.yaml)

``Alexa ask Home Assistant whether all windows are closed``