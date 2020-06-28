import appdaemon.plugins.hass.hassapi as hass  # pylint: disable=import-error
import datetime

#
# Special version of Motion Trigger. Only trigger when Door is not open (dont want any mosquittos) and only trigger when not both smartphones are in bedroom
#
#
# Args:
#
# app_switch: on/off switch for this app. example: input_boolean.turn_fan_on_when_hot
# sensor: binary sensor to use as trigger
# entity_on : entity to turn on when detecting motion, can be a light, script, scene or anything else that can be turned on
# entity_off (optionally): entity to turn off when detecting motion, can be a light, script or anything else that can be turned off. Can also be a scene which will be turned on
# sensor_type: Possible values: xiaomi, zigbee2mqtt, deconz. Default: xiaomi
# after (optionally): Only trigger after a certain time. example: 22:00
# after_sundown (optionally): true
# delay (optionally): amount of time after turning on to turn off again. If not specified defaults to 70 seconds. example: 10
#                     if an input_number is defined it will automatically take the delay from there. example: input_number.motionTrigger_delay
# turn_on_constraint_entities_off (optionally): list of entities which have to be off for entity to be turned on. example: light.bedroom_yeelight,light.bar_table
# turn_on_constraint_entities_on (optionally): list of entities which have to be on for entity to be turned on. example: light.bedroom_yeelight,light.bar_table
# turn_off_constraint_entities_off (optionally): list of entities which have to be off for entity to be turned off. example: light.bedroom_yeelight,light.bar_table
# turn_off_constraint_entities_on (optionally): list of entities which have to be on for entity to be turned off. example: light.bedroom_yeelight,light.bar_table
#
# Release Notes
#
# Version 1.10.1:
#   always log No entity_off defined
#
# Version 1.10:
#   wait with turn_off till sensor is really off
#
# Version 1.9:
#   introduced turn_on_constraints and turn_off_constraints
#
# Version 1.8:
#   support for input_number as delay and delay starts on last motion not when state changes to off
#
# Version 1.7:
#   support for zigbee2mqtt and xiaomi motion sensors
#
# Version 1.6:
#   message now directly in own yaml instead of message module
#
# Version 1.5:
#   Added app_switch
#
# Version 1.4:
#   Added options "after, turn_on_constraint_entities_off and turn_on_constraint_entities_on"
#
# Version 1.3:
#   Only turn off entity if it was turned on by this app
#
# Version 1.2:
#   Add after_sundown argument
#
# Version 1.1:
#   Add ability for other apps to cancel the timer
#
# Version 1.0:
#   Initial Version

SENSOR_TYPE_XIAOMI = "xiaomi"
SENSOR_TYPE_ZIGBEE2MQTT = "zigbee2mqtt"
SENSOR_TYPE_DECONZ = "deconz"


class MotionTrigger(hass.Hass):
    def initialize(self):

        self.timer_handle = None
        self.listen_event_handle_list = []
        self.listen_state_handle_list = []
        self.timer_handle_list = []

        self.turned_on_by_me = False  # Giggedi

        self.app_switch = self.args["app_switch"]
        self.sensor = self.args["sensor"]
        self.entity_on = self.args["entity_on"]
        self.entity_off = self.args["entity_off"]
        try:
            self.sensor_type = self.args["sensor_type"]
        except KeyError:
            self.sensor_type = SENSOR_TYPE_ZIGBEE2MQTT
        self.after = self.args.get("after")
        self.after_sundown = self.args.get("after_sundown")
        try:
            self.delay = self.args["delay"]
            try:
                if self.delay.startswith("input_number"):
                    self.delay_entity = self.delay
                    self.delay = int(self.get_state(self.delay_entity).split(".")[0])
                    self.listen_state_handle_list.append(
                        self.listen_state(self.delay_changed, self.delay_entity)
                    )
            except AttributeError:  # does not have attribute 'startswith' -> is not of type string
                pass
            self.log("Delay changed to : {}".format(self.delay))
        except KeyError:
            self.delay = 90
        try:
            self.turn_on_constraint_entities_off = self.args[
                "turn_on_constraint_entities_off"
            ].split(",")
        except KeyError:
            self.turn_on_constraint_entities_off = []
        try:
            self.turn_on_constraint_entities_on = self.args[
                "turn_on_constraint_entities_on"
            ].split(",")
        except KeyError:
            self.turn_on_constraint_entities_on = []
        try:
            self.turn_off_constraint_entities_off = self.args[
                "turn_off_constraint_entities_off"
            ].split(",")
        except KeyError:
            self.turn_off_constraint_entities_off = []
        try:
            self.turn_off_constraint_entities_on = self.args[
                "turn_off_constraint_entities_on"
            ].split(",")
        except KeyError:
            self.turn_off_constraint_entities_on = []

        # Subscribe to sensors
        if self.sensor_type == SENSOR_TYPE_XIAOMI:
            self.listen_event_handle_list.append(
                self.listen_event(self.motion_event_detected, "xiaomi_aqara.motion")
            )
        elif self.sensor_type in [SENSOR_TYPE_ZIGBEE2MQTT, SENSOR_TYPE_DECONZ]:
            self.listen_state_handle_list.append(
                self.listen_state(self.state_changed, self.sensor)
            )
        else:
            self.log(f"Unknown sensor_type: {self.sensor_type}", level="ERROR")

    def delay_changed(self, entity, attribute, old, new, kwargs):
        self.delay = int(self.get_state(self.delay_entity).split(".")[0])
        self.log(f"Delay changed to : {self.delay}")

    def motion_event_detected(self, event_name, data, kwargs):
        if self.get_state(self.app_switch) == "on":
            if data["entity_id"] == self.sensor:
                self.turn_on_callback(None)

    def state_changed(self, entity, attribute, old, new, kwargs):
        if self.get_state(self.app_switch) == "on":
            if new == "on":
                self.turn_on_callback(None)

    def turn_on_callback(self, kwargs):
        self.log(f"Motion detected on sensor: {self.friendly_name(self.sensor)}",)
        turn_on = True
        if self.after_sundown is not None:
            if self.after_sundown and not self.sun_down():
                turn_on = False
                self.log("Is not after sundown")
        if self.after is not None:
            after_time = datetime.datetime.combine(
                datetime.date.today(),
                datetime.time(
                    int(self.after.split(":")[0]), int(self.after.split(":")[1])
                ),
            )
            if datetime.datetime.now() > after_time:
                turn_on = False
                self.log(f"Now is before {self.after}")
        for entity in self.turn_on_constraint_entities_off:
            entity_state = self.get_state(entity)
            if entity_state != "off":
                turn_on = False
                self.log(f"{entity} is still {entity_state}")
                break
        for entity in self.turn_on_constraint_entities_on:
            entity_state = self.get_state(entity)
            if entity_state != "on":
                turn_on = False
                self.log(f"{entity} is still {entity_state}")
                break
        if turn_on and self.get_state(self.entity_on) == "off":
            self.log(f"Motion detected: turning {self.entity_on} on")
            self.turn_on(self.entity_on)
            self.turned_on_by_me = True
        if self.turned_on_by_me and turn_on:
            self.reset_timer()

    def turn_off_callback(self, kwargs):
        if self.get_state(self.sensor) == "on":
            self.log(f"{self.sensor} is still on")
            self.reset_timer()
        else:
            turn_off = True
            if self.entity_off is not None:
                for entity in self.turn_off_constraint_entities_off:
                    entity_state = self.get_state(entity)
                    if entity_state != "off":
                        turn_off = False
                        self.log(f"{entity} is still {entity_state}")
                        break
                for entity in self.turn_off_constraint_entities_on:
                    entity_state = self.get_state(entity)
                    if entity_state != "on":
                        turn_off = False
                        self.log(f"{entity} is still {entity_state}")
                        break
                if turn_off:
                    self.log(f"Turning {self.entity_off} off")
                    self.turn_off(self.entity_off)
                    self.turned_on_by_me = False
            else:
                self.log("No entity_off defined.")

    def reset_timer(self):
        if self.timer_handle is not None:
            self.log("Resetting timer")
            self.timer_handle_list.remove(self.timer_handle)
            self.cancel_timer(self.timer_handle)
        self.log(f"Will turn off in {self.delay}s")
        self.timer_handle = self.run_in(self.turn_off_callback, self.delay)
        self.timer_handle_list.append(self.timer_handle)

    def terminate(self):
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)

        for listen_event_handle in self.listen_event_handle_list:
            self.cancel_listen_event(listen_event_handle)

        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
