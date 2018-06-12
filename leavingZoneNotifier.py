import appdaemon.plugins.hass.hassapi as hass
import messages
import secrets
import datetime
#
# App to notify if user_one is leaving a zone. User had to be in that zone 3 minutes before in order for the notification to be triggered
#
# Args:
#   device: Device to track
#   proximity: Proximity Entity which the device is leaving from
#   user_name: Name of the user used in the notification message
#   zone: zone name from which the user is leaving
#   zone_tracker_delay: delay between device_zone changes
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class LeavingZoneNotifier(hass.Hass):

    def initialize(self):
        self.user_name = self.args["user_name"]
        if self.user_name.startswith("secret_"):
            self.user_name = self.get_secret(self.user_name)

        self.device_zone = self.get_state(self.args["device"])
        if "zone_tracker_delay" in self.args:
            self.delay = self.args["zone_tracker_delay"]
        else:
            self.delay = 180

        self.listen_state_handle_list = []
        self.timer_handle = None

        self.last_triggered = 0
        self.time_between_messages = datetime.timedelta(seconds=600)

        self.listen_state_handle_list.append(self.listen_state(self.state_change, self.args["proximity"], attribute = "all"))
        self.listen_state_handle_list.append(self.listen_state(self.zone_state_change, self.args["device"], attribute = "all"))
    
    def state_change(self, entity, attribute, old, new, kwargs):
        device = self.args["device"]
        if device.startswith("secret_"):
            device = self.get_secret(device)

        self.log("device: {}".format(device))
        self.log("device_zone: {}".format(self.device_zone))
        self.log("entity: {}, new: {}".format(entity,new))

        if (new["attributes"]["nearest"] == device and 
        old["attributes"]["dir_of_travel"] != "away_from" and 
        new["attributes"]["dir_of_travel"] == "away_from" and
        self.device_zone == self.args["zone"] and
        (self.datetime() - self.last_triggered) > self.time_between_messages):
            self.log(messages.user_is_leaving_zone().format(self.user_name, self.friendly_name(self.args["proximity"])))
            self.call_service("notify/slack",message=messages.user_is_leaving_zone().format(self.user_name, self.friendly_name(self.args["proximity"])))
            
        self.last_triggered = self.datetime()


    def zone_state_change(self, entity, attributes, old, new, kwargs):
        self.log("Zone change detected, will run set_device_zone in {} seconds".format(self.delay))
        self.timer_handle = self.run_in(self.set_device_zone, self.delay, device_zone=new)

    def set_device_zone(self, device_zone):
        self.log("Setting device_zone to: {}".format(device_zone))
        self.device_zone = device_zone

    def get_secret(self, key):
        if key in secrets.secret_dict:
            return secrets.secret_dict[key]
        else:
            self.log("Could not find {} in secret_dict".format(key))

    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)

        self.cancel_timer(self.timer_handle)
      
