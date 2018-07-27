import appdaemon.plugins.hass.hassapi as hass
import globals
import datetime

#
# Special version of Motion Trigger. Only trigger when Door is not open (dont want any mosquittos) and only trigger when not both smartphones are in bedroom
#
#
# Args:
#
# sensor: binary sensor to use as trigger
# entity_on : entity to turn on when detecting motion, can be a light, script, scene or anything else that can be turned on
# entity_off (optionally): entity to turn off when detecting motion, can be a light, script or anything else that can be turned off. Can also be a scene which will be turned on
# after (optionally): Only trigger after a certain time. example: 22:00
# after_sundown (optionally): true 
# delay (optionally): amount of time after turning on to turn off again. If not specified defaults to 70 seconds.
# constraint_entities_off (optionally): list of entities which have to be off. example: light.bedroom_yeelight,light.bar_table
# constraint_entities_on (optionally): list of entities which have to be on. example: light.bedroom_yeelight,light.bar_table
#
# Release Notes
#
# Version 1.4:
#   Added options "after, constraint_entities_off and constraint_entities_on"
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

class MotionTrigger(hass.Hass):

    def initialize(self):
    
        self.timer_handle = None
        self.listen_event_handle_list = []

        self.turned_on_by_me = False #Giggedi
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
            self.constraint_entities_off = None
        try:
            self.constraint_entities_on = globals.get_arg_list(self.args,"constraint_entities_on")
        except KeyError as identifier:
            self.constraint_entities_on = None

        # Subscribe to sensors
        self.listen_event_handle_list.append(self.listen_event(self.motion_detected, "motion"))

    
    def motion_detected(self, event_name, data, kwargs):
        turn_on = True
        self.log("Motion: event_name: {}, data: {}".format(event_name,data), level = "DEBUG")
        if data["entity_id"] != self.sensor:
            turn_on = False
        if self.after_sundown != None:
            if self.after_sundown == True and not self.sun_down():
                turn_on = False
        if self.after != None:
            after_time = datetime.datetime.combine(datetime.date.today(), datetime.time(int(self.after.split(":")[0]),int(self.after.split(":")[1])))
            if datetime.datetime.now() > after_time:
                turn_on = False
        for entity in self.constraint_entities_off:
            if self.get_state(entity) != "off":
                turn_on = False
        for entity in self.constraint_entities_on:
            if self.get_state(entity) != "on":
                turn_on = False
        if self.get_state(self.entity_on) != "off":
            turn_on = False
        if turn_on:
            self.log("Motion detected: turning {} on".format(self.entity_on))
            self.turn_on(self.entity_on)
            self.turned_on_by_me = True
        if "delay"!= None:
            delay = self.delay
        else:
            delay = 70
        if self.turned_on_by_me == True:
            self.cancel_timer(self.timer_handle)
            self.timer_handle = self.run_in(self.light_off, delay)
  
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