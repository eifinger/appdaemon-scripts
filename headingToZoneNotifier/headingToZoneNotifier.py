import appdaemon.plugins.hass.hassapi as hass
import messages
import secrets
import datetime
#
# App to notify if user_one is leaving a zone
#
# Args:
#   device: Device to track
#   proximity: Proximity Entity which the device is leaving from
#   user_name: Name of the user used in the notification message
#   notify_input_boolean: input_boolean which toggles the notification
#   notify_name: Who to notify
#
# Release Notes
# Version 1.2:
#   Added notify_input_boolean
#
# Version 1.1:
#   Added notify_name
#
# Version 1.0:
#   Initial Version

class HeadingToZoneNotifier(hass.Hass):

    def initialize(self):
        self.user_name = self.args["user_name"]
        if self.user_name.startswith("secret_"):
            self.user_name = self.get_secret(self.user_name)

        self.notify_name = self.get_arg("notify_name")

        self.listen_state_handle_list = []

        self.notify_input_boolean = self.get_arg("notify_input_boolean")

        self.last_triggered = 0
        self.time_between_messages = datetime.timedelta(seconds=600)

        self.listen_state_handle_list.append(self.listen_state(self.state_change, self.args["proximity"], attribute = "all"))
    
    def state_change(self, entity, attributes, old, new, kwargs):
        device = self.args["device"]
        if device.startswith("secret_"):
            device = self.get_secret(device)

        self.log("device: {}".format(device))
        self.log("entity: {}, new: {}, attribute: {}".format(entity,new, attributes))

        if (new["attributes"]["nearest"] == device and 
        old["attributes"]["dir_of_travel"] != "towards" and 
        new["attributes"]["dir_of_travel"] == "towards" and
        int(new["state"]) < 4):
            if self.last_triggered == 0:
                self.last_triggered = self.datetime()
                self.log(messages.user_is_heading_to_zone().format(self.user_name, self.friendly_name(self.args["proximity"])))
                if self.get_state(self.notify_input_boolean) == "on":
                    self.log("Notifying {}".format(self.notify_name)) 
                    self.call_service("notify/" + self.notify_name,message=messages.user_is_heading_to_zone().format(self.user_name, self.friendly_name(self.args["proximity"])))
            if self.last_triggered != 0 and (self.datetime() - self.last_triggered) > self.time_between_messages:
                self.last_triggered = self.datetime()
                self.log(messages.user_is_still_heading_to_zone().format(self.user_name, self.friendly_name(self.args["proximity"])))
                if self.get_state(self.notify_input_boolean) == "on":
                    self.log("Notifying {}".format(self.notify_name)) 
                    self.call_service("notify/" + self.notify_name,message=messages.user_is_still_heading_to_zone().format(self.user_name, self.friendly_name(self.args["proximity"])))

        if new["attributes"]["nearest"] == device and old["attributes"]["dir_of_travel"] == "arrived":
            self.last_triggered = 0


    def get_arg(self, key):
        key = self.args[key]
        if key.startswith("secret_"):
            if key in secrets.secret_dict:
                return secrets.secret_dict[key]
            else:
                self.log("Could not find {} in secret_dict".format(key))
        else:
            return key


    def get_secret(self, key):
        if key in secrets.secret_dict:
            return secrets.secret_dict[key]
        else:
            self.log("Could not find {} in secret_dict".format(key))

    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
      
