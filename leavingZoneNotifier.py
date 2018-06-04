import appdaemon.plugins.hass.hassapi as hass
import messages
import secrets
#
# App to notify if user_one is leaving a zone
#
# Args:
#   device: Device to track
#   proximity: Proximity Entitiy which the device is leaving from
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class LeavingZoneNotifier(hass.Hass):

    def initialize(self):
        self.listen_state_handle_list = []

        self.listen_state_handle_list.append(self.listen_state(self.state_change, "proximity.sindlingen"))
    
    def state_change(self, entity, attribute, old, new, kwargs):
        self.log("entity: {}, new: {}, attribute: {}".format(entity,new, attribute))

    def get_secret(self, key):
        if key in secrets.secret_dict:
            return secrets.secret_dict[key]
        else:
            self.log("Could not find {} in secret_dict".format(key))

    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
      
