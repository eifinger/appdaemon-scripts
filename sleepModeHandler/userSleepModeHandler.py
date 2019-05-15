import appdaemon.plugins.hass.hassapi as hass
import globals
from queue import Queue

#
# App which sets the sleep mode on/off
#
# Args:
#   app_switch: on/off switch for this app. example: input_boolean.turn_fan_on_when_hot
#   input_boolean: input_boolean holding the sleepmode. example: input_boolean.sleepmode
#   location_sensor: location sensor of user. example: sensor.location_user_one
#   room: Room name in which user must be. example: Wohnzimmer
#   asleep_duration: seconds to wait before turning sleepmode on. example: 120
#   awake_duration: seconds to wait before turning sleepmode off. example: 120
#
# Release Notes
#
# Version 1.3:
#   Reimplementation
#
# Version 1.2:
#   Only trigger on an actual change
#
# Version 1.1:
#   Added asleep_duration and awake_duration instead of duration
#
# Version 1.0:
#   Initial Version


class UserSleepModeHandler(hass.Hass):
    def initialize(self):
        self.listen_state_handle_list = []

        self.app_switch = globals.get_arg(self.args, "app_switch")
        self.location_sensor = globals.get_arg(self.args, "location_sensor")
        self.room = globals.get_arg(self.args, "room")
        self.asleep_duration = globals.get_arg(self.args, "asleep_duration")
        self.awake_duration = globals.get_arg(self.args, "awake_duration")
        self.input_boolean = globals.get_arg(self.args, "input_boolean")

        self.timer_handle = None

        self.queue = Queue()

        self.listen_state_handle_list.append(
            self.listen_state(self.state_change, self.location_sensor)
        )

    def state_change(self, entity, attribute, old, new, kwargs):
        """Handle state changes of the location sensor"""
        if new != old:
            if self.get_state(self.app_switch) == "on":
                # User left room
                if old == self.room:
                    self.log(
                        f"User left {self.room}. Resetting timer. Will trigger awake in {self.awake_duration}s"
                    )
                    if self.timer_handle is not None:
                        self.cancel_timer(self.timer_handle)
                    self.timer_handle = self.run_in(self.awake, self.awake_duration)
                elif new == self.room:
                    self.log(
                        f"User entered {self.room}. "
                        f"Resetting timer. Will trigger asleep in {self.asleep_duration}s"
                    )
                    if self.timer_handle is not None:
                        self.cancel_timer(self.timer_handle)
                    self.timer_handle = self.run_in(self.asleep, self.asleep_duration)

    def awake(self, kwargs):
        """User left room for more than self.awake_duration. Turn off sleep mode"""
        current_location = self.get_state(self.location_sensor)
        if current_location != self.room:
            if self.get_state(self.input_boolean) == "on":
                self.log(
                    f"{self.friendly_name(self.location_sensor)} is outside {self.room} "
                    f"for more than {self.asleep_duration}s. "
                    f"Turning {self.input_boolean} off"
                )
                self.turn_off(self.input_boolean)
        else:
            self.log(f"Timer ran out but user is in {current_location}")

    def asleep(self, kwargs):
        """User stayed in room for more than self.asleep_duration. Turn on sleep mode"""
        current_location = self.get_state(self.location_sensor)
        if current_location == self.room:
            if self.get_state(self.input_boolean) == "off":
                self.log(
                    f"{self.friendly_name(self.location_sensor)} is in {self.room} "
                    f"for more than {self.asleep_duration}s. "
                    f"Turning {self.input_boolean} on"
                )
                self.turn_on(self.input_boolean)
        else:
            self.log(f"Timer ran out but user is in {current_location}")

    def insert_room_state_change(self, entity, attribute, old, new, kwargs):
        """Insert a new room state change into the queue"""
        self.queue.put(new)

    def calculate_room_presence(self, kwargs):
        """Calculate the percentage the person was in the target room since the last invocation"""
        state_changes = []
        while not self.queue.empty():
            state_changes.append(self.queue.get())
        for state_change in state_changes:
            pass

    def terminate(self):
        if self.timer_handle is not None:
            self.cancel_timer(self.timer_handle)

        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
