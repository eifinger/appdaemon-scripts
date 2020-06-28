import appdaemon.plugins.hass.hassapi as hass
import datetime

#
# App which reminds you daily to water your plants if it won't rain
#
#
# Args:
#
# app_switch: on/off switch for this app. example: input_boolean.turn_fan_on_when_hot
# rain_precip_sensor: sensor which shows rain probability. example: sensor.dark_sky_precip_probability
# rain_precip_intensity_sensor: sensor which shows rain probability. example: sensor.dark_sky_precip_intensity
# precip_type_sensor: sensor which shows precip type. example: sensor.dark_sky_precip
# notify_name: Who to notify. example: group_notifications
# user_id: The user_id of the telegram user to ask whether he knows an unknown face. example: 812391
# reminder_acknowledged_entity: Input Boolean to store the information whether the user acknowledged the notification.
#                        This prevents new notifications upon HA/Appdaemon restart.
#                        example: input_boolean.persistence_plantwateringnotifier_reminder_acknowledged
# message: localized message to use in notification
#
# Release Notes
#
# Version 1.5.1:
#   Use consistent message variable
#
# Version 1.5:
#   use Notify App
#
# Version 1.4:
#   message now directly in own yaml instead of message module
#
# Version 1.3:
#   Added app_switch
#
# Version 1.2:
#   Update original message with information when the reminder was acknowledged
#
# Version 1.1:
#   Store reminder acknowledged in an input_boolean to prevent notifications after HA/Appdaemon restarts
#
# Version 1.0:
#   Initial Version


class PlantWateringNotifier(hass.Hass):
    def initialize(self):

        self.timer_handle_list = []
        self.listen_event_handle_list = []
        self.listen_state_handle_list = []

        self.app_switch = self.args["app_switch"]
        self.rain_precip_sensor = self.args["rain_precip_sensor"]
        self.rain_precip_intensity_sensor = self.args["rain_precip_intensity_sensor"]
        self.precip_type_sensor = self.args["precip_type_sensor"]
        self.notify_name = self.args["notify_name"]
        self.user_id = self.args["user_id"]
        self.reminder_acknowledged_entity = self.args["reminder_acknowledged_entity"]
        self.message = self.args["message"]
        self.message_not_needed = self.args["message_not_needed"]
        self.message_evening = self.args["message_evening"]

        self.intensity_minimum = 2  # mm/h
        self.propability_minimum = 90  # %

        self.keyboard_callback = "/plants_watered"

        self.notifier = self.get_app("Notifier")

        self.reminder_acknowledged = self.get_state(self.reminder_acknowledged_entity)

        self.listen_event_handle_list.append(
            self.listen_event(self.receive_telegram_callback, "telegram_callback")
        )

        # Remind daily at 08:00
        self.timer_handle_list.append(
            self.run_daily(self.run_morning_callback, datetime.time(8, 0, 0))
        )
        # Remind daily at 18:00
        self.timer_handle_list.append(
            self.run_daily(self.run_evening_callback, datetime.time(18, 0, 0))
        )

    def run_morning_callback(self, kwargs):
        """Check if it will rain and if not remind the user to water the plants"""
        if self.get_state(self.app_switch) == "on":
            precip_propability = self.get_state(self.rain_precip_sensor)
            self.log("Rain Propability: {}".format(float(precip_propability)))
            precip_intensity = self.get_state(self.rain_precip_intensity_sensor)
            self.log("Rain Intensity: {}".format(float(precip_intensity)))
            precip_type = self.get_state(self.precip_type_sensor)
            self.log("Precip Type: {}".format(precip_type))

            if (
                precip_propability != None
                and precip_propability != ""
                and float(precip_propability) < self.propability_minimum
                and precip_intensity != None
                and precip_intensity != ""
                and float(precip_intensity) < self.intensity_minimum
            ):
                self.turn_off(self.reminder_acknowledged_entity)
                self.log("Setting reminder_acknowledged to: {}".format("off"))
                self.log("Reminding user")
                keyboard = [[("Hab ich gemacht", self.keyboard_callback)]]
                self.call_service(
                    "telegram_bot/send_message",
                    target=self.user_id,
                    message=self.message.format(precip_propability),
                    inline_keyboard=keyboard,
                )

            else:
                self.turn_on(self.reminder_acknowledged_entity)
                self.log("Setting reminder_acknowledged to: {}".format("off"))
                self.log("Notifying user")
                self.notifier.notify(
                    self.notify_name,
                    self.message_not_needed.format(
                        precip_propability, precip_intensity
                    ),
                )

    def run_evening_callback(self, kwargs):
        """Remind user to water the plants he if didn't acknowledge it"""
        if self.get_state(self.app_switch) == "on":
            if self.get_state(self.reminder_acknowledged_entity) == "off":
                self.log("Reminding user")
                self.call_service(
                    "notify/" + self.notify_name, message=self.message_evening
                )

    def receive_telegram_callback(self, event_name, data, kwargs):
        """Event listener for Telegram callback queries."""
        assert event_name == "telegram_callback"
        data_callback = data["data"]
        callback_id = data["id"]
        chat_id = data["chat_id"]
        message_id = data["message"]["message_id"]
        text = data["message"]["text"]
        self.log("callback data: {}".format(data), level="DEBUG")

        if data_callback == self.keyboard_callback:  # Keyboard editor:
            # Answer callback query
            self.call_service(
                "telegram_bot/answer_callback_query",
                message="Super!",
                callback_query_id=callback_id,
            )
            self.turn_on(self.reminder_acknowledged_entity)
            self.log("Setting reminder_acknowledged to: {}".format("on"))

            self.call_service(
                "telegram_bot/edit_message",
                chat_id=chat_id,
                message_id=message_id,
                message=text
                + " Hast du um {}:{} erledigt.".format(
                    datetime.datetime.now().hour, datetime.datetime.now().minute
                ),
                inline_keyboard=[],
            )

    def terminate(self):
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)

        for listen_event_handle in self.listen_event_handle_list:
            self.cancel_listen_event(listen_event_handle)

        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
