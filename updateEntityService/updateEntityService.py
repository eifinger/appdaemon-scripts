import appdaemon.plugins.hass.hassapi as hass
import globals

#
# App which calls homeassistant.update_entity at an interval controlled by an input_boolean
#
# Args:
#
# app_switch: on/off switch for this app. example: input_boolean.warm_bath_before_wakeup
# entity_to_update: entity which should get updated : example: sensor.google_travel_time
# input_number: input_number which holds the interval. example: input_number.google_travel_time_update_interval
# counter (optional): counter entity which shows amount of service calls example: counter.google_maps_api_calls
# max_counter (optional): maximum amount of service calls. if it is exceeded no service will get called. example: 18000
#
# Release Notes
#
# Version 1.1:
#   Add warning if counter exceeds threshold
#
# Version 1.0:
#   Initial Version

THRESHOLD_PERCENTAGE = 0.9


class UpdateEntityService(hass.Hass):
    def initialize(self):
        self.timer_handle_list = []
        self.listen_state_handle_list = []

        self.app_switch = globals.get_arg(self.args, "app_switch")
        self.entity_to_update = globals.get_arg(self.args, "entity_to_update")
        self.input_number = globals.get_arg(self.args, "input_number")
        try:
            self.counter = globals.get_arg(self.args, "counter")
        except KeyError:
            self.counter = None
        try:
            self.max_counter = globals.get_arg(self.args, "max_counter")
        except KeyError:
            self.max_counter = None

        self.run_timer = self.run_in(
            self.update_entity_callback, float(self.get_state(self.input_number)) * 60
        )
        self.timer_handle_list.append(self.run_timer)

        self.listen_state_handle_list.append(
            self.listen_state(self.state_change, self.input_number)
        )

    def state_change(self, entity, attribute, old, new, kwargs):
        if new != "":
            self.log("Interval changed to: {}".format(new))
            if self.run_timer != None:
                self.cancel_timer(self.run_timer)
                self.log("Cancelled old run timer")
            self.run_timer = self.run_in(self.update_entity_callback, float(new) * 60)
            self.timer_handle_list.append(self.run_timer)
            self.log("Next update in: {} minutes".format(float(new)))

    def update_entity_callback(self, kwargs):
        if self.get_state(self.app_switch) == "on":
            if (
                self.counter != None
                and self.max_counter != None
                and int(self.get_state(self.counter)) >= int(self.max_counter)
            ):
                self.error(
                    "Maximum amount of {} exceeded on counter: {}".format(
                        self.max_counter, self.friendly_name(self.counter)
                    )
                )
            elif (
                self.counter != None
                and self.max_counter != None
                and int(self.get_state(self.counter))
                >= int(self.max_counter) * THRESHOLD_PERCENTAGE
            ):
                self.log(
                    "Threshold amount of {} exceeded on counter: {}".format(
                        THRESHOLD_PERCENTAGE, self.friendly_name(self.counter)
                    ),
                    level="WARNING",
                )
            else:
                self.call_service(
                    "homeassistant/update_entity", entity_id=self.entity_to_update
                )
                self.log(
                    "Updated {}.".format(self.friendly_name(self.entity_to_update))
                )
                self.run_timer = self.run_in(
                    self.update_entity_callback,
                    float(self.get_state(self.input_number)) * 60,
                )
                self.timer_handle_list.append(self.run_timer)

    def terminate(self):
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)

        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
