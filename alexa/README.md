# Alexa Intents

Intents for [Alexa-Appdaemon-App](https://github.com/ReneTode/Alexa-Appdaemon-App) from [Rene Tode](https://github.com/ReneTode).

To set it up for yourself follow [this](https://github.com/ReneTode/Alexa-Appdaemon-App/blob/master/alexa%20skill%20tutorial.md) tutorial

## listService

Supply friendly names and known entities for other alexa skills.
This is needed as this is a custom Alexa App and has nothing to do with HA Cloud / Alexa integration

## turnEntityOffInX

Ask Alexa to turn something off in a set amount of minutes.

Only works with entities defined under *switchable* in [listService.yaml](https://github.com/eifinger/appdaemon-scripts/blob/master/alexa/listService/listService.yaml)

``Alexa tell Home Assistant to turn off Ventilator in 10 Minutes``

```yaml
turnEntityOffInXIntent:
  module: turnEntityOffInXIntent
  class: TurnEntityOffInXIntent
  language: DE
  textLine: "Okay Homeassistant schaltet {{device}} in"
  Error: <p>Ich habe nicht richtig verstanden welches geraet soll ich ausschalten?</p>
  unreadableState: "unlesbar fuer mich"
  dependencies:
   - listService
```

## windowsOpen

Will tell you if any windows / doors are open and/or tilted

Only works with entities defined under *window*/*door*/*door_tilted* in [listService.yaml](https://github.com/eifinger/appdaemon-scripts/blob/master/alexa/listService/listService.yaml)

``Alexa ask Home Assistant whether all windows are closed``

```yaml
windowsOpenIntent:
  module: windowsOpenIntent
  class: WindowsOpenIntent
  language: DE
  textLineClosed: "Alle Fenster und Türen sind zu"
  #textLineClosed: "All windows and doors are closed"
  textLineWindowOpen: "Folgende Fenster sind noch offen"
  #textLineWindowOpen: "The following windows are stil open..."
  textLineDoorOpen: "Folgende Türen sind noch offen"
  #textLineDoorOpen: "The following doors are still open"
  textLineDoorTilted: "Die folgenden Türen sind noch gekippt"
  #textLineDoorTilted: "The following doors are tilted"
  Error: <p>Ich habe dich nicht richtig verstanden</p>
  unreadableState: "unlesbar fuer mich"
  dependencies:
   - listService
```

## nextBusIntent

Will tell you the next departure of a bus/train of a [RMV](https://www.home-assistant.io/components/sensor.rmvtransport/) sensor

``Alexa ask Home Assistant when the next bus departs``

```yaml
nextBusIntent:
  module: nextBusIntent
  class: nextBusIntent
  textLine: "Linie {} fährt in {} Minuten"
  #textLine: "Line {} departs in {} minutes"
  Error: <p>Ich habe nicht richtig verstanden was du meinst</p>
  sensor: sensor.nach_bruckenkopf
  global_dependencies:
    - globals
```

## remindMeOfXWhenZoneIntent

CURRENTLY DOES NOT WORK BECAUSE ALEXA DOES NOT ALLOW INTENTS CONTAINING REMINDERS

Will send you a reminder over the notification service when you leave/enter a zone.

``Alexa tell Home Assistant to remind me of <> when entering work``

```yaml
remindMeOfXWhenZoneIntent:
  module: remindMeOfXWhenZoneIntent
  class: RemindMeOfXWhenZoneIntent
  device_tracker: person.kevin
  notify_name: group_notifications
  Error: <p>Es ist etwas schief gegangen</p>
  textLine: "Okay ich erinnere dich an {{reminder}} wenn du {{zone}} "
  textEnter: "erreichst"
  textLeave: "verlässt"
  remindMessageSkeleton: "Ich sollte dich erinnern an "
  zoneMapping:
    arbeit: work
    hause: home
    elmo: elmo
  dependencies:
    - Notifier
  global_dependencies:
    - globals
```
