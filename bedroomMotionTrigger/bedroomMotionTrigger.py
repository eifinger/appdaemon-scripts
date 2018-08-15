import appdaemon.plugins.hass.hassapi as hass
import globals
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
# after (optionally): Only trigger after a certain time. example: 22:00
# after_sundown (optionally): true 
# delay (optionally): amount of time after turning on to turn off again. If not specified defaults to 70 seconds.
# constraint_entities_off (optionally): list of entities which have to be off. example: light.bedroom_yeelight,light.bar_table
# constraint_entities_on (optionally): list of entities which have to be on. example: light.bedroom_yeelight,light.bar_table
# location_user_one_sensor: sensor showing room of user one. example: sensor.location_user_one
# location_user_two_sensor: device_tracker of user one. example: sensor.location_user_two
# bedroom_state: state which indicates location bedroom. example: Schlafzimmer
#
# Release Notes
#
# Version 1.1:
#   Added app_switch
#
# Version 1.0:
#   Initial Version

class BedroomMotionTrigger(hass.Hass):

    def initialize(self):
    
        self.timer_handle = None
        self.listen_event_handle_list = []
        self.listen_state_handle_list = []
        self.timer_handle_list = []

        self.turned_on_by_me = False #Giggedi

        self.app_switch = globals.get_arg(self.args,"app_switch")
        self.sensor = globals.get_arg(self.args,"sensor")
        self.entity_on = globals.get_arg(self.args,"entity_on")
        try:
            self.entity_off = globals.get_arg(self.args,"entity_off")
        except KeyError as identifier:
            self.entity_off = None
        try:
            self.after = globals.get_arg(self.args,"after")
        except KeyError as identifier:
            self.after = None
        try:
            self.after_sundown = globals.get_arg(self.args,"after_sundown")
        except KeyError as identifier:
            self.after_sundown = None
        try:
            self.delay = globals.get_arg(self.args,"delay")
        except KeyError as identifier:
            self.delay = None
        try:
            self.constraint_entities_off = globals.get_arg_list(self.args,"constraint_entities_off")
        except KeyError as identifier:
            self.constraint_entities_off = []
        try:
            self.constraint_entities_on = globals.get_arg_list(self.args,"constraint_entities_on")
        except KeyError as identifier:
            self.constraint_entities_on = []
        self.location_user_one_sensor = globals.get_arg(self.args,"location_user_one_sensor")
        self.location_user_two_sensor = globals.get_arg(self.args,"location_user_two_sensor")
        self.bedroom_state = globals.get_arg(self.args,"bedroom_state")

        # Subscribe to sensors
        self.listen_event_handle_list.append(self.listen_event(self.motion_detected, "motion"))

    
    def motion_detected(self, event_name, data, kwargs):
        if self.get_state(self.app_switch) == "on":
            turn_on = True
            self.log("Motion: event_name: {}, data: {}".format(event_name,data), level = "DEBUG")
            if data["entity_id"] != self.sensor:
                self.log("Wrong sensor.", level = "DEBUG")
                turn_on = False
            if self.after_sundown != None:
                if self.after_sundown == True and not self.sun_down():
                    self.log("Sun is not down", level = "DEBUG")
                    turn_on = False
            if self.after != None:
                after_time = datetime.datetime.combine(datetime.date.today(), datetime.time(int(self.after.split(":")[0]),int(self.after.split(":")[1])))
                if datetime.datetime.now() > after_time:
                    self.log("Now is before {}".format(self.after), level = "DEBUG")
                    turn_on = False
            for entity in self.constraint_entities_off:
                if self.get_state(entity) != "off":
                    self.log("{} is {}".format(self.friendly_name(entity), self.get_state(entity)), level = "DEBUG")
                    turn_on = False
            for entity in self.constraint_entities_on:
                if self.get_state(entity) != "on":
                    self.log("{} is {}".format(self.friendly_name(entity), self.get_state(entity)), level = "DEBUG")
                    turn_on = False
            if self.get_state(self.entity_on) != "off":
                self.log("Device is already on", level = "DEBUG")
                turn_on = False
            #Bedroom specifics
            if self.get_state(self.location_user_one_sensor) == self.bedroom_state and self.get_state(self.location_user_two_sensor) == self.bedroom_state:
                self.log("Both in bedroom", level = "DEBUG")
                turn_on = False
            if turn_on:
                self.log("Motion detected: turning {} on".format(self.entity_on))
                self.turn_on(self.entity_on)
                self.turned_on_by_me = True
            if self.delay != None:
                delay = self.delay
            else:
                delay = 70
            if self.turned_on_by_me == True:
                if self.timer_handle != None:
                    self.timer_handle_list.remove(self.timer_handle)
                    self.cancel_timer(self.timer_handle)
                self.timer_handle = self.run_in(self.light_off, delay)
                self.timer_handle_list.append(self.timer_handle)
  
    def light_off(self, kwargs):
        if self.entity_off != None:
            self.log("Turning {} off".format(self.entity_off))
            self.turn_off(self.entity_off)
            self.turned_on_by_me = False
        else:
            self.log("No entity_off defined")
        
    def terminate(self):
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)

        for listen_event_handle in self.listen_event_handle_list:
            self.cancel_listen_event(listen_event_handle)

        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)