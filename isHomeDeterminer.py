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
        oneplus3 = self.get_state(self.get_secret("secret_device_user_one"))
        oneplus3T = self.get_state(self.get_secret("secret_device_user_two"))
        self.isHomeHandler(oneplus3T, oneplus3)
        
        self.listen_state(self.state_change, self.get_secret("secret_device_user_one"))
        self.listen_state(self.state_change, self.get_secret("secret_device_user_two"))
    
    def state_change(self, entity, attribute, old, new, kwargs):
        if new != "":
            if entity == self.get_secret("secret_device_user_two"):
                oneplus3 = self.get_state(self.get_secret("secret_device_user_one"))
                oneplus3T = new
            if entity == self.get_secret("secret_device_user_one"):
                oneplus3T = self.get_state(self.get_secret("secret_device_user_two"))
                oneplus3 = new
            self.isHomeHandler(oneplus3T, oneplus3)

    def isHomeHandler(self, oneplus3T, oneplus3):
        if oneplus3 == "home" or oneplus3T == "home":
            self.log("Setting {} to on".format(self.args["isHome"]))
            self.set_state(self.args["isHome"], state = "on")
        if oneplus3 == "not_home" and oneplus3T == "not_home":
            self.log("Setting {} to off".format(self.args["isHome"]))
            self.set_state(self.args["isHome"], state = "off")
            self.call_service("notify/slack",message=messages.isHome_off())

    def get_secret(self, key):
        if key in secrets.secret_dict:
            return secrets.secret_dict[key]
        else:
            self.log("Could not find {} in secret_dict".format(key))
      
