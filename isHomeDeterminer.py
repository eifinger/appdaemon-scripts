import appdaemon.plugins.hass.hassapi as hass
import messages
import secrets
#
# App to 
#
# Args:
# input_booleans: list of input boolean which determine if a user is home
# is_home: input boolean which determins if someone is home
# Release Notes
#
# Version 1.0:
#   Initial Version

class IsHomeDeterminer(hass.Hass):

    def initialize(self):
        self.listen_state_handle_list = []

        self.is_home = self.get_arg("is_home")
        
        for input_boolean in self.args["input_booleans"]:
            self.listen_state_handle_list.append(self.listen_state(self.state_change, self.get_arg(input_boolean)))
    
    def state_change(self, entity, attribute, old, new, kwargs):
        if new != "" and new != old:
            self.log("{} changed from {} to {}".format(entity,old,new))
            if new == "on":
                if self.are_others_away:
                    self.turn_on(self.is_home)
                    self.log("Setting {} to on".format(self.is_home))
            if new == "off":
                if self.are_others_away:
                    self.turn_off(self.is_home)
                    self.log("Setting {} to off".format(self.is_home))
                    self.call_service("notify/group_notifications",message=messages.isHome_off())

    def are_others_away():
        for input_boolean in self.args["input_booleans"]:
            if self.get_state(self.get_arg(input_boolean)) == "on":
                return False
        return True

    def get_arg(self, key):
        key = self.args[key]
        if key.startswith("secret_"):
            if key in secrets.secret_dict:
                return secrets.secret_dict[key]
            else:
                self.log("Could not find {} in secret_dict".format(key))
        else:
            return key

    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
      
