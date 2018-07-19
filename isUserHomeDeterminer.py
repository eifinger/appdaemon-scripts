import appdaemon.plugins.hass.hassapi as hass
import messages
import globals
import datetime 
import requests
#
# App to toggle an input boolean when a person enters or leaves home.
# This is determined based on a combination of a GPS device tracker and the door sensor.
#
# - If the door sensor opens and the device_tracker changed to "home" in the last self.delay minutes this means someone got home
# - If the door sensor opens and the device_tracker changes to "not_home" in the next self.delay minutes this means someone left home
#
# Args:
#
# input_boolean: input_boolean which shows if someone is home e.g. input_boolean.isHome
# device_tracker: device tracker of the user to track e.g. device_tracker.simon
# door_sensor: Door sensor which indicated the frontdoor opened e.g. binary_sensor.door_window_sensor_158d000126a57b
# Release Notes
#
# Version 1.1:
#   Set when initializing (also when HA restarts)
#
# Version 1.0:
#   Initial Version

class IsUserHomeDeterminer(hass.Hass):

    def initialize(self):
        self.listen_state_handle_list = []
        self.timer_handle_list = []

        self.delay = 600

        self.input_boolean = globals.get_arg(self.args,"input_boolean")
        self.device_tracker = globals.get_arg(self.args,"device_tracker")
        self.door_sensor = globals.get_arg(self.args,"door_sensor")

        device_tracker_state = self.get_state(self.device_tracker, attribute = "all")
        if device_tracker_state["state"]  == "home":
            self.log("User is home")
            self.timer_handle_list.append(self.run_in(self.turn_on_callback, 0, turn_on_entity = self.input_boolean))
        else:
            self.log("User is not home")
            self.timer_handle_list.append(self.run_in(self.turn_off_callback, 0, turn_off_entity = self.input_boolean))

        self.listen_state_handle_list.append(self.listen_state(self.state_change, self.door_sensor))
        
    def state_change(self, entity, attribute, old, new, kwargs):
        if new != "" and new != old:
            self.log("{} changed from {} to {}".format(entity,old,new), level = "DEBUG")
            if new == "off" and old == "on":
                device_tracker_state = self.get_state(self.device_tracker, attribute = "all")
                self.log("device_tracker_state: {}".format(device_tracker_state), level = "DEBUG")
                last_changed = device_tracker_state["last_changed"]
                self.log("last_changed: {}".format(last_changed))
                #User got home: Device tracker changed to home before door sensor triggered
                if device_tracker_state["state"]  == "home" and (datetime.datetime.now(datetime.timezone.utc) - self.convert_utc(last_changed) ) < datetime.timedelta(seconds=self.delay):
                    self.log("User got home")
                    self.turn_on(self.input_boolean)
                #User got home: Device tracker is still not home. Wait if it changes to home in the next self.delay seconds
                elif device_tracker_state["state"]  != "home":
                    self.log("Wait for device tracker to change to 'home'")
                    self.timer_handle_list.append(self.run_in(self.check_if_user_got_home,self.delay))
                #User left home: Device tracker is still home.  Wait if it changes to home in the next self.delay seconds
                elif device_tracker_state["state"]  == "home":
                    self.log("Wait for device tracker to change to 'not_home'")
                    self.timer_handle_list.append(self.run_in(self.check_if_user_left_home,self.delay))

    def check_if_user_left_home(self, *kwargs):
        device_tracker_state = self.get_state(self.device_tracker, attribute = "all")
        self.log("device_tracker_state: {}".format(device_tracker_state), level = "DEBUG")
        if device_tracker_state["state"]  != "home":
            self.log("User left home")
            self.turn_off(self.input_boolean)

    def check_if_user_got_home(self, *kwargs):
        device_tracker_state = self.get_state(self.device_tracker, attribute = "all")
        self.log("device_tracker_state: {}".format(device_tracker_state), level = "DEBUG")
        if device_tracker_state["state"]  == "home":
            self.log("User got home")
            self.turn_on(self.input_boolean)

    def turn_on_callback(self, **kwargs):
        """This is needed because the turn_on command can result in a HTTP 503 when homeassistant is restarting"""
        try:
            self.turn_on(kwargs["turn_on_entity"])
        except requests.exceptions.HTTPError as exception:
            self.log("Error trying to turn on entity. Will try again in 1s. Error: {}".format(exception), level = "WARNING")
            self.timer_handle_list.append(self.run_in(self.turn_on_callback,1))

    def turn_off_callback(self, kwargs):
        """This is needed because the turn_off command can result in a HTTP 503 when homeassistant is restarting"""
        try:
            self.turn_off(kwargs["turn_off_entity"])
        except requests.exceptions.HTTPError as exception:
            self.log("Error trying to turn off entity. Will try again in 1s. Error: {}".format(exception), level = "WARNING")
            self.timer_handle_list.append(self.run_in(self.turn_off_callback,1))

    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)

        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)
      
