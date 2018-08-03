import appdaemon.plugins.hass.hassapi as hass
import random
import isodate
import datetime

class TurnEntityOffInXIntent(hass.Hass):

    def initialize(self):
        self.timer_handle_list = []
        return

    def getIntentResponse(self, slots, devicename):
        ############################################
        # an Intent to give back the state from a light.
        # but it also can be any other kind of entity
        ############################################           
        try:
            self.log("slots: {}".format(slots))
            entityname = self.args["entities"][slots["device"]]
            #to upper because of https://github.com/gweis/isodate/issues/52
            duration = isodate.parse_duration(slots["duration"].upper())
            self.timer_handle_list.append(self.run_in(self.turn_off_callback, duration.total_seconds(), entityname=entityname))
            minutes, seconds = divmod(duration.total_seconds(), 60)
            if int(minutes) == 0:
                if int(seconds) == 1:
                    timeText = " einer Sekunde"
                else:
                    timeText = " {} Sekunden".format(int(seconds))
            elif int(minutes) == 1:
                if int(seconds) == 1:
                    timeText = " einer Minute und einer Sekunde"
                else:
                    timeText = " einer Minute und {} Sekunden".format(int(seconds))
            else:
                if int(seconds) == 0:
                    timeText = " {} Minuten".format(minutes)
                else:
                    timeText = " {} Minuten und {} Sekunden".format(int(minutes), int(seconds))
            text = self.args["textLine"] + timeText + " ab."
        except Exception as e:
            self.log("Exception: {}".format(e))
            text = self.random_arg(self.args["Error"])
        return text

    def turn_off_callback(self, kwargs):
        entityname = kwargs["entityname"]
        self.log("Turning off {}".format(entityname))
        self.turn_off(entityname)

    def random_arg(self,argName):
        ############################################
        # pick a random text from a list
        ############################################
        if isinstance(argName,list):
            text = random.choice(argName)
        else:
            text = argName
        return text

    def terminate(self):
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)