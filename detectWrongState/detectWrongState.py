import appdaemon.plugins.hass.hassapi as hass
import globals

#
# App which notifies of wrong states based on a state change
#
# Args:
#
# app_switch: on/off switch for this app. example: input_boolean.turn_fan_on_when_hot
# entities_on (optional): list of entities which should be on
# entities_off (optional): list of entities which should off
# trigger_entity: entity which triggers this app. example: input_boolean.is_home
# trigger_state: new state of trigger_entity which triggers this app. example: "off"
# after_sundown (optional): Only trigger after sundown. example: True
# message_<LANG>: message to use in notification
# message_off_<LANG>: message to use in notification
# message_reed_<LANG>: message to use in notification
# message_reed_off_<LANG>: message to use in notification
# notify_name: who to notify. example: group_notifications
# use_alexa: use alexa for notification. example: False
#
# Release Notes
#
# Version 2.1:
#   More off_states to support alexa_media
#
# Version 2.0:
#   Renamed to detectWrongState, notification optional
#
# Version 1.9:
#   check unavailable when using get_state
#
# Version 1.8:
#   check None when using get_state
#
# Version 1.7:
#   check for != off instead of == on
#
# Version 1.6.1:
#   fix wrong key access for attributes
#
# Version 1.6:
#   garage_door to device_classes of reed sensors
#
# Version 1.5:
#   distinguish normal and reed switches by device_class
#
# Version 1.4.1:
#   fix wrong assignment of app_switch
#
# Version 1.4:
#   Generalize to detectWrongState
#
# Version 1.3:
#   use Notify App
#
# Version 1.2:
#   message now directly in own yaml instead of message module
#
# Version 1.1:
#   Using globals and app_switch
#
# Version 1.0:
#   Initial Version


class DetectWrongState(hass.Hass):
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
        self.trigger_entity = globals.get_arg(self.args, "trigger_entity")
        self.trigger_state = globals.get_arg(self.args, "trigger_state")
        try:
            self.message = globals.get_arg(self.args, "message")
        except KeyError:
            self.message = None
        try:
            self.message_off = globals.get_arg(self.args, "message_off")
        except KeyError:
            self.message_off = None
        try:
            self.message_reed = globals.get_arg(self.args, "message_reed")
        except KeyError:
            self.message_reed = None
        try:
            self.message_reed_off = globals.get_arg(self.args, "message_reed_off")
        except KeyError:
            self.message_reed_off = None
        try:
            self.notify_name = globals.get_arg(self.args, "notify_name")
        except KeyError:
            self.notify_name = None
        try:
            self.use_alexa = globals.get_arg(self.args, "use_alexa")
        except KeyError:
            self.use_alexa = False

        self.notifier = self.get_app("Notifier")

        self.listen_state_handle_list.append(
            self.listen_state(self.state_change, self.trigger_entity)
        )

    def state_change(self, entity, attribute, old, new, kwargs):
        if self.get_state(self.app_switch) == "on":
            if new != "" and new == self.trigger_state:
                if self.after_sundown is None or (
                    (self.after_sundown and self.sun_down())
                    or self.after_sundown is not False
                ):
                    self.check_entities_should_be_off()
                    self.check_entities_should_be_on()

    def check_entities_should_be_off(self):
        off_states = ["off", "unavailable", "paused", "standby"]
        for entity in self.entities_off:
            state = self.get_state(entity)
            self.log(f"entity: {entity}")
            if state is not None and state not in off_states:
                if self.is_entity_reed_contact(entity):
                    message = self.message_reed
                else:
                    self.turn_off(entity)
                    message = self.message
                self.send_notification(message, entity)
    
    def check_entities_should_be_on(self):
        for entity in self.entities_on:
            state = self.get_state(entity)
            if state == "off":
                if self.is_entity_reed_contact(entity):
                    message = self.message_reed_off
                else:
                    self.turn_on(entity)
                    message = self.message_on
                self.send_notification(message, entity)

    def is_entity_reed_contact(self, entity):
        reed_types = ["window", "door", "garage_door"]
        full_state = self.get_state(entity, attribute="all")
        if full_state is not None:
            attributes = full_state["attributes"]
            self.log("full_state: {}".format(full_state), level="DEBUG")
            if attributes.get("device_class") in reed_types:
                self.log(f"device_class: {attributes.get("device_class")}")
                return True
        return False

    def send_notification(self, message, entity):
        if message is not None:
            formatted_message = self.message.format(
                    self.friendly_name(entity)
                )
            self.log(
                formatted_message
            )
            if self.notify_name is not None:
                self.notifier.notify(
                    self.notify_name,
                    formatted_message,
                    useAlexa=self.use_alexa,
                )

    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
