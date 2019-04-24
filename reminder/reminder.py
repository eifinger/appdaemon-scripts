import appdaemon.plugins.hass.hassapi as hass
import globals
import datetime
import uuid
#
# App which reminds you daily and again in the evening if not acknowledged
#
#
# Args:
#
# app_switch: on/off switch for this app. example: input_boolean.turn_fan_on_when_hot
# notify_name: Who to notify. example: group_notifications
# user_id: The user_id of the telegram user to ask whether he knows an unknown face. example: 812391
# reminder_acknowledged_entity: Input Boolean to store the information whether the user acknowledged the notification.
#                        This prevents new notifications upon HA/Appdaemon restart.
#                        example: input_boolean.persistence_plantwateringnotifier_reminder_acknowledged
# message: localized message to use in notification
#
# Release Notes
#
# Version 1.0:
#   Initial Version

KEYBOARD_CALLBACK_BASE = "/reminder_acknowledged"

class Reminder(hass.Hass):

    def initialize(self):
    
        self.timer_handle_list = []
        self.listen_event_handle_list = []
        self.listen_state_handle_list = []

        self.app_switch = globals.get_arg(self.args, "app_switch")
        self.notify_name = globals.get_arg(self.args, "notify_name")
        self.user_id = globals.get_arg(self.args, "user_id")
        self.reminder_acknowledged_entity = globals.get_arg(self.args, "reminder_acknowledged_entity")
        self.message = globals.get_arg(self.args, "message")
        self.message_evening = globals.get_arg(self.args, "message_evening")

        self.keyboard_callback = KEYBOARD_CALLBACK_BASE + uuid.uuid4().hex  # Unique callback for each instance

        self.notifier = self.get_app('Notifier')

        self.reminder_acknowledged = self.get_state(self.reminder_acknowledged_entity)

        self.listen_event_handle_list.append(self.listen_event(self.receive_telegram_callback, 'telegram_callback'))

        # Remind daily at 08:00
        self.timer_handle_list.append(self.run_daily(self.run_morning_callback, datetime.time(8, 0, 0)))
        # Remind daily at 18:00
        self.timer_handle_list.append(self.run_daily(self.run_evening_callback, datetime.time(18, 0, 0)))

    def run_morning_callback(self, kwargs):
        """Remind the user of {self.message}"""
        if self.get_state(self.app_switch) == "on":

            self.turn_off(self.reminder_acknowledged_entity)
            self.log("Setting reminder_acknowledged to: off")
            self.log("Reminding user")
            keyboard = [[("Hab ich gemacht", self.keyboard_callback)]]
            self.call_service('telegram_bot/send_message',
                      target=self.user_id,
                      message=self.message,
                      inline_keyboard=keyboard)

    def run_evening_callback(self, kwargs):
        """Remind the user again if he didn't acknowledge it"""
        if self.get_state(self.app_switch) == "on":
            if self.get_state(self.reminder_acknowledged_entity) == "off":
                self.log("Reminding user")
                self.call_service("notify/" + self.notify_name, message=self.message_evening)

    def receive_telegram_callback(self, event_name, data, kwargs):
        """Event listener for Telegram callback queries."""
        assert event_name == 'telegram_callback'
        data_callback = data['data']
        callback_id = data['id']
        chat_id = data['chat_id']
        message_id = data["message"]["message_id"]
        text = data["message"]["text"]
        self.log(f"callback data: {data}", level="DEBUG")

        if data_callback == self.keyboard_callback:  # Keyboard editor:
            # Answer callback query
            self.call_service('telegram_bot/answer_callback_query',
                              message="Super!",
                              callback_query_id=callback_id)
            self.turn_on(self.reminder_acknowledged_entity)
            self.log("Setting reminder_acknowledged to: on")

            self.call_service('telegram_bot/edit_message',
                              chat_id=chat_id,
                              message_id=message_id,
                              message=text + f" Hast du um {datetime.datetime.now().hour}:{datetime.datetime.now().minute} erledigt.",
                              inline_keyboard=[])

    def terminate(self):
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)

        for listen_event_handle in self.listen_event_handle_list:
            self.cancel_listen_event(listen_event_handle)

        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)