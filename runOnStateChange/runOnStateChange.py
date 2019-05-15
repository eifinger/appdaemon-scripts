import appdaemon.plugins.hass.hassapi as hass
import globals

#
# App which runs something based on a state change
#
# Args:
#
# app_switch: on/off switch for this app. example: input_boolean.turn_fan_on_when_hot
# entities_on (optional): list of entities which should be turned on
# entities_off (optional): list of entities which should be turned off
# trigger_entity: entity which triggers this app. example: input_boolean.is_home
# trigger_state: new state of trigger_entity which triggers this app. example: "off"
# after_sundown (optional): Only trigger after sundown. example: True
# message_on: message to use in notification
# message_off: message to use in notification
# notify_name: who to notify. example: group_notifications
# use_alexa: use alexa for notification. example: False
#
# Release Notes
#
# Version 1.2:
#   only run on actual state change
#
# Version 1.1:
#   fix switch of On/Off
#
# Version 1.0:
#   Initial Version


class RunOnStateChange(hass.Hass):
    def initialize(self):
        self.listen_state_handle_list = []

        self.app_switch = globals.get_arg(self.args, "app_switch")
        try:
            self.entities_on = globals.get_arg_list(self.args, "entities_on")
        except KeyError:
            self.entities_on = []
        try:
            self.entities_off = globals.get_arg_list(self.args, "entities_off")
        except KeyError:
            self.entities_off = []
        try:
            self.after_sundown = globals.get_arg(self.args, "after_sundown")
        except KeyError:
            self.after_sundown = None
        try:
            self.notify_name = globals.get_arg(self.args, "notify_name")
        except KeyError:
            self.notify_name = None
        try:
            self.message_on = globals.get_arg(self.args, "message_on")
        except KeyError:
            self.message_on = None
        try:
            self.message_off = globals.get_arg(self.args, "message_off")
        except KeyError:
            self.message_off = None
        try:
            self.use_alexa = globals.get_arg(self.args, "use_alexa")
        except KeyError:
            self.use_alexa = None
        self.trigger_entity = globals.get_arg(self.args, "trigger_entity")
        self.trigger_state = globals.get_arg(self.args, "trigger_state")

        self.notifier = self.get_app("Notifier")

        self.listen_state_handle_list.append(
            self.listen_state(self.state_change, self.trigger_entity)
        )

    def state_change(self, entity, attribute, old, new, kwargs):
        if self.get_state(self.app_switch) == "on":
            if new != "" and new == self.trigger_state and old != new:
                if self.after_sundown == None or (
                    (self.after_sundown == True and self.sun_down())
                    or self.after_sundown == False
                ):
                    # turn_off
                    for entity in self.entities_on:
                        self.turn_on(entity)
                        self.log("Turning on {}".format(entity))
                        if self.notify_name is not None and self.message_on is not None:
                            self.log(self.message_on.format(self.friendly_name(entity)))
                            self.notifier.notify(
                                self.notify_name,
                                self.message_on.format(self.friendly_name(entity)),
                                useAlexa=self.use_alexa,
                            )
                    # turn_on
                    for entity in self.entities_off:
                        self.turn_off(entity)
                        self.log("Turning off {}".format(entity))
                        if (
                            self.notify_name is not None
                            and self.message_off is not None
                        ):
                            self.log(
                                self.message_off.format(self.friendly_name(entity))
                            )
                            self.notifier.notify(
                                self.notify_name,
                                self.message_off.format(self.friendly_name(entity)),
                                useAlexa=self.use_alexa,
                            )

    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
