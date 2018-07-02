import appdaemon.plugins.hass.hassapi as hass
import messages
import secrets
#
# App to toggle an input boolean when a person enters or leaves home.
# This is determined based on a combination of a GPS device tracker and the door sensor.
#
# - If the door sensor openes and the device_tracker changed to "home" in the last 2 minutes this means someone got home
# - If the door sensor openes and the device_tracker changes to "not_home" in the next to minutes this means someone left home
#
# Args:
#
# input_boolean: input_boolean which shows if someone is home e.g. input_boolean.isHome
# device_tracker: device tracker of the user to track e.g. device_tracker.simon
# door_sensor: Door sensor which indicated the frontdoor opened e.g. binary_sensor.door_window_sensor_158d000126a57b
# Release Notes
#
# Version 1.0:
#   Initial Version

class IsUserHomeDeterminer(hass.Hass):

    def initialize(self):
        self.listen_state_handle_list = []

        self.delay = 120

        self.input_boolean = self.args["input_boolean"]
        if self.input_boolean.startswith("secret_"):
            self.input_boolean = self.get_secret(self.input_boolean)
        self.device_tracker = self.args["device_tracker"]
        if self.device_tracker.startswith("secret_"):
            self.device_tracker = self.get_secret(self.device_tracker)
        self.door_sensor = self.args["door_sensor"]
        if self.door_sensor.startswith("secret_"):
            self.door_sensor = self.get_secret(self.door_sensor)
        
        self.listen_state_handle_list.append(self.listen_state(self.state_change, self.door_sensor))
    
    def state_change(self, entity, attribute, old, new, kwargs):
        if new != "" and new != old:
            self.log("{} changed from {} to {}".format(entity,old,new))
            device_tracker_state = self.get_state(self.device_tracker, attribute = "all")
            self.log("device_tracker_state: {}".format(device_tracker_state))
            last_changed = device_tracker_state["attributes"]["last_changed"]
            #User got home: Device tracker changed to home before door sensor triggered
            if device_tracker_state == "home" and (self.datetime() - last_changed ) < self.delay:
                self.turn_on(self.input_boolean)
            #User got home: Device tracker is still not home. Wait if it changes to home in the next self.delay seconds
            elif device_tracker_state != "home":
                self.run_in(self.check_if_user_got_home,self.delay)
            #User left home: Device tracker is still home.  Wait if it changes to home in the next self.delay seconds
            elif device_tracker_state == "home":
                self.run_in(self.check_if_user_left_home,self.delay)

    def check_if_user_left_home(self):
        device_tracker_state = self.get_state(self.device_tracker)
        self.log("device_tracker_state: {}".format(device_tracker_state))
        if device_tracker_state != "home":
            self.turn_off(self.input_boolean)

    def check_if_user_got_home(self):
        device_tracker_state = self.get_state(self.device_tracker)
        self.log("device_tracker_state: {}".format(device_tracker_state))
        if device_tracker_state == "home":
            self.turn_on(self.input_boolean)

    def get_secret(self, key):
        if key in secrets.secret_dict:
            return secrets.secret_dict[key]
        else:
            self.log("Could not find {} in secret_dict".format(key))

    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
      
