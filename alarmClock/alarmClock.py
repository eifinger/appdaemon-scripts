import appdaemon.plugins.hass.hassapi as hass
import datetime
import math


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
#  message: localized message to use in notification. e.g. "You left open {} Dummy."
#
# Release Notes
#
# Version 1.4:
#   Catch unknown
#
# Version 1.3.1:
#   Use consistent message variable
#
# Version 1.3:
#   Use new formatted alarm_time
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
        """
        Initialize the internal state.

        Args:
            self: (todo): write your description
        """

        self.timer_handle_list = []
        self.listen_event_handle_list = []
        self.listen_state_handle_list = []

        self.alarm_time = self.args["alarm_time"]
        self.wakemeup = self.args["wakemeup"]
        self.naturalwakeup = self.args["naturalwakeup"]
        self.alarmweekday = self.args["alarmweekday"]
        self.radiowakeup = self.args["radiowakeup"]
        self.isweekday = self.args["isweekday"]
        self.notify_name = self.args["notify_name"]
        self.wakeup_light = self.args["wakeup_light"]
        self.fade_in_time_multiplicator = self.args["fade_in_time_multiplicator"]
        self.message = self.args["message"]
        self.button = self.args["button"]

        self.notifier = self.get_app("Notifier")

        self.brightness = 100
        self.rgb_color = [255, 120, 0]
        self.alarm_timer = None

        self.cached_alarm_time = self.get_state(self.alarm_time)
        self.cached_fade_in_time = self.get_state(self.naturalwakeup)
        self.add_timer()

        self.listen_state_handle_list.append(
            self.listen_state(self.alarm_change, self.alarm_time)
        )
        self.listen_state_handle_list.append(
            self.listen_state(self.naturalwakeup_change, self.naturalwakeup)
        )

        self.listen_event_handle_list.append(
            self.listen_event(self.button_clicked, "xiaomi_aqara.click")
        )

    def alarm_change(self, entity, attributes, old, new, kwargs):
        """
        Cancel a new alarm.

        Args:
            self: (todo): write your description
            entity: (todo): write your description
            attributes: (dict): write your description
            old: (str): write your description
            new: (str): write your description
        """
        if new is not None and new != old and new != self.cached_alarm_time:
            if self.alarm_timer is not None:
                if self.alarm_timer in self.timer_handle_list:
                    self.timer_handle_list.remove(self.alarm_timer)
                self.cancel_timer(self.alarm_timer)
            self.log("Alarm time change: {}".format(new))
            self.cached_alarm_time = new
            self.add_timer()

    def naturalwakeup_change(self, entity, attributes, old, new, kwargs):
        """
        Cancel a new change.

        Args:
            self: (todo): write your description
            entity: (todo): write your description
            attributes: (dict): write your description
            old: (todo): write your description
            new: (todo): write your description
        """
        if new is not None and new != old and new != self.cached_fade_in_time:
            if self.alarm_timer is not None:
                if self.alarm_timer in self.timer_handle_list:
                    self.timer_handle_list.remove(self.alarm_timer)
                self.cancel_timer(self.alarm_timer)
            self.log("Fade-In time change: {}".format(new))
            self.cached_fade_in_time = new
            self.add_timer()

    def add_timer(self):
        """
        Add a timer.

        Args:
            self: (todo): write your description
        """
        self.log("cached_alarm_time: {}".format(self.cached_alarm_time))
        self.log("cached_fade_in_time: {}".format(self.cached_fade_in_time))
        offset = self.cached_fade_in_time.split(".", 1)[0]

        if (
            self.cached_alarm_time is not None
            and self.cached_alarm_time != ""
            and self.cached_alarm_time != "unknown"
        ):
            run_datetime = datetime.datetime.strptime(
                self.cached_alarm_time, "%Y-%m-%d %H:%M:%S"
            )
            event_time = run_datetime - datetime.timedelta(minutes=int(offset))
            try:
                self.alarm_timer = self.run_at(self.trigger_alarm, event_time)
                self.timer_handle_list.append(self.alarm_timer)
                self.log("Alarm will trigger at {}".format(event_time))
            except ValueError:
                self.log("New trigger time would be in the past: {}".format(event_time))

    def trigger_alarm(self, kwargs):
        """
        Trigger an alarm on a specific service.

        Args:
            self: (todo): write your description
        """
        if self.get_state(self.wakemeup) == "on":
            if self.get_state(self.alarmweekday) == "off" or (
                self.get_state(self.alarmweekday) == "on"
                and self.get_state(self.isweekday) == "on"
            ):
                if float(self.cached_fade_in_time) > 0:
                    self.log(
                        "Turning on {}".format(self.friendly_name(self.wakeup_light))
                    )
                    self.call_service(
                        "light/turn_on", entity_id=self.wakeup_light, brightness_pct=1
                    )
                    transition = int(
                        float(self.cached_fade_in_time)
                        * int(self.fade_in_time_multiplicator)
                    )
                    self.log(
                        "Transitioning light in over {} seconds".format(transition)
                    )
                    self.timer_handle_list.append(
                        self.run_in(
                            self.run_fade_in, 1, transition=transition, brightness_pct=1
                        )
                    )
                self.timer_handle_list.append(
                    self.run_in(self.run_alarm, float(self.cached_fade_in_time))
                )

    def button_clicked(self, event_name, data, kwargs):
        """Extra callback method to trigger the wakeup light on demand by pressing a Xiaomi Button"""
        if data["entity_id"] == self.button:
            if data["click_type"] == "single":
                if float(self.cached_fade_in_time) > 0:
                    self.log(
                        "Turning on {}".format(self.friendly_name(self.wakeup_light))
                    )
                    self.call_service(
                        "light/turn_on", entity_id=self.wakeup_light, brightness_pct=1
                    )
                    transition = int(
                        float(self.cached_fade_in_time)
                        * int(self.fade_in_time_multiplicator)
                    )
                    self.log(
                        "Transitioning light in over {} seconds".format(transition)
                    )
                    self.timer_handle_list.append(
                        self.run_in(
                            self.run_fade_in, 1, transition=transition, brightness_pct=1
                        )
                    )

    def run_fade_in(self, kwargs):
        """
        Callback / recursion style because the transition feature does not seem to work well with Yeelight for
        transition values greater than 10s.
        :param kwargs:
        :return:
        """
        wait_factor = 1
        transition = kwargs["transition"]
        brightness_pct = kwargs["brightness_pct"]
        pct_increase = 1 / transition
        self.log("pct_increase: {}".format(pct_increase), level="DEBUG")
        if pct_increase < 0.01:
            wait_factor = math.ceil(0.01 / pct_increase)
            pct_increase = 0.01
            self.log(
                "pct_increase smaller than 1% next run_in in {} seconds".format(
                    wait_factor
                ),
                level="DEBUG",
            )
        brightness_pct_old = brightness_pct
        self.log("brightness_pct_old: {}".format(brightness_pct_old), level="DEBUG")
        brightness_pct_new = int((brightness_pct_old + pct_increase * 100))
        self.log("brightness_pct_new: {}".format(brightness_pct_new), level="DEBUG")
        if brightness_pct_new < 100:
            self.call_service(
                "light/turn_on",
                entity_id=self.wakeup_light,
                rgb_color=self.rgb_color,
                brightness_pct=brightness_pct_new,
            )
            self.timer_handle_list.append(
                self.run_in(
                    self.run_fade_in,
                    wait_factor,
                    transition=transition,
                    brightness_pct=brightness_pct_new,
                )
            )

    def run_alarm(self, kwargs):
        """
        Run a message.

        Args:
            self: (todo): write your description
        """
        self.notifier.notify(self.notify_name, self.message)
        # TODO radio

    def terminate(self):
        """
        Terminate all the event.

        Args:
            self: (todo): write your description
        """
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)

        for listen_event_handle in self.listen_event_handle_list:
            self.cancel_listen_event(listen_event_handle)

        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
