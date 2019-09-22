import appdaemon.plugins.hass.hassapi as hass
import datetime
import globals

#
# App which notifies the user if the travel time is within a normal amount
#
#
# Args:
# sensor: google_travel_time or here_travel_time sensor to watch. example: sensor.travel_time_home_from_work
# notify_input_boolean: input_boolean determining whether to notify. example: input_boolean.travel_time_home_from_work
# notify_name: Who to notify. example: group_notifications
# acceptable_range (optional): Multiplier of the normal travel time that is still acceptable. example: 1.2
# message_<LANG>: message to use in notification
# notify_use_Alexa: use Alexa as TTS. Defaults to True. example: False
#
# Release Notes
#
# Version 1.6:
#   Introduce methods to deal with minor differences between google and here
#
# Version 1.5:
#   Rename to TravelTimeNotifier as this can be used with here_travel_time also
#
# Version 1.4:
#   use Notify App
#
# Version 1.3:
#   message now directly in own yaml instead of message module
#
# Version 1.2:
#   Moved to standard google travel sensors. Now only notification
#
# Version 1.1:
#   Add notification feature
#
# Version 1.0:
#   Initial Version


class TravelTimeNotifier(hass.Hass):
    def initialize(self):

        self.listen_state_handle_list = []
        self.timer_handle_list = []

        self.sensor = globals.get_arg(self.args, "sensor")
        self.notify_input_boolean = globals.get_arg(self.args, "notify_input_boolean")
        self.notify_name = globals.get_arg(self.args, "notify_name")
        self.message = globals.get_arg(self.args, "message")
        try:
            self.acceptable_range = globals.get_arg(self.args, "acceptable_range")
        except KeyError:
            self.acceptable_range = 1.2
        try:
            self.notify_use_Alexa = globals.get_arg(self.args, "notify_use_Alexa")
        except KeyError:
            self.notify_use_Alexa = True

        self.notifier = self.get_app("Notifier")

        self.listen_state_handle_list.append(
            self.listen_state(self.state_change, self.sensor, attribute="all")
        )

    def state_change(self, entity, attributes, old, new, kwargs) -> None:
        self.log("entity: {}".format(entity), level="DEBUG")
        self.log("old: {}".format(old), level="DEBUG")
        self.log("new: {}".format(new), level="DEBUG")

        duration_in_traffic_minutes = self.parse_duration_in_traffic_minutes(new)
        self.log(
            "duration_in_traffic_minutes: {}".format(duration_in_traffic_minutes),
            level="DEBUG",
        )

        duration_minutes = self.parse_duration_minutes(new)
        self.log("duration_minutes: {}".format(duration_minutes), level="DEBUG")

        if duration_in_traffic_minutes <= duration_minutes * self.acceptable_range:
            if self.get_state(self.notify_input_boolean) == "on":
                destination_address = self.parse_destination_address(new)
                self.notify_user(destination_address)
                self.turn_off(self.notify_input_boolean)

    def notify_user(self, address: str) -> None:
        """Notify the user it is time to leave for the given address."""
        message = self.message.format(address)
        self.log("Notify user")
        self.notifier.notify(self.notify_name, message, useAlexa=self.notify_use_Alexa)

    def parse_duration_in_traffic_minutes(self, state) -> Optional[int]:
        """Get duration_in_traffic from the states attributes."""
        duration_in_traffic = state["attributes"].get("duration_in_traffic")
        duration_in_traffic_minutes = None
        if duration_in_traffic is not None:
            if isinstance(duration_in_traffic, float):
                duration_in_traffic_minutes = int(duration_in_traffic)
            else:
                duration_in_traffic_minutes = int(
                    duration_in_traffic[: duration_in_traffic.find(" ")]
                )
        else:
            self.log(
                "Could not find duration_in_traffic in state attributes.",
                level="WARNING",
            )
        return duration_in_traffic_minutes

    def parse_destination_address(self, state) -> Optional[str]:
        """Get a destination address from the states attributes."""
        attributes = state["attributes"]
        destination_address = None
        if "destination_name" in attributes:
            destination_address = attributes["destination_name"]
        elif "destination_addresses" in attributes:
            destination_address = attributes["destination_addresses"][0]
        else:
            self.log(
                "Could not find destination_name or destination_addresses in state attributes.",
                level="WARNING",
            )
        return destination_address

    def parse_duration_minutes(self, state) -> Optional[int]:
        """Get duration from the states attributes."""
        duration_minutes = None
        duration = state["attributes"].get("duration")
        if duration is not None:
            if isinstance(duration, float):
                duration_minutes = int(duration)
            else:
                duration_minutes = int(duration[: duration.find(" ")])
        else:
            self.log("Could not find duration in state attributes.", level="WARNING")
        return duration_minutes

    def terminate(self) -> None:
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
