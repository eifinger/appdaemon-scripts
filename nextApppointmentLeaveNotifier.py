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
# input_number: input_number which tells how early to leave. example: input_number.leave_time_offset
# destination_name_sensor: Sensor which holds the Destination name to use in notification. example: sensor.cal_next_appointment_location
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
        self.input_number = self.get_arg("input_number")
        self.destination_name_sensor = self.get_arg("destination_name_sensor")

        notification_time = self.calculate_notification_time()
        self.timer_handle = self.run_at(self.notify,notification_time)

        self.listen_state_handle_list.append(self.listen_state(self.state_change, self.sensor))
        self.listen_state_handle_list.append(self.listen_state(self.state_change, self.sensor))

    def state_change(self, entity, attributes, old, new, kwargs):
        self.cancel_timer(self.timer_handle)
        notification_time = self.calculate_notification_time()
        self.timer_handle = self.run_at(self.notify,notification_time)


    def calculate_notification_time(self):
        time_to_leave = self.convert_utc(self.get_state(self.sensor))
        offset_raw = self.get_state(self.input_number)
        offset_raw = offset_raw[:offset_raw.find(".")]
        offset = int(offset_raw)
        time_to_leave += datetime.timedelta(0,offset * 60) 
        return time_to_leave

    def notfiy(self):
        self.log("Notify user")
        self.call_service("notify/" + self.notify_name, message=messages.time_to_leave.format(self.get_state(self.destination_name_sensor)))

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

        self.cancel_timer(self.timer_handle)