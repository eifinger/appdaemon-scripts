import appdaemon.plugins.hass.hassapi as hass
import random
import isodate
import datetime


class TurnEntityOffInXIntent(hass.Hass):
    def initialize(self):
        """
        Initialize the application.

        Args:
            self: (todo): write your description
        """
        self.timer_handle_list = []
        self.listService = self.get_app("listService")
        return

    def getIntentResponse(self, slots, devicename):
        """
        Generate a list of the response.

        Args:
            self: (todo): write your description
            slots: (todo): write your description
            devicename: (str): write your description
        """
        ############################################
        # an Intent to give back the state from a light.
        # but it also can be any other kind of entity
        ############################################
        try:

            entityname = self.listService.getSwitchable()[slots["device"]]
            # to upper because of https://github.com/gweis/isodate/issues/52
            duration = isodate.parse_duration(slots["duration"].upper())
            self.timer_handle_list.append(
                self.run_in(
                    self.turn_off_callback,
                    duration.total_seconds(),
                    entityname=entityname,
                )
            )
            minutes, seconds = divmod(duration.total_seconds(), 60)
            minutes = int(minutes)
            seconds = int(seconds)
            if minutes == 0:
                if seconds == 1:
                    timeText = " einer Sekunde"
                else:
                    timeText = " {} Sekunden".format(seconds)
            elif minutes == 1:
                if seconds == 1:
                    timeText = " einer Minute und einer Sekunde"
                elif seconds == 0:
                    timeText = " einer Minute"
                else:
                    timeText = " einer Minute und {} Sekunden".format(seconds)
            else:
                if seconds == 1:
                    timeText = " {} Minuten und einer Sekunde".format(minutes)
                elif seconds == 0:
                    timeText = " {} Minuten".format(minutes)
                else:
                    timeText = " {} Minuten und {} Sekunden".format(minutes, seconds)
            text = self.args["textLine"] + timeText + " ab."
        except Exception as e:
            self.log("Exception: {}".format(e))
            self.log("slots: {}".format(slots))
            text = self.random_arg(self.args["Error"])
        return text

    def turn_off_callback(self, kwargs):
        """
        Turn off the callback : ~.

        Args:
            self: (todo): write your description
        """
        entityname = kwargs["entityname"]
        self.log("Turning off {}".format(entityname))
        self.turn_off(entityname)

    def random_arg(self, argName):
        """
        Return the value from argname.

        Args:
            self: (todo): write your description
            argName: (str): write your description
        """
        ############################################
        # pick a random text from a list
        ############################################
        if isinstance(argName, list):
            text = random.choice(argName)
        else:
            text = argName
        return text

    def terminate(self):
        """
        Terminate the timer.

        Args:
            self: (todo): write your description
        """
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)
