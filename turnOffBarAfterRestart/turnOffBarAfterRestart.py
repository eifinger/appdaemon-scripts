import appdaemon.plugins.hass.hassapi as hass
import globals
import requests

#
# Will turn the bar table green and then off when homeassistant restarts to indicate the restart went well
#
#
# Args:
#
# light: light. example: light.bar_table
#
# Release Notes
#
# Version 1.0:
#   Initial Version


class TurnOffBarAfterRestart(hass.Hass):
    def initialize(self):

        self.timer_handle_list = []
        self.listen_event_handle_list = []
        self.listen_state_handle_list = []

        self.light = globals.get_arg(self.args, "light")

        self.timer_handle_list.append(self.run_in(self.turn_green_callback, 1))

    def turn_off_callback(self, kwargs):
        """Turn off light"""
        try:
            self.log("Turning {} off".format(self.friendly_name(self.light)))
            self.turn_off(self.light)
        except requests.exceptions.HTTPError as exception:
            self.log(
                "Error trying to turn off entity. Will try again in 1s. Error: {}".format(
                    exception
                ),
                level="WARNING",
            )
            self.timer_handle_list.append(self.run_in(self.turn_off_callback, 1))

    def turn_green_callback(self, kwargs):
        """This is needed because the turn_on command can result in a HTTP 503 when homeassistant is restarting"""
        try:
            self.call_service(
                "light/turn_on",
                entity_id=self.light,
                rgb_color=[0, 255, 0],
                white_value=0
            )
            self.log("Turning {} green".format(self.friendly_name(self.light)))
            self.timer_handle_list.append(self.run_in(self.turn_off_callback, 5))
        except requests.exceptions.HTTPError as exception:
            self.log(
                "Error trying to turn on entity. Will try again in 1s. Error: {}".format(
                    exception
                ),
                level="WARNING",
            )
            self.timer_handle_list.append(self.run_in(self.turn_green_callback, 1))

    def terminate(self):
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)

        for listen_event_handle in self.listen_event_handle_list:
            self.cancel_listen_event(listen_event_handle)

        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
