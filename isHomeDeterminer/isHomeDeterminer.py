import appdaemon.plugins.hass.hassapi as hass
import messages
import globals

#
# App to
#
# Args:
#   app_switch: on/off switch for this app. example: input_boolean.turn_fan_on_when_hot
#   input_booleans: list of input boolean which determine if a user is home
#   ishome: input boolean which determins if someone is home
#   message: message to use in notification
# Release Notes
#
# Version 1.3:
#   message now a list
#
# Version 1.2:
#   message now directly in own yaml instead of message module
#
# Version 1.1:
#   Added app_switch
#
# Version 1.0:
#   Initial Version


class IsHomeDeterminer(hass.Hass):
    def initialize(self):
        self.listen_state_handle_list = []

        self.app_switch = globals.get_arg(self.args, "app_switch")
        self.ishome = globals.get_arg(self.args, "ishome")
        self.input_booleans = globals.get_arg_list(self.args, "input_booleans")
        self.message = globals.get_arg_list(self.args, "message")

        if self.get_state(self.app_switch) == "on":
            for input_boolean in self.input_booleans:
                self.log(
                    "{} is {}".format(input_boolean, self.get_state(input_boolean))
                )
                self.listen_state_handle_list.append(
                    self.listen_state(self.state_change, input_boolean)
                )
                if (
                    self.get_state(input_boolean) == "on"
                    and self.get_state(self.ishome) == "off"
                ):
                    self.turn_on(self.ishome)
                    self.log("Setting {} to on".format(self.ishome))
                if (
                    self.get_state(input_boolean) == "off"
                    and self.get_state(self.ishome) == "on"
                ):
                    if self.are_others_away(input_boolean):
                        self.turn_off(self.ishome)
                        self.log("Setting {} to off".format(self.ishome))
                        notify_message = globals.random_arg(self.message)
                        self.log("notify_messsage: {}".format(notify_message))
                        self.call_service(
                            "notify/group_notifications", message=notify_message
                        )

    def state_change(self, entity, attribute, old, new, kwargs):
        if self.get_state(self.app_switch) == "on":
            if new != "" and new != old:
                self.log("{} changed from {} to {}".format(entity, old, new))
                if new == "on":
                    self.turn_on(self.ishome)
                    self.log("Setting {} to on".format(self.ishome))
                if new == "off":
                    if self.are_others_away(entity):
                        self.turn_off(self.ishome)
                        self.log("Setting {} to off".format(self.ishome))
                        notify_message = globals.random_arg(self.message)
                        self.log("notify_messsage: {}".format(notify_message))
                        self.call_service(
                            "notify/group_notifications", message=notify_message
                        )

    def are_others_away(self, entity):
        self.log("Entity: {}".format(entity))
        for input_boolean in self.input_booleans:
            self.log("{} is {}".format(input_boolean, self.get_state(input_boolean)))
            if input_boolean == entity:
                pass
            elif self.get_state(input_boolean) == "on":
                self.log("{} is still at on".format(input_boolean))
                return False
        self.log("Everybody not home")
        return True

    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
