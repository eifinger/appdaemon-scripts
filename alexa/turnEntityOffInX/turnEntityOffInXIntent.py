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
            duration.total_seconds()
            self.timer_handle_list.append(self.run_in(self.turn_off_callback, duration.total_seconds(), entityname=entityname))
            text = self.random_arg(self.args["textLine"])
        except Exception as e:
            self.log("Exception: {}".format(e))
            text = self.random_arg(self.args["Error"])
        return text

    def turn_off_callback(self, kwargs):
        entityname = kwargs["entityname"]
        self.log("Turning off {}".format(entityname))
        self.turn_off(entityname)

    def terminate(self):
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)