import appdaemon.plugins.hass.hassapi as hass
import globals
#
# App which sets the sleep mode on/off
#
# Args:
#   app_switch: on/off switch for this app. example: input_boolean.turn_fan_on_when_hot
#   input_boolean: input_boolean holding the sleepmode. example: input_boolean.sleepmode
#
# Release Notes
#
# Version 1.0:
#   Initial Version


class SleepModeHandler(hass.Hass):

    def initialize(self):
        self.listen_state_handle_list = []

        self.app_switch = globals.get_arg(self.args, "app_switch")
        self.sleepmode = globals.get_arg(self.args, "sleepmode")
        self.users = globals.get_arg(self.args, "users")


        for user,user_config in self.users:
            self.listen_state_handle_list.append(
                self.listen_state(self.state_change, user_config.sleep_mode), user_config=user_config)
    
    def state_change(self, entity, attribute, old, new, kwargs):
        if self.get_state(self.app_switch) == "on":
            if new != "" and new != old:
                if new != "off":
                    # is home
                    user_config = kwargs["user_config"]
                    self.log(user_config)
                    # are others home and sleeping

    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)

