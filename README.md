# appdaemon-scripts
This is the repository containing all my Appdaemon apps.

Used together with my Homeassistant config which you can find here:

[https://github.com/eifinger/homeassistant-config](https://github.com/eifinger/homeassistant-config)

I run Appdaemon in a Docker Container alongside my Homeassistant Container. I use Appdaemon for all my automations since I am a programmer myself and it provides me with all the possibilities of the Python world and a far better debugging experience than [HA Automations](https://www.home-assistant.io/getting-started/automation/) or [nodered](https://nodered.org/).

This is a continouus work in progress and I am no real Python programmer. So any comments are highly appreciated.

## General Remarks
I tried to write each App in this repository with reusability in mind. This means that every app in here has a short documentation and is (if possible) written to be easily adjusted to your environment and your needs.

### globals and secrets
As there is currently no functionality for secrets like there is for the HA config I am using [globals.py](globals.py) where I implemented the methods ``get_arg`` and ``get_arg_list`` which do nothing else than the standard ``self.args["argname"]`` but if the argument starts with ``secret`` it will search for actual value of the argument using a dictionary in the module ``secrets.py``. As I don't upload this file to github I included the file [travis_secrets.py](travis_secrets.py) to make it easier to retrace for others.

## App list

### Alexa Intents

Are explained [here](alexa/README.md)

### Alarm Clock
Alarm Clock App inspired by [this](https://community.home-assistant.io/t/creating-a-alarm-clock/410) forum post.
It fades in my bedroom light and sends a notifcation. The fade in and alarm time is defined by input_number sliders in HA

### Bedroom Motiontrigger
Special version of Motion Trigger. Only trigger when Door is not open (dont want any mosquittos) and only trigger when not both smartphones are in bedroom

### Button Clicked
My multipurpose App to link any switch/light to a Xiaomi Button

### Coming Home
When the front door openes and no one was home before this will turn on something. I am using it to turn on the light (if the sun is down) and turn on the receiver so I can hear Alexa

### Detect Door Open When Going to Bed
During this hot summer in Germany we somethimes forgot to close the terrace door before going to bed. This will check if the Xiaomi Door/Window Sensor reports the door being open if the [sleepmode](sleepModeHandler/sleepModeHandler.py) is turned on.

### Detect Wrong State When Leaving
Checks a list of entities which should be on/off when everybody left the house. If something isn't right it will try to turn it off (e.g. a light) and send a notification.

### Eventmonitor
Monitor all events. Useful for debugging and developing

### Google Travel Time
Monitors my Google Travel Time Sensors e.g. between home and work. I can enable an input_boolean in HA which causes this App to send me a notication as soon as the traffic is in an acceptable range. I use this drive to/from work when there is the least traffic.

### Heading To Zone Notifier
Currently not used

### Home Arrival Notifier
Greet the person coming home with a notification

### Is Home Determiner
Controls an input_boolean "isHome" which is used as a trigger for other Apps.
The state depends on other input_booleans controlled by the [isUserHomeDeterminer](isUserHomeDeterminer/isUserHomeDeterminer.py)

### Is User Home Determiner
The GPS Logger tells me where someone is. But I want to know for sure who just came in the door.
App to toggle an input boolean when a person enters or leaves home.
This is determined based on a combination of a GPS device tracker and the door sensor.
- If the door sensor opens and the device_tracker changed to "home" in the last self.delay minutes this means someone got home
- If the door sensor opens and the device_tracker changes to "not_home" in the next self.delay minutes this means someone left home

### leavingZoneNotifier
Notify if a user is leaving a zone after being there for a certain amount of time. I use this to notify my SO that I am leaving work and driving home

### motionTrigger
Turn something on/off when a motion sensor turns on. Automatically turn it off again after a delay.

### newWifiDeviceNotify
Actually a wrong name. This will send me a notification when any device_tracker component detects a new device. I initally thought to use this as a security feature but found it quite useful when adding new Sonoff switches and such. I get a notification if the setup was successfull.

### nextAppointmentLeaveNotifier
Send me a notification when it is time to leave for my next appointment based on my current location. Inspired by [this](https://community.home-assistant.io/t/text-to-speech-notification-to-leave-for-appointment/8689) blog post.
- Selectable travel mode (car/bus/walk/bike)
- Only for google calendar events which have a location
- Adjustable offset when to notify
- Includes a direct Google Maps Navigation Link in Notification Message
Saved my ass quite a few times

### notifyFailedLogin
Send a notification on a failed login.

### notifyOfActionWhenAway
Notify me of any event for a list of entities when no one is at home.
For example a door being openend or a motion sensor triggered

### plantWateringNotifier
Remind us to water the plants in the morning when the precipiation propability is too low. This uses a Telegram Chatbot. We can press a button in the notification to tell the App that we watered the plants. If we don't do that we get reminded again in the evening.

### pollenNotifier
Notify in the morning if any monitored pollen level is above a threshold.

### PowerUsageNotification
Notify when the Washingmachine or Dishwasher started/finished. Using power measured by TP HS110 Plugs like [this one](https://www.amazon.de/dp/B017X72IES/ref=twister_B07CQBCZ5G)

### RoomBasedLightControl - BETA
Turn the light on based on which room my smartphone is currently being determined by [find3](https://github.com/schollz/find3)

### sleepModeHandler
Set an input_boolean on/off. Used as a trigger for other Apps.

### standardSetter
Set back some HA entities back to their standard values.
Configurable in the HA frontend

### turnFanOnWhenHot
Turns the Fan on when the temperature is above a configurable threshold and someone is in the room ([find3](https://github.com/schollz/find3))

### turnOffBarAfterRestart
As I sometimes restart HA when working on it from remote I turn the Bar lights to red with [this script](https://github.com/eifinger/homeassistant-config/blob/master/updateHomeassistant.sh). This way everyone can see HA is currently unavailable. If it comes back up again this app will turn the light green and then off. 

### facebox - IN DEVELOPMENT
Use Facebox to announce who is at the door.
Automatically send a notfication if an unkwon face is detected.
Automatic selflearning with reinforced learning based on a telegram chatbot.

# Thanks
Some of the Apps are taken from the official examples and many based on or at least inspired by [Rene Tode](https://github.com/ReneTode). For example his absolutely fantastic [Alexa-Appdaemon-App](https://github.com/ReneTode/Alexa-Appdaemon-App).