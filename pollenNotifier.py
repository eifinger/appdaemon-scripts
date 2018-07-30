import appdaemon.plugins.hass.hassapi as hass
import globals
import messages
import datetime
#
# App which notifies you when there is a pollen forecast for today
# Used with sensors getting data from https://opendata.dwd.de/climate_environment/health/alerts/s31fg.json
#
#
# Args:
#
# app_switch: on/off switch for this app. example: input_boolean.turn_fan_on_when_hot
# pollen_sensor: sensor which shows pollen for today. example: sensor.pollen_101_roggen_today
# pollen_name: Name of the allergene. example: Roggen
# notify_name: Who to notify. example: group_notifications
# notify_time: When to notify. example: 08:00
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class PollenNotifier(hass.Hass):

    def initialize(self):
    
        self.timer_handle_list = []
        self.listen_event_handle_list = []
        self.listen_state_handle_list = []

        self.app_switch = globals.get_arg(self.args,"app_switch")
        self.pollen_sensor = globals.get_arg(self.args,"pollen_sensor")
        self.pollen_name = globals.get_arg(self.args,"pollen_name")
        self.notify_name = globals.get_arg(self.args,"notify_name")
        self.notify_time = globals.get_arg(self.args,"notify_time")

        self.mappingsdict = {}
        self.mappingsdict["-1"] = "keine Daten"
        self.mappingsdict["0"] = "Keine"
        self.mappingsdict["0-1"] = "Keine bis Geringe"
        self.mappingsdict["1"] = "Geringe"
        self.mappingsdict["1-2"] = "Geringe bis Mittlere"
        self.mappingsdict["2"] = "Mittlere"
        self.mappingsdict["2-3"] = "Mittlere bis Hohe"
        self.mappingsdict["3"] = "Hohe"


        hours = self.notify_time.split(":",1)[0]
        minutes = self.notify_time.split(":",1)[1]
        self.timer_handle_list.append(self.run_daily(self.run_daily_callback, datetime.time(hours, minutes, 0)))

    def run_daily_callback(self, kwargs):
        """Check if there is an pollen forcast and notify the user about it"""
        if self.get_state(self.app_switch) == "on":
            pollen_sensor_state = self.get_state(self.pollen_sensor)
            self.log("{} Belastung Heute: {}".format(self.pollen_name,pollen_sensor_state))

            if pollen_sensor_state == "-1":
                message = messages.no_pollen_data().format("Heute", self.pollen_name)
            elif pollen_sensor_state == "0":
                message = messages.pollen_data().format("Heute", self.mappingsdict[pollen_sensor_state], self.pollen_name) + " Genieß den Tag!"
            else:
                message = messages.pollen_data().format("Heute", self.mappingsdict[pollen_sensor_state], self.pollen_name)

            self.log("Notifying user")
            self.call_service("notify/" + self.notify_name,message=message)
        
    def terminate(self):
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)

        for listen_event_handle in self.listen_event_handle_list:
            self.cancel_listen_event(listen_event_handle)

        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)