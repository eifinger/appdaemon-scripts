import appdaemon.plugins.hass.hassapi as hass
import messages
import secrets
import datetime
import globals
#
# App to notify if user_one is leaving a zone. User had to be in that zone 3 minutes before in order for the notification to be triggered
#
# Args:
#   device: Device to track
#   user_name: Name of the user used in the notification message
#   zone: zone name from which the user is leaving
#   notify_name: Who to notify. example: group_notifications
#
# Release Notes
#
# Version 1.1:
#   Rework without proximity
#
# Version 1.0:
#   Initial Version

class LeavingZoneNotifier(hass.Hass):

    def initialize(self):

        self.user_name = globals.get_arg(self.args,"user_name")
        self.zone = globals.get_arg(self.args,"zone")
        self.notify_name = globals.get_arg(self.args,"notify_name")
        self.device = globals.get_arg(self.args,"device")
        # 'lingering_time' the time a user has to stay in a zone for this app to trigger
        self.lingering_time = 3600
        self.delay = 120

        self.user_entered_zone = None

        self.listen_state_handle_list = []
        self.timer_handle_list = []
        self.time_between_messages = datetime.timedelta(seconds=600)

        self.listen_state_handle_list.append(self.listen_state(self.zone_state_change, self.device, attribute = "all"))

    def zone_state_change(self, entity, attributes, old, new, kwargs):
        last_changed = self.convert_utc(new["attributes"]["last_changed"])
        if new == self.zone:
            self.log("Setting user_entered_zone to {}".format(last_changed))
            self.user_entered_zone = last_changed
        if old == self.zone:
            if self.user_entered_zone == None or (self.convert_utc(last_changed) - self.user_entered_zone >= datetime.timedelta(seconds=self.lingering_time)):
                self.log("Zone of {} changed from {} to {}. Wait {} seconds until notification.".format(self.friendly_name(entity),old,new,self.delay))
                self.timer_handle_list.append(self.run_in(self.notify_user, self.delay, old_zone = old))

        

    def notify_user(self, kwargs):
        #Check if user did not come back to the zone in the meantime
        if self.get_state(self.device) != kwargs["old_zone"]:
            self.call_service("notify/" + self.notify_name, message=messages.user_is_leaving_zone().format(self.user_name, self.zone)) 


    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)

        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)
      
