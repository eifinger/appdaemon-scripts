import appdaemon.plugins.hass.hassapi as hass
import globals
import datetime
#
# App which sets a thermostat to a target temperature based on a time from an entity
#
# Args:
#
# app_switch: on/off switch for this app. example: input_boolean.warm_bath_before_wakeup
# isHome: entity which shows if someone is home. example: input_boolean.is_home
# sleepMode: entity which shows if users are sleeping. example: input_boolean.sleepmode
# time_entity: sensor which determines when to run in the format 14:30. example: sensor.alarm_time
# upfront_time: how many minutes before the time_sensor to run. example: 60
# duration: After how many minutes should the thermostat be set back to its previous value. example: 60
# climat_entity: climate entity to set. example: climate.bad_thermostat
# target_entity: the entity holding the target temp. example: warm_bath_before_wakeup
# message: message to use in notification
# notify_name: who to notify. example: group_notifications
# use_alexa: use alexa for notification. example: False
#
# Release Notes
#
# Version 1.4:
#   Use sleepmode
#
# Version 1.3:
#   Use new formatted alarm_time
#
# Version 1.2.1:
#   Reschedule timer after first run
#
# Version 1.2:
#   Added isHome. Only run when someone is home
#
# Version 1.1:
#   Actually set the previous temp
#
# Version 1.0:
#   Initial Version


class SetThermostat(hass.Hass):

    def initialize(self):
        self.timer_handle_list = []
        self.listen_state_handle_list = []

        self.app_switch = globals.get_arg(self.args, "app_switch")
        self.time_entity = globals.get_arg(self.args, "time_entity")
        self.upfront_time = globals.get_arg(self.args, "upfront_time")
        self.duration = globals.get_arg(self.args, "duration")
        self.climat_entity = globals.get_arg(self.args, "climat_entity")
        self.target_entity = globals.get_arg(self.args, "target_entity")
        self.message = globals.get_arg(self.args, "message")
        self.notify_name = globals.get_arg(self.args, "notify_name")
        self.use_alexa = globals.get_arg(self.args, "use_alexa")
        self.isHome = globals.get_arg(self.args, "isHome")
        self.sleepMode = globals.get_arg(self.args, "sleepMode")

        self.notifier = self.get_app('Notifier')

        self.run_timer = None

        self.listen_state_handle_list.append(self.listen_state(self.schedule_trigger, self.time_entity))
        self.schedule_trigger(None, None, None, "Run", None)

    def schedule_trigger(self, entity, attribute, old, new, kwargs):
        if self.run_timer is not None:
            self.cancel_timer(self.run_timer)
            self.log("Cancelled scheduled trigger")
            self.run_timer = None
        # Not using 'new' so this function can be triggered during initialize
        time_entity_state = self.get_state(self.time_entity)
        if time_entity_state is not None and time_entity_state != "":
            event_time = datetime.datetime.strptime(time_entity_state, "%Y-%m-%d %H:%M:%S")
            event_time = event_time - datetime.timedelta(minutes=self.upfront_time)
            self.run_timer = self.run_at(self.trigger_thermostat, event_time)
            self.timer_handle_list.append(self.run_timer)
            self.log("Thermostat will trigger at {}".format(event_time))

    def trigger_thermostat(self, kwargs):
        if(
                self.get_state(self.app_switch) == "on"
                and self.get_state(self.isHome) == "on"
                and self.get_state(self.sleepMode) == "on"
        ):
            self.log(self.message.format(self.friendly_name(self.climat_entity), self.get_state(self.target_entity)))
            self.notifier.notify(
                self.notify_name,
                self.message.format(
                    self.friendly_name(self.climat_entity),
                    self.get_state(self.target_entity)),
                useAlexa=self.use_alexa)
            self.log("Turning {} on".format(self.climat_entity))
            self.call_service("climate/turn_on", entity_id=self.climat_entity)
            self.previous_temp = self.get_state(self.climat_entity, attribute="all")["attributes"]["temperature"]
            self.call_service(
                "climate/set_temperature",
                entity_id=self.climat_entity,
                temperature=self.get_state(self.target_entity))
            self.log("Resetting Thermostat in {} minutes.".format(self.duration))
            self.timer_handle_list.append(self.run_in(self.reset_thermostat, float(self.duration)*60))
            if self.run_timer is not None:
                self.cancel_timer(self.run_timer)

    def reset_thermostat(self, kwargs):
        if self.previous_temp is not None:
            self.log(self.message.format(self.friendly_name(self.climat_entity), self.previous_temp))
            self.notifier.notify(
                self.notify_name,
                self.message.format(
                    self.friendly_name(self.climat_entity),
                    self.previous_temp),
                useAlexa=self.use_alexa)
            self.call_service("climate/set_temperature", entity_id=self.climat_entity, temperature=self.previous_temp)
            self.schedule_trigger(None, None, None, "Run", None)

    def terminate(self):
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)

        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)

