import appdaemon.plugins.hass.hassapi as hass
import datetime
import secrets
import messages

#
# App which notifies the user to start to the next appointment
#
#
# Args:
# sensor: sensor to watch. example: sensor.calc_leave_time
# notify_input_boolean: input_boolean determining whether to notify. example: input_boolean.announce_time_to_leave
# notify_name: Who to notify. example: group_notifications
# destination_name_sensor: Sensor which holds the Destination name to use in notification. example: sensor.cal_next_appointment_location
# travel_time_sensor: sensor which holds the travel time. example: sensor.travel_time_next_appointment_location
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class NextApppointmentLeaveNotifier(hass.Hass):

    def initialize(self):

        self.listen_state_handle_list = []
        

        self.sensor = self.get_arg("sensor")
        self.notify_input_boolean = self.get_arg("notify_input_boolean")
        self.notify_name = self.get_arg("notify_name")
        self.destination_name_sensor = self.get_arg("destination_name_sensor")
        self.travel_time_sensor = self.get_arg("travel_time_sensor")

        self.timer_handle = None

        self.google_source_url = "http://maps.google.com/maps?q="

        #Used to check of user got already notified for this event
        self.location_of_last_notified_event = ""

        if self.get_state(self.sensor) != "unknown":
            notification_time = datetime.datetime.strptime(self.get_state(self.sensor),"%Y-%m-%d %H:%M")
            if self.get_state(self.travel_time_sensor) != "unknown":
                try:
                    self.timer_handle = self.run_at(self.notify_user,notification_time)
                    self.log("Will notify at {}".format(notification_time))
                except ValueError:
                    self.log("Notification time is in the past")

        self.listen_state_handle_list.append(self.listen_state(self.state_change, self.sensor))

    def state_change(self, entity, attributes, old, new, kwargs):
        try:
            self.cancel_timer(self.timer_handle)
        except AttributeError:
            #Timer was not set
            pass
        #Parse time string from sensor. For parsing information look at http://strftime.org/
        if self.get_state(self.sensor) != "unknown":
            notification_time = datetime.datetime.strptime(self.get_state(self.sensor),"%Y-%m-%d %H:%M")
            if self.get_state(self.travel_time_sensor) != "unknown":
                try:
                    self.timer_handle = self.run_at(self.notify_user,notification_time)
                    self.log("Will notify at {}".format(notification_time))
                except ValueError:
                    self.log("Notification time is in the past")

    def notify_user(self, *kwargs):
        if self.get_state(self.notify_input_boolean) == "on":
            location_name = self.get_state(self.destination_name_sensor)
            if self.location_of_last_notified_event == location_name:
                self.log("User already got notified for {}".format())
            else:
                google_maps_url = self.google_source_url + location_name.replace(" ","+")
                self.log("Notify user")
                self.call_service("notify/" + self.notify_name, message=messages.time_to_leave().format(location_name,self.get_state(self.travel_time_sensor), google_maps_url))
                self.location_of_last_notified_event = location_name
        else:
            self.log("Notification is turned off")

    def get_arg(self, key):
        key = self.args[key]
        if key.startswith("secret_"):
            if key in secrets.secret_dict:
                return secrets.secret_dict[key]
            else:
                self.log("Could not find {} in secret_dict".format(key))
        else:
            return key

    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
        if self.timer_handle != None:
            self.cancel_timer(self.timer_handle)