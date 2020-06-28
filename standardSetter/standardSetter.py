import appdaemon.plugins.hass.hassapi as hass

#
# App which resets entities back to a standard value
#
#
# Args:
#  entity: entity to set back to standard. example: input_select.next_appointment_travel_mode
#  standard_entity: entity which holds the standard value. example: input_select.next_appointment_travel_mode_standard
#  trigger_event (optional): Event which triggers this app. example: click
#  trigger_state (optional): State which triggers this app. example: on
#  trigger_entity: Entity which triggers this app. If no state or event is set all state changes trigger this app. example: sensor.cal_next_appointment_title
#
#
# Release Notes
#
# Version 1.0:
#   Initial Version


class StandardSetter(hass.Hass):
    def initialize(self):

        self.timer_handle_list = []
        self.listen_event_handle_list = []
        self.listen_state_handle_list = []

        self.entity = self.args["entity"]
        self.standard_entity = self.args["standard_entity"]
        self.trigger_event = self.args.get("trigger_event")
        self.trigger_state = self.args.get("trigger_state")

        self.trigger_entity = self.args["trigger_entity"]

        if self.trigger_event != None:
            self.listen_event_handle_list.append(
                self.listen_event(self.event_callback, self.trigger_event)
            )
        self.listen_state_handle_list.append(
            self.listen_state(self.state_change, self.trigger_entity)
        )

    def state_change(self, entity, attributes, old, new, kwargs):
        if new != None:
            if self.trigger_state == None or (
                self.trigger_state != None and new == self.trigger_state
            ):
                if self.entity.startswith("input_select."):
                    self.log(
                        "Setting {} to {}.".format(
                            self.entity, self.get_state(self.standard_entity)
                        )
                    )
                    self.select_option(
                        self.entity, self.get_state(self.standard_entity)
                    )
                elif self.entity.startswith("input_number."):
                    self.set_value(self.entity, self.get_state(self.standard_entity))
                else:
                    self.log(
                        "Unsupported entity type {}. Supported are: 'input_select' and 'input_select'".format(
                            self.entity
                        ),
                        level="ERROR",
                    )

    def event_callback(self, event_name, data, kwargs):
        if data["entity_id"] == self.trigger_entity:
            if self.entity.startswith("input_select."):
                self.log(
                    "Setting {} to {}.".format(
                        self.entity, self.get_state(self.standard_entity)
                    )
                )
                self.select_option(self.entity, self.get_state(self.standard_entity))
            elif self.entity.startswith("input_number."):
                self.set_value(self.entity, self.get_state(self.standard_entity))
            else:
                self.log(
                    "Unsupported entity type {}. Supported are: 'input_select' and 'input_select'".format(
                        self.entity
                    ),
                    level="ERROR",
                )

    def terminate(self):
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)

        for listen_event_handle in self.listen_event_handle_list:
            self.cancel_listen_event(listen_event_handle)

        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
