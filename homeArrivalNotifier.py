import appdaemon.plugins.hass.hassapi as hass
import messages
import secrets
#
# App to send a notification if someone arrives at home
#
# Args:
#  input_boolean: input boolean which holds the information of someone is home or not
#  notify_name: Who to notify
#  zone_name: Name of the zone
# Release Notes
#
# Version 1.0:
#   Initial Version

class HomeArrivalNotifier(hass.Hass):

    def initialize(self):
        self.listen_state_handle_list = []

        self.zone_name = self.get_arg("zone_name")
        self.input_boolean = self.get_arg("input_boolean")
        self.notify_name = self.get_arg("notify_name")
        
        self.listen_state_handle_list.append(self.listen_state(self.state_change, self.input_boolean))
    
    def state_change(self, entity, attribute, old, new, kwargs):
        if new != "" and new != old:
            self.log("{} changed from {} to {}".format(entity,old,new))
            if new == "on":
                self.log("{} arrived at {}".format(self.notify_name,self.zone_name))
                self.call_service("notify/" + self.notify_name, message=messages.welcome_home().format(self.notify_name))            
                    
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
      
