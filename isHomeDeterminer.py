import appdaemon.plugins.hass.hassapi as hass
import messages
import secrets
#
# App to Turn on Lobby Lamp when Door openes and OnePlus is not Home
#
# Args:
#
# isHome: input_boolean which shows if someone is home eg input_boolean.isHome
# Release Notes
#
# Version 1.0:
#   Initial Version

class IsHomeDeterminer(hass.Hass):

    def initialize(self):
        self.listen_state_handle_list = []

        device_user_one = self.get_state(self.get_secret("secret_device_user_one"))
        device_user_two = self.get_state(self.get_secret("secret_device_user_two"))
        self.isHomeHandler(device_user_two, device_user_one)
        
        self.listen_state_handle_list.append(self.listen_state(self.state_change, self.get_secret("secret_device_user_one")))
        self.listen_state_handle_list.append(self.listen_state(self.state_change, self.get_secret("secret_device_user_two")))
    
    def state_change(self, entity, attribute, old, new, kwargs):
        if new != "":
            if entity == self.get_secret("secret_device_user_two"):
                device_user_one = self.get_state(self.get_secret("secret_device_user_one"))
                self.isHomeHandler(new, device_user_one)
                self.call_service("notify/slack", message=messages.welcome_home().format(self.get_secret("secret_name_user_one")))
            if entity == self.get_secret("secret_device_user_one"):
                device_user_two = self.get_state(self.get_secret("secret_device_user_two"))
                self.isHomeHandler(new, device_user_two)
                self.call_service("notify/slack", message=messages.welcome_home().format(self.get_secret("secret_name_user_two")))
            

    def isHomeHandler(self, new, other):
        if new == "home" or other == "home":
            self.log("Setting {} to on".format(self.args["isHome"]))
            self.set_state(self.args["isHome"], state = "on")
        if new == "not_home" and other == "not_home":
            self.log("Setting {} to off".format(self.args["isHome"]))
            self.set_state(self.args["isHome"], state = "off")
            self.call_service("notify/slack",message=messages.isHome_off())

    def get_secret(self, key):
        if key in secrets.secret_dict:
            return secrets.secret_dict[key]
        else:
            self.log("Could not find {} in secret_dict".format(key))

    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
        self.cancel_listen_state(listen_state_handle)
      
