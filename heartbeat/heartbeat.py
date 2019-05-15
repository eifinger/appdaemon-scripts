import appdaemon.plugins.hass.hassapi as hass
import globals
import requests

#
# App which sets a homeassistant entity as a heartbeat to check for threadstarvation etc
#
# Args:
# sensor: sensor.appdaemon_heartbeat
#
# Release Notes
#
# Version 1.0:
#   Initial Version


class Heartbeat(hass.Hass):
    def initialize(self):
        self.timer_handle_list = []

        self.sensor = globals.get_arg(self.args, "sensor")

        self.heartbeat(None)

        self.timer_handle_list.append(
            self.run_minutely(self.heartbeat, start=self.time())
        )

    def heartbeat(self, kwargs):
        try:
            self.set_state(self.sensor, state=str(self.time()))
            self.log("Heartbeat", level="DEBUG")
        except requests.exceptions.HTTPError as exception:
            self.log(
                "Error trying to set entity. Will try again in 1s. Error: {}".format(
                    exception
                ),
                level="WARNING",
            )
            self.timer_handle_list.append(self.run_in(self.heartbeat, 1))

    def terminate(self):
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)
