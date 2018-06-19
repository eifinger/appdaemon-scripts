import appdaemon.plugins.hass.hassapi as hass
import messages
import secrets
#
# App to Turn on Lobby Lamp when Door openes and OnePlus is not Home
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

class IsHomeDeterminer(hass.Hass):

    def initialize(self):
        self.listen_state_handle_list = []

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
            device_tracker_state = self.get_state(self.device_tracker)
            self.log(device_tracker_state)
            last_changed = device_tracker_state["last_changed"]
            if device_tracker_state == "home" and (self.datetime() - last_changed ) < 120:
                self.turn_on(self.input_boolean)

    def get_secret(self, key):
        if key in secrets.secret_dict:
            return secrets.secret_dict[key]
        else:
            self.log("Could not find {} in secret_dict".format(key))

    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
      
