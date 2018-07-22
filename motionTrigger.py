import appdaemon.plugins.hass.hassapi as hass

#
# App to turn something on when motion detected then off again after a delay if no more motion was detected
#
#
# Args:
#
# sensor: binary sensor to use as trigger
# entity_on : entity to turn on when detecting motion, can be a light, script, scene or anything else that can be turned on
# entity_off : entity to turn off when detecting motion, can be a light, script or anything else that can be turned off. Can also be a scene which will be turned on
# TODO after (optionally): Only trigger after a certain time
# after_sundown: true 
# delay: amount of time after turning on to turn off again. If not specified defaults to 70 seconds.
#
# Release Notes
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

        # Subscribe to sensors
        self.listen_event_handle_list.append(self.listen_event(self.motion_detected, "motion"))

    
    def motion_detected(self, event_name, data, kwargs):
        self.log("Motion: event_name: {}, data: {}".format(event_name,data), level = "DEBUG")
        if data["entity_id"] == self.args["sensor"]:
            if "after_sundown" in self.args:
                if self.args["after_sundown"] == True and self.sun_down():
                    if self.get_state(self.args["entity_on"]) == "off":
                        self.log("Motion detected: turning {} on".format(self.args["entity_on"]))
                        self.turn_on(self.args["entity_on"])
                        self.turned_on_by_me = True
            else:
                if self.get_state(self.args["entity_on"]) == "off":
                        self.log("Motion detected: turning {} on".format(self.args["entity_on"]))
                        self.turn_on(self.args["entity_on"])
                        self.turned_on_by_me = True
        if "delay" in self.args:
            delay = self.args["delay"]
        else:
            delay = 70
        if self.turned_on_by_me == True:
            self.cancel_timer(self.timer_handle)
            self.timer_handle = self.run_in(self.light_off, delay)
  
    def light_off(self, kwargs):
        if "entity_off" in self.args:
            self.log("Turning {} off".format(self.args["entity_off"]))
            self.turn_off(self.args["entity_off"])
            self.turned_on_by_me = False
        else:
            self.log("No entity_off defined")
        
    def terminate(self):
        self.cancel_timer(self.timer_handle)

        for listen_event_handle in self.listen_event_handle_list:
            self.cancel_listen_event(listen_event_handle)