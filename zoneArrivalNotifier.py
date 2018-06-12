import appdaemon.plugins.hass.hassapi as hass
import messages
import secrets
#
# App to send a notification if someone arrives at a zone
#
# Args:
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class ZoneArrivalNotifier(hass.Hass):

    def initialize(self):
        self.listen_state_handle_list = []
        
        self.listen_state_handle_list.append(self.listen_state(self.state_change, self.get_secret("secret_device_user_one")))
        self.listen_state_handle_list.append(self.listen_state(self.state_change, self.get_secret("secret_device_user_two")))
    
    def state_change(self, entity, attribute, old, new, kwargs):
        if new != "" and new != old:
            self.log("{} changed from {} to {}".format(entity,old,new))
            if new == "Wohnung":
                self.log("{} came to flat".format(entity))
                if entity == self.get_secret("secret_device_user_one"):
                    self.call_service("notify/slack", message=messages.welcome_in_new_flat().format(self.get_secret("secret_name_user_one")))
                if entity == self.get_secret("secret_device_user_two"):
                    self.call_service("notify/slack", message=messages.welcome_in_new_flat().format(self.get_secret("secret_name_user_two")))            

    def get_secret(self, key):
        if key in secrets.secret_dict:
            return secrets.secret_dict[key]
        else:
            self.log("Could not find {} in secret_dict".format(key))

    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
      
