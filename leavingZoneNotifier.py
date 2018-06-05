import appdaemon.plugins.hass.hassapi as hass
import messages
import secrets
#
# App to notify if user_one is leaving a zone
#
# Args:
#   device: Device to track
#   proximity: Proximity Entity which the device is leaving from
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class LeavingZoneNotifier(hass.Hass):

    def initialize(self):
        self.listen_state_handle_list = []

        self.listen_state_handle_list.append(self.listen_state(self.state_change, self.args["proximity"]))
    
    def state_change(self, entity, attribute, old, new, kwargs):
        device = self.args["device"]
        if device.startswith("secret_"):
            device = self.get_secret(device)

        self.log("device: {}".format(device))
        self.log("entity: {}, new: {}, attribute: {}".format(entity,new, attribute))

        if attribute["nearest"] == device and attribute["dir_of_travel"] == "away_from":
            if self.args["device"] == "secret_device_user_one":
                user = self.get_secret("secret_name_user_one")
            self.log(messages.user_is_leaving_zone().format(user, self.friendly_name(self.args["proximity"])))
            self.call_service("notify/slack",message=messages.user_is_leaving_zone().format(user, self.friendly_name(self.args["proximity"])))



    def get_secret(self, key):
        if key in secrets.secret_dict:
            return secrets.secret_dict[key]
        else:
            self.log("Could not find {} in secret_dict".format(key))

    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
      
