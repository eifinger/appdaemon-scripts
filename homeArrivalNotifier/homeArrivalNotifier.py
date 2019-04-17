import appdaemon.plugins.hass.hassapi as hass
import globals
#
# App to send a notification if someone arrives at home
#
# Args:
#  app_switch: on/off switch for this app. example: input_boolean.turn_fan_on_when_hot
#  input_boolean: input boolean which holds the information of someone is home or not
#  notify_name: Who to notify
#  user_name: name to use in notification message
#  zone_name: Name of the zone
#  message: message to use in notification
# Release Notes
#
# Version 1.4.1:
#   Use consistent message variable
#
# Version 1.4:
#   use Notify App
#
# Version 1.3:
#   message now directly in own yaml instead of message module
#
# Version 1.2:
#   Added app_switch
#
# Version 1.1:
#   Added user_name
#
# Version 1.0:
#   Initial Version

class HomeArrivalNotifier(hass.Hass):

    def initialize(self):
        self.listen_state_handle_list = []

        self.app_switch = globals.get_arg(self.args, "app_switch")
        self.zone_name = globals.get_arg(self.args, "zone_name")
        self.input_boolean = globals.get_arg(self.args, "input_boolean")
        self.notify_name = globals.get_arg(self.args, "notify_name")
        self.user_name = globals.get_arg(self.args, "user_name")
        self.message = globals.get_arg(self.args, "message")

        self.notifier = self.get_app('Notifier')
        
        self.listen_state_handle_list.append(self.listen_state(self.state_change, self.input_boolean))
    
    def state_change(self, entity, attribute, old, new, kwargs):
        if self.get_state(self.app_switch) == "on":
            if new != "" and new != old:
                self.log("{} changed from {} to {}".format(entity, old, new))
                if new == "on":
                    self.log("{} arrived at {}".format(self.notify_name, self.zone_name))
                    self.notifier.notify(self.notify_name, self.message.format(self.user_name))          

    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)

