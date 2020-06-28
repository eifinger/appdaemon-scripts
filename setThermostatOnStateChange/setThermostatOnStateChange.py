import appdaemon.plugins.hass.hassapi as hass

#
# App which sets a thermostat to a target temperature on state change
#
# Args:
#
# app_switch: on/off switch for this app. example: input_boolean.warm_bath_before_wakeup
# trigger_entity: entity which triggers this app. example: input_boolean.is_home
# trigger_state: new state of trigger_entity which triggers this app. example: "off"
# climate_entity: climate entity to set. example: climate.bad_thermostat
# target_entity: the entity holding the target temp. example: warm_bath_before_wakeup
# message (optional): message to use in notification
# notify_name (optional): who to notify. example: group_notifications
# use_alexa (optional): use alexa for notification. example: False
#
# Release Notes
#
# Version 1.2:
#   Rename of SetThermostatOnStateChange
#
# Version 1.1:
#   Use isHome as trigger
#
# Version 1.0:
#   Initial Version


class SetThermostatOnStateChange(hass.Hass):
    def initialize(self):
        self.timer_handle_list = []
        self.listen_state_handle_list = []

        self.app_switch = self.args["app_switch"]
        self.trigger_entity = self.args["trigger_entity"]
        self.trigger_state = self.args["trigger_state"]
        self.climate_entity = self.args["climate_entity"]
        self.target_entity = self.args["target_entity"]
        self.message = self.args.get("message")
        self.notify_name = self.args.get("notify_name")
        try:
            self.use_alexa = self.args["use_alexa"]
        except KeyError:
            self.use_alexa = False

        self.notifier = self.get_app("Notifier")

        self.listen_state_handle_list.append(
            self.listen_state(self.state_change, self.trigger_entity)
        )

    def state_change(self, entity, attribute, old, new, kwargs):
        if self.get_state(self.app_switch) == "on":
            if new != "" and new == self.trigger_state and old != new:
                if self.message is not None:
                    self.log(
                        self.message.format(
                            self.friendly_name(self.climate_entity),
                            self.get_state(self.target_entity),
                        )
                    )
                self.call_service("climate/turn_on", entity_id=self.climate_entity)
                self.call_service(
                    "climate/set_temperature",
                    entity_id=self.climate_entity,
                    temperature=self.get_state(self.target_entity),
                )
                if self.notify_name is not None:
                    self.notifier.notify(
                        self.notify_name,
                        self.message.format(
                            self.friendly_name(self.climate_entity),
                            self.get_state(self.target_entity),
                        ),
                        useAlexa=self.use_alexa,
                    )

    def terminate(self):
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)

        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
