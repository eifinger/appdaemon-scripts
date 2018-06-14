import appdaemon.plugins.hass.hassapi as hass
import messages
import secrets
#
# App to send notification when a sensor changes state
#
# Args:
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class DummyTelegramTrigger(hass.Hass):

    def initialize(self):
        self.listen_state_handle_list = []

        self.listen_state_handle_list.append(self.listen_state(self.state_change, "input_boolean.user_one_home"))
    
    def state_change(self, entity, attribute, old, new, kwargs):
        name = self.get_secret("secret_name_user_one")
        self.log("{} changed to {}".format(self.friendly_name(entity), new))
        self.call_service("notify/"+name,message=messages.device_change_alert().format(self.friendly_name(entity), new))

    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)

    def get_secret(self, key):
        if key in secrets.secret_dict:
            return secrets.secret_dict[key]
        else:
            self.log("Could not find {} in secret_dict".format(key))
      
