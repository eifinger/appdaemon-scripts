import appdaemon.plugins.hass.hassapi as hass
from requests.exceptions import HTTPError

#
# App which sets a homeassistant entity as a heartbeat to check for threadstarvation etc
#
# Args:
# sensor: sensor.appdaemon_heartbeat
#
# Release Notes
#
# Version 1.1:
#   Set start to None run_minutely will run after 1 minute
#
# Version 1.0:
#   Initial Version


class Heartbeat(hass.Hass):
    def initialize(self):
        """
        Initialize the sensor.

        Args:
            self: (todo): write your description
        """
        self.timer_handle_list = []

        self.sensor = self.args["sensor"]

        self.heartbeat(None)

        self.timer_handle_list.append(self.run_minutely(self.heartbeat, start=None))

    def heartbeat(self, kwargs):
        """
        Tells the heartbeat the heartbeat.

        Args:
            self: (todo): write your description
        """
        try:
            self.set_state(self.sensor, state=str(self.time()))
            self.log("Heartbeat", level="DEBUG")
        except HTTPError as exception:
            self.log(
                "Error trying to set entity. Will try again in 5s. Error: {}".format(
                    exception
                ),
                level="WARNING",
            )
            self.timer_handle_list.append(self.run_in(self.heartbeat, 5))

    def terminate(self):
        """
        Terminate the timer.

        Args:
            self: (todo): write your description
        """
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)
