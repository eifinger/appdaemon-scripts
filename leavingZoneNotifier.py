import appdaemon.plugins.hass.hassapi as hass
import messages
import datetime
import globals
#
# App to notify if user_one is leaving a zone. User had to be in that zone 3 minutes before in order for the notification to be triggered
#
# Args:
#   app_switch: on/off switch for this app. example: input_boolean.turn_fan_on_when_hot
#   device: Device to track
#   user_name: Name of the user used in the notification message
#   delay: time to wait before notifying. Maybe user returns to zone. example: 120
#   lingering_time: time a user has to be in a zone to trigger this app. example: 3600
#   zone: zone name from which the user is leaving
#   notify_name: Who to notify. example: group_notifications
#
# Release Notes
#
# Version 1.3:
#   delay and lingering_time now as args
#
# Version 1.2:
#   Added app_switch
#
# Version 1.1:
#   Rework without proximity
#
# Version 1.0:
#   Initial Version

class LeavingZoneNotifier(hass.Hass):

    def initialize(self):

        self.app_switch = globals.get_arg(self.args,"app_switch")
        self.user_name = globals.get_arg(self.args,"user_name")
        self.zone = globals.get_arg(self.args,"zone")
        self.notify_name = globals.get_arg(self.args,"notify_name")
        self.device = globals.get_arg(self.args,"device")
        # 'lingering_time' the time a user has to stay in a zone for this app to trigger
        self.lingering_time = globals.get_arg(self.args,"lingering_time")
        self.delay = globals.get_arg(self.args,"delay")

        self.user_entered_zone = None

        self.listen_state_handle_list = []
        self.timer_handle_list = []

        self.listen_state_handle_list.append(self.listen_state(self.zone_state_change, self.device, attribute = "all"))

    def zone_state_change(self, entity, attributes, old, new, kwargs):
        if self.get_state(self.app_switch) == "on":
            last_changed = self.convert_utc(new["last_changed"])
            self.log("Zone of {} changed from {} to {}.".format(self.friendly_name(entity),old["state"],new["state"]), level="DEBUG")
            if new["state"] == self.zone:
                self.log("Setting user_entered_zone to {}".format(last_changed), level = "DEBUG")
                self.user_entered_zone = last_changed
            if old["state"] == self.zone:
                if self.user_entered_zone == None or (last_changed - self.user_entered_zone >= datetime.timedelta(seconds=self.lingering_time)):
                    self.log("Zone of {} changed from {} to {}. Wait {} seconds until notification.".format(self.friendly_name(entity),old,new,self.delay))
                    self.timer_handle_list.append(self.run_in(self.notify_user, self.delay, old_zone = old))

        

    def notify_user(self, kwargs):
        #Check if user did not come back to the zone in the meantime
        if self.get_state(self.device) != kwargs["old_zone"]:
            self.log("Notify user")
            self.call_service("notify/" + self.notify_name, message=messages.user_is_leaving_zone().format(self.user_name, self.zone)) 


    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)

        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)
      
