import appdaemon.plugins.hass.hassapi as hass
import datetime

#
# App to notify if user_one is leaving a zone.
# User had to be in that zone 3 minutes before
# in order for the notification to be triggered
#
# Args:
#   app_switch: on/off switch for this app.
#               example: input_boolean.turn_fan_on_when_hot
#   device: Device to track
#   user_name: Name of the user used in the notification message
#   delay: seconds to wait before notifying. Maybe user returns to zone.
#          This should be too small to avoid false positives from your tracker.
#          I am using GPS Logger on Android and sometimes my device switches
#          from work to home and 2 minutes later back. example: 120
#   lingering_time: time a user has to be in a zone to trigger this app.
#                   example: 3600
#   zone: zone name from which the user is leaving
#   notify_name: Who to notify. example: group_notifications
#   message: localized message to use in notification
#   travel_time_sensor (optional): Sensor showing the travel time home.
#                                  example: sensor.travel_time_home_user_one
#   travel_time_sensor_message (optional): Additional notify message.
#
# Release Notes
#
# Version 1.11:
#   Catch new state might be None
#
# Version 1.10:
#   Catch old state might be None during startup
#
# Version 1.9:
#   PEP8 style and log message when updating travel_time_sensor
#
# Version 1.8:
#   Add travel time in notification message
#
# Version 1.7.1:
#   Fix delay in notify message. Only input the minutes not the tuple
#
# Version 1.7:
#   use Notify App
#
# Version 1.6:
#   notify message includes delay
#
# Version 1.5:
#   message now directly in own yaml instead of message module
#
# Version 1.4:
#   additional note for delay and better handling of zone_entered for
#   false positives
#
# Version 1.3:
#   delay and lingering_time now as args
#
# Version 1.2:
#   Added app_switch
#
# Version 1.1:
#   Rework without proximity
#
# Version 1.0:
#   Initial Version


class LeavingZoneNotifier(hass.Hass):
    def initialize(self):
        """
        Initializes initial initialization.

        Args:
            self: (todo): write your description
        """

        self.listen_state_handle_list = []
        self.timer_handle_list = []

        self.app_switch = self.args["app_switch"]
        self.user_name = self.args["user_name"]
        self.zone = self.args["zone"]
        self.notify_name = self.args["notify_name"]
        self.device = self.args["device"]
        # 'lingering_time' the time a user has to stay in a zone
        # for this app to trigger
        self.lingering_time = self.args["lingering_time"]
        self.delay = self.args["delay"]
        self.message = self.args["message"]
        self.travel_time_sensor = self.args.get("travel_time_sensor")
        self.travel_time_sensor_message = self.args.get("travel_time_sensor_message")

        self.user_entered_zone = None
        self.false_positive = False

        self.notifier = self.get_app("Notifier")

        self.listen_state_handle_list.append(
            self.listen_state(self.zone_state_change, self.device, attribute="all")
        )

    def zone_state_change(self, entity, attributes, old, new, kwargs):
        """Check if user entered or left a zone."""
        if self.get_state(self.app_switch) == "on":
            if new is not None:
                last_changed = self.convert_utc(new["last_changed"])
                if old is not None:
                    old_state = old["state"]
                self.log(
                    "Zone of {} changed from {} to {}.".format(
                        self.friendly_name(entity), old_state, new["state"]
                    ),
                )
                if (
                    new["state"] == self.zone
                    and old_state != self.zone
                    and self.false_positive is False
                ):
                    self.log("Setting user_entered_zone to {}".format(last_changed))
                    self.user_entered_zone = last_changed
                if old_state == self.zone and new["state"] != self.zone:
                    if self.user_entered_zone is None or (
                        last_changed - self.user_entered_zone
                        >= datetime.timedelta(seconds=self.lingering_time)
                    ):
                        self.log(
                            "Zone of {} changed from {} to {}. Wait {} seconds until notification.".format(
                                self.friendly_name(entity),
                                old_state,
                                new["state"],
                                self.delay,
                            )
                        )
                        self.timer_handle_list.append(
                            self.run_in(self.notify_user, self.delay, old_zone=old)
                        )
                        self.false_positive = True
                        self.log("Setting false_positive to {}".format(self.false_positive))

    def notify_user(self, kwargs):
        """
        Notify about a user.

        Args:
            self: (todo): write your description
        """
        # Check if user did not come back to the zone in the meantime
        if self.get_state(self.device) != kwargs["old_zone"]:
            if self.travel_time_sensor is not None:
                self.log(
                    "Updating travel_time_sensor: {}".format(self.travel_time_sensor)
                )

                self.call_service(
                    "homeassistant/update_entity", entity_id=self.travel_time_sensor
                )

                self.timer_handle_list.append(self.run_in(self.notify_user_callback, 2))
            else:
                self.log("self.travel_time_sensor is not None")
                self.log("Notify user")
                self.notifier.notify(
                    self.notify_name,
                    self.message.format(
                        self.user_name, self.zone, divmod(self.delay, 60)[0]
                    ),
                )
                self.false_positive = False
                self.log("Setting false_positive to {}".format(self.false_positive))

    def notify_user_callback(self, kwargs):
        """
        Notify the user about the sensor.

        Args:
            self: (todo): write your description
        """
        self.log("Notify user")
        self.notifier.notify(
            self.notify_name,
            self.message.format(self.user_name, self.zone, divmod(self.delay, 60)[0])
            + self.travel_time_sensor_message.format(
                self.get_state(self.travel_time_sensor)
            ),
        )
        self.false_positive = False
        self.log("Setting false_positive to {}".format(self.false_positive))

    def terminate(self):
        """
        Terminate all the jobs.

        Args:
            self: (todo): write your description
        """
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)

        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)
