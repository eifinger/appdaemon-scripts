import appdaemon.plugins.hass.hassapi as hass
from fritz_switch_profiles import FritzProfileSwitch

#
# App which sends a notification if a new device is found
#
# Args:
#
# notify_name: Who to notify. example: group_notifications
# user_id: Who to notify. example: -217831
# message: Message to use in notification. e.g. "Unknown device connected. Hostname: {}. MAC: {}"
# fritzbox_url (optional): The url of your fritzbox. example: http://fritz.box
# fritzbox_user (optional): The user to login to your fritzbox. example: ''
# fritzbox_password (optional): The password to login to your fritzbox. example: 'mysecurepassword'
# fritzbox_profile_name (optional): Name of the profile with Internet Access. example: 'Unbeschränkt'
# fritzbox_message_allow_access (optional): Message to use in telegram message. example: "Should I let the device access the Internet?"
# fritzbox_message_access_allowed (optional): Message to use in telegram message. example: "I have let the device access the internet. How kind of me!"
# fritzbox_message_access_blocked (optional): Message to use in telegram message. example: "I have saved the device from the dangers of the Internet"
#
# Release Notes
#
# Version 1.5.2:
#   Handle hostname is None
#
# Version 1.5.1:
#   Wait till entity is fully created
#
# Version 1.5:
#   Add support for Unifi > 0.98 and other integrations that are not using known_devices / device_tracker_new_device.
#   Fritzbox support is now optional
#
# Version 1.4:
#   Don't use Alexa for Notifications
#
# Version 1.3:
#   Fix for hostnames containing "-"
#
# Version 1.2:
#   Make us of fritz_switch_profiles to control Internet access
#
# Version 1.1:
#   use Notify App
#
# Version 1.0:
#   Initial Version

IDENTIFIER_DELIMITER = "-"
ALLOW_CALLBACK_IDENTIFIER = "/NEWDEVICENOTIFYALLOW"
BLOCK_CALLBACK_IDENTIFIER = "/NEWDEVICEBNOTIFYLOCK"


class DeviceNotify(hass.Hass):
    def initialize(self):
        """
        Initialize the device.

        Args:
            self: (todo): write your description
        """
        self.listen_event_handle_list = []

        self.notify_name = self.args["notify_name"]
        self.user_id = self.args["user_id"]
        self.message = self.args["message"]
        self.fritzbox_url = self.args.get("fritzbox_url")
        self.fritzbox_user = self.args.get("fritzbox_user")
        self.fritzbox_password = self.args.get("fritzbox_password")
        self.fritzbox_profile_name = self.args.get("fritzbox_profile_name")
        self.fritzbox_message_allow_access = self.args.get(
            "fritzbox_message_allow_access"
        )
        self.fritzbox_message_access_allowed = self.args.get(
            "fritzbox_message_access_allowed"
        )
        self.fritzbox_message_access_blocked = self.args.get(
            "fritzbox_message_access_blocked"
        )

        self.notifier = self.get_app("Notifier")

        self.listen_event_handle_list.append(
            self.listen_event(self.newDeviceCallback, "device_tracker_new_device")
        )
        self.listen_event_handle_list.append(
            self.listen_event(
                self.entityRegistryUpdatedCallback, "entity_registry_updated"
            )
        )
        self.listen_event_handle_list.append(
            self.listen_event(self.receiveTelegramCallback, "telegram_callback")
        )

    def entityRegistryUpdatedCallback(self, event_name, data, kwargs):
        """Callback method for entity_registry_updated event"""
        self.log("event_name: {}".format(event_name))
        self.log("data: {}".format(data))
        if data["action"] == "create":
            # Wait recursively until the entity was fully created
            self.run_in(
                self.handleNewRegistryEntity, 1, new_entity_id=data["entity_id"]
            )

    def handleNewRegistryEntity(self, kwargs):
        """Wait till Entity is available and notify if it was created by a router"""
        full_state = self.get_state(kwargs["new_entity_id"], attribute="all")
        if full_state is None:
            self.run_in(
                self.handleNewRegistryEntity, 1, new_entity_id=kwargs["new_entity_id"]
            )
        else:
            new_entity_attributes = full_state["attributes"]
            if new_entity_attributes.get("source_type") == "router":
                hostname = new_entity_attributes.get("hostname")
                mac = new_entity_attributes.get("mac")
                self.notifyNewDeviceAdded(hostname, mac)
                if self.fritzbox_url is not None and hostname is not None:
                    self.askForProfileChange(hostname)

    def newDeviceCallback(self, event_name, data, kwargs):
        """Callback method for device_tracker_new_device event"""
        self.log("event_name: {}".format(event_name))
        self.log("data: {}".format(data))
        self.notifyNewDeviceAdded(data["host_name"], data["mac"])
        if self.fritzbox_url is not None:
            self.askForProfileChange(data["host_name"])

    def notifyNewDeviceAdded(self, host_name, mac):
        """Send a notification message when a new device was added"""
        message = self.message.format(host_name, mac)
        self.notifier.notify(self.notify_name, message, useAlexa=False)

    def askForProfileChange(self, host_name):
        """Asks the user if he wants to allow the new device to have internet access"""
        self.log("Asking for profile change")
        if host_name is None:
            host_name = ""
        keyboard = [
            [
                (
                    "Zulassen",
                    ALLOW_CALLBACK_IDENTIFIER + IDENTIFIER_DELIMITER + host_name,
                )
            ],
            [("Sperren", BLOCK_CALLBACK_IDENTIFIER + IDENTIFIER_DELIMITER + host_name)],
        ]
        self.log("keyboard is: {}".format(keyboard), level="DEBUG")
        self.call_service(
            "telegram_bot/send_message",
            target=self.user_id,
            message=self.message_allow_access,
            inline_keyboard=keyboard,
        )

    def receiveTelegramCallback(self, event_name, data, kwargs):
        """Event listener for Telegram callback queries."""
        self.log("callback data: {}".format(data))
        data_callback = data["data"]
        callback_id = data["id"]
        chat_id = data["chat_id"]
        message_id = data["message"]["message_id"]
        text = data["message"]["text"]
        from_first = data["from_first"]

        if data_callback.startswith(ALLOW_CALLBACK_IDENTIFIER):
            host_name = data_callback.split(IDENTIFIER_DELIMITER, maxsplit=1)[1]
            self.log(
                "Received Telegram Callback to allow internet access for: {}".format(
                    host_name
                )
            )
            self.call_service(
                "telegram_bot/answer_callback_query",
                message="Dankeschön!",
                callback_query_id=callback_id,
            )
            self.call_service(
                "telegram_bot/edit_message",
                chat_id=chat_id,
                message_id=message_id,
                message=self.message_access_allowed,
                inline_keyboard=[],
            )
            self.allowDevice(host_name)
        elif data_callback.startswith(BLOCK_CALLBACK_IDENTIFIER):
            host_name = data_callback.split(IDENTIFIER_DELIMITER, maxsplit=1)[1]
            self.log(
                "Received Telegram Callback to block internet access for: {}".format(
                    host_name
                )
            )
            self.call_service(
                "telegram_bot/answer_callback_query",
                message="Dankeschön!",
                callback_query_id=callback_id,
            )
            self.call_service(
                "telegram_bot/edit_message",
                chat_id=chat_id,
                message_id=message_id,
                message=self.message_access_blocked,
                inline_keyboard=[],
            )

    def allowDevice(self, host_name):
        """Login to fritzbox and assign the 'Internet Access' profile to the device with the given host name"""
        fps = FritzProfileSwitch(
            self.fritzbox_url, self.fritzbox_user, self.fritzbox_password
        )
        devices = fps.get_devices()
        profiles = fps.get_profiles()

        # Get the device_id for the host name
        device_id = None
        for device in devices:
            if device["name"] == host_name:
                device_id = device["id1"]

        if device_id:
            # Get the profile id for the Internet access profile
            profile_id = None
            for profile in profiles:
                if profile["name"] == self.fritzbox_profile_name:
                    profile_id = profile["id"]

            if profile_id:
                # construct the array to set the profile for the device
                profile_for_device = [(device_id, profile_id)]
                # set device profile
                fps.set_profiles(profile_for_device)
            else:
                message = "Could not find profile with the name: {}".format(
                    self.fritzbox_profile_name
                )
                self.log(message)
                self.notifier.notify(self.notify_name, message)
        else:
            message = "Could not find device with the hostname: {}".format(host_name)
            self.log(message)
            self.notifier.notify(self.notify_name, message)

    def terminate(self):
        """
        Terminate all registered listeners.

        Args:
            self: (todo): write your description
        """
        for listen_event_handle in self.listen_event_handle_list:
            self.cancel_listen_event(listen_event_handle)
