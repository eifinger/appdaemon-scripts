import appdaemon.plugins.hass.hassapi as hass
import globals

#
# App to send notification when a sensor changes state
#
# Args:
#
#  app_switch: on/off switch for this app. example: input_boolean.turn_fan_on_when_hot
#  sensor: sensor to monitor. example: sensor.upstairs_smoke
#  isHome: input_boolean which shows if someone is home. example: input_boolean.isHome
#  isHome_delay: delay to wait for user to come home before notifying. example: 10
#
# Release Notes
#
# Version 1.3.1:
#   Use consistent message variable
#
# Version 1.3:
#   use Notify App
#
# Version 1.2:
#   message now directly in own yaml instead of message module
#
# Version 1.1:
#   Added isHome_delay
#
# Version 1.0:
#   Initial Version


class NotifyOfActionWhenAway(hass.Hass):
    def initialize(self):

        self.listen_state_handle_list = []
        self.timer_handle_list = []

        self.app_switch = globals.get_arg(self.args, "app_switch")
        self.notify_name = globals.get_arg(self.args, "notify_name")
        self.isHome_delay = globals.get_arg(self.args, "isHome_delay")
        self.isHome = globals.get_arg(self.args, "isHome")
        self.message = globals.get_arg(self.args, "message")

        self.notifier = self.get_app("Notifier")

        for sensor in globals.get_arg_list(self.args, "sensor"):
            self.listen_state_handle_list.append(
                self.listen_state(self.state_change, sensor)
            )

    def state_change(self, entity, attribute, old, new, kwargs):
        if self.get_state(self.app_switch) == "on":
            if new != "" and new != old:
                if self.get_state(self.isHome) == "off":
                    if (
                        entity.startswith("binary_sensor.motion_sensor")
                        and new == "off"
                    ):
                        pass
                    else:
                        self.log(
                            "Waiting {} seconds for someone to come home".format(
                                self.isHome_delay
                            )
                        )
                        self.timer_handle_list.append(
                            self.run_in(
                                self.notify_if_no_one_home,
                                self.isHome_delay,
                                sensor=entity,
                                new=new,
                            )
                        )

    def notify_if_no_one_home(self, kwargs):
        if self.get_state(self.isHome) == "off":
            self.log(
                "{} changed to {}".format(
                    self.friendly_name(kwargs["sensor"]), kwargs["new"]
                )
            )
            self.notifier.notify(
                self.notify_name,
                self.message.format(
                    self.friendly_name(kwargs["sensor"]), kwargs["new"]
                ),
                useAlexa=False,
            )

    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)

        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)
