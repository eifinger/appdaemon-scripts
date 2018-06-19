import appdaemon.plugins.hass.hassapi as hass
import messages
import secrets
#
# App to 
#
# Args:
#
# isHome: input_boolean which shows if someone is home e.g. input_boolean.isHome
# door_sensor: Door sensor which indicated the frontdoor opened e.g. binary_sensor.door_window_sensor_158d000126a57b
# user_name: who to notify
# Release Notes
#
# Version 1.0:
#   Initial Version

class IsHomeDeterminer(hass.Hass):

    def initialize(self):
        self.listen_state_handle_list = []

        device_user_one_state = self.get_state(self.get_secret("secret_device_user_one"))
        device_user_two_state = self.get_state(self.get_secret("secret_device_user_two"))
        self.isHomeHandler(device_user_two_state, device_user_two_state, device_user_one_state)
        
        self.listen_state_handle_list.append(self.listen_state(self.state_change, self.get_secret("secret_device_user_one")))
        self.listen_state_handle_list.append(self.listen_state(self.state_change, self.get_secret("secret_device_user_two")))
    
    def state_change(self, entity, attribute, old, new, kwargs):
        if new != "" and new != old:
            self.log("{} changed from {} to {}".format(entity,old,new))
            if new == "home":
                self.log("{} came Home".format(entity))
                if entity == self.get_secret("secret_device_user_one"):
                    device_user_two_state = self.get_state(self.get_secret("secret_device_user_two"))
                    self.isHomeHandler(new, old, device_user_two_state)
                    self.call_service("notify/group_notifications", message=messages.welcome_home().format(self.get_secret("secret_name_user_one")))
                if entity == self.get_secret("secret_device_user_two"):
                    device_user_one_state = self.get_state(self.get_secret("secret_device_user_one"))
                    self.isHomeHandler(new, old, device_user_one_state)
                    self.call_service("notify/group_notifications", message=messages.welcome_home().format(self.get_secret("secret_name_user_two")))
            else:
                if entity == self.get_secret("secret_device_user_one"):
                    device_user_two_state = self.get_state(self.get_secret("secret_device_user_two"))
                    self.isHomeHandler(new, old, device_user_two_state)
                if entity == self.get_secret("secret_device_user_two"):
                    device_user_one_state = self.get_state(self.get_secret("secret_device_user_one"))
                    self.isHomeHandler(new, old, device_user_one_state)
            

    def isHomeHandler(self, new, old, other):
        if new == "home" or other == "home":
            self.log("Setting {} to on".format(self.args["isHome"]))
            self.set_state(self.args["isHome"], state = "on")
        if new == "not_home" and other == "not_home" and old == "home":
            self.log("Setting {} to off".format(self.args["isHome"]))
            self.set_state(self.args["isHome"], state = "off")
            if new != old:
                self.call_service("notify/group_notifications",message=messages.isHome_off())

    def get_secret(self, key):
        if key in secrets.secret_dict:
            return secrets.secret_dict[key]
        else:
            self.log("Could not find {} in secret_dict".format(key))

    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
      
