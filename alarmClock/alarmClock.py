import appdaemon.plugins.hass.hassapi as hass
import globals
import datetime
#
# Alarm Clock App
#
#
# Args:
#  alarm_time: entity which holds the alarm time. example: sensor.alarm_time
#  wakemeup: entity which enables the alarm. example: input_boolean.wakemeup
#  naturalwakeup: entity which enables the natural wake up fade in. example: input_number.alarm_natural_wakeup_fade_in
#  alarmweekday: entity which enables alarm only on weekdays. example: input_boolean.alarmweekday
#  radiowakeup: entity which enables radio wake up. example: input_boolean.radiowakeup
#  TODO radioplayer: entity which holds the information which radio player to select. example: input_select.wakeup_radioplayer
#  wakeup_light: light to fade in. example: light.bedroom_yeelight
#  isweekday: entity which holds the information whether today is a week day. example: binary_sensor.workday_today
#  notify_name: Who to notify. example: group_notifications
#  message_<LANG>: localized message to use in notification. e.g. "You left open {} Dummy."
#
# Release Notes
#
# Version 1.2:
#   use Notify App
#
# Version 1.1:
#   message now directly in own yaml instead of message module
#
# Version 1.0:
#   Initial Version

class AlarmClock(hass.Hass):

    def initialize(self):
    
        self.timer_handle_list = []
        self.listen_event_handle_list = []
        self.listen_state_handle_list = []

        self.alarm_time = globals.get_arg(self.args,"alarm_time")
        self.wakemeup = globals.get_arg(self.args,"wakemeup")
        self.naturalwakeup = globals.get_arg(self.args,"naturalwakeup")
        self.alarmweekday = globals.get_arg(self.args,"alarmweekday")
        self.radiowakeup = globals.get_arg(self.args,"radiowakeup")
        self.isweekday = globals.get_arg(self.args,"isweekday")
        self.notify_name = globals.get_arg(self.args,"notify_name")
        self.wakeup_light = globals.get_arg(self.args,"wakeup_light")
        self.message = globals.get_arg(self.args, "message_DE")

        self.notifier = self.get_app('Notifier')

        self.brightness = 100
        self.rgb = (255,255,255)
        

        self.cached_alarm_time = self.get_state(self.alarm_time)
        self.cached_fade_in_time = self.get_state(self.naturalwakeup)
        self.add_timer()

        self.listen_state_handle_list.append(self.listen_state(self.state_change, self.alarm_time))
        self.listen_state_handle_list.append(self.listen_state(self.state_change, self.naturalwakeup))
    
    def state_change(self, entity, attributes, old, new, kwargs):
        if new != None and new != old:
            self.timer_handle_list.remove(self.alarm_timer)
            self.cancel_timer(self.alarm_timer)
            if entity == self.alarm_time:
                self.log("Alarm time change: {}".format(new))
                self.cached_alarm_time = new
            elif entity == self.naturalwakeup:
                self.log("Fade-In time change: {}".format(new))
                self.cached_fade_in_time = new
            self.add_timer()

    def add_timer(self):
        self.log("cached_alarm_time: {}".format(self.cached_alarm_time))
        self.log("cached_fade_in_time: {}".format(self.cached_fade_in_time))
        hours = self.cached_alarm_time.split(":",1)[0]
        self.log("hours: {}".format(hours))
        minutes = self.cached_alarm_time.split(":",1)[1]
        self.log("minutes: {}".format(minutes))
        offset = self.cached_fade_in_time.split(".",1)[0]

        runtime = datetime.time(int(hours),int(minutes))
        today = datetime.date.today()
        rundatetime = datetime.datetime.combine(today, runtime)
        event_time = rundatetime - datetime.timedelta(minutes=int(offset))

        #check if event is in the past
        if datetime.datetime.now() > event_time:
            event_time = event_time + datetime.timedelta(days=1)

        self.alarm_timer = self.run_at(self.trigger_alarm, event_time)
        self.timer_handle_list.append(self.alarm_timer)
        self.log("Alarm will trigger at {}".format(event_time))

    def trigger_alarm(self, kwargs):
        if self.get_state(self.wakemeup) == "on":
            if self.get_state(self.alarmweekday) == "off" or (self.get_state(self.alarmweekday) == "on" and self.get_state(self.isweekday) == "on"):
                if float(self.cached_fade_in_time) > 0:
                    self.call_service("light/turn_on", entity_id = self.wakeup_light, transition = self.cached_fade_in_time, brightness = self.brightness)
                self.timer_handle_list.append(self.run_in(self.run_alarm, float(self.cached_fade_in_time)))


    def run_alarm(self, kwargs):
        self.notifier.notify(self.notify_name, self.message)   
        #TODO radio

                
     
    def terminate(self):
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)

        for listen_event_handle in self.listen_event_handle_list:
            self.cancel_listen_event(listen_event_handle)

        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)

    