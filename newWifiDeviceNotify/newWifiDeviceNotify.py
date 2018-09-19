import appdaemon.plugins.hass.hassapi as hass
from fritz_switch_profiles import FritzProfileSwitch
import globals

#
# App which sends a notification if a new device is found
#
# Args:
#
# notify_name: Who to notify. example: group_notifications
# user_id: Who to notify. example: -217831
# fritzbox_url: The url of your fritzbox. example: http://fritz.box
# fritzbox_user: The user to login to your fritzbox. example: ''
# fritzbox_password: The password to login to your fritzbox. example: 'mysecurepassword'
# fritzbox_profile_name: Name of the profile with Internet Access. example: 'Unbeschränkt'
# message_<LANG>: localized message to use in notification. e.g. "You left open {} Dummy."
# message_allow_access:
#
# Release Notes
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
    self.listen_event_handle_list = []

    self.notify_name = globals.get_arg(self.args,"notify_name")
    self.user_id = globals.get_arg(self.args,"user_id")
    self.message = globals.get_arg(self.args,"message")
    self.fritzbox_url = globals.get_arg(self.args,"fritzbox_url")
    self.fritzbox_user = globals.get_arg(self.args,"fritzbox_user")
    self.fritzbox_password = globals.get_arg(self.args,"fritzbox_password")
    self.fritzbox_profile_name = globals.get_arg(self.args, "fritzbox_profile_name")
    self.message_allow_access = globals.get_arg(self.args,"message_allow_access")
    self.message_access_allowed = globals.get_arg(self.args,"message_access_allowed")
    self.message_access_blocked = globals.get_arg(self.args,"message_access_blocked")

    self.notifier = self.get_app('Notifier')

    self.listen_event_handle_list.append(self.listen_event(self.newDevice, "device_tracker_new_device"))
    #subscribe to telegram events
    self.listen_event_handle_list.append(self.listen_event(self.receive_telegram_callback, 'telegram_callback'))

  def newDevice(self, event_name, data, kwargs):
    """Callback method for device_tracker_new_device event"""
    self.log("event_name: {}".format(event_name))
    self.log("data: {}".format(data))
    message = self.message.format(data["host_name"],data["mac"])
    self.notifier.notify(self.notify_name, message)
    self.askForProfileChange(data["host_name"])


  def askForProfileChange(self, host_name):
    """Asks the user if he wants to allow the new device to have internet access"""
    self.log("Asking for profile change")
    keyboard = [[("Zulassen",ALLOW_CALLBACK_IDENTIFIER + IDENTIFIER_DELIMITER + host_name)],[("Sperren",BLOCK_CALLBACK_IDENTIFIER + IDENTIFIER_DELIMITER + host_name)]]
    self.log("keyboard is: {}".format(keyboard), level="DEBUG")
    self.call_service('telegram_bot/send_message',
                      target=self.user_id,
                      message=self.message_allow_access,
                      inline_keyboard=keyboard)


  def receive_telegram_callback(self, event_name, data, kwargs):
    """Event listener for Telegram callback queries."""
    self.log("callback data: {}".format(data))
    data_callback = data['data']
    callback_id = data['id']
    chat_id = data['chat_id']
    message_id = data["message"]["message_id"]
    text = data["message"]["text"]
    from_first = data["from_first"]

    if data_callback.startswith(ALLOW_CALLBACK_IDENTIFIER):
        host_name = data_callback.split(IDENTIFIER_DELIMITER, maxsplit=1)[1]
        self.log("Received Telegram Callback to allow internet access for: {}".format(host_name))
        self.call_service('telegram_bot/answer_callback_query',
                      message="Dankeschön!",
                      callback_query_id=callback_id)
        self.call_service('telegram_bot/edit_message',
                      chat_id=chat_id,
                      message_id=message_id,
                      message=self.message_access_allowed,
                      inline_keyboard=[])
        self.allowDevice(host_name)
    elif data_callback.startswith(BLOCK_CALLBACK_IDENTIFIER):
        host_name = data_callback.split(IDENTIFIER_DELIMITER, maxsplit=1)[1]
        self.log("Received Telegram Callback to block internet access for: {}".format(host_name))
        self.call_service('telegram_bot/answer_callback_query',
                      message="Dankeschön!",
                      callback_query_id=callback_id)
        self.call_service('telegram_bot/edit_message',
                      chat_id=chat_id,
                      message_id=message_id,
                      message=self.message_access_blocked,
                      inline_keyboard=[])

  def allowDevice(self, host_name):
    """Login to fritzbox and assign the 'Internet Access' profile to the device with the given host name"""
    fps = FritzProfileSwitch(self.fritzbox_url, self.fritzbox_user, self.fritzbox_password)
    devices = fps.get_devices()
    profiles = fps.get_profiles()

    #Get the device_id for the host name
    device_id = None
    for device in devices:
      if device['name'] == host_name:
        device_id = device['id1']

    if device_id:
      #Get the profile id for the Internet access profile
      profile_id = None
      for profile in profiles:
        if profile['name'] == self.fritzbox_profile_name:
          profile_id = profile['id']
      
      if profile_id:
        #construct the array to set the profile for the device
        profile_for_device = [(device_id, profile_id)]
        #set device profile
        fps.set_profiles(profile_for_device)
      else:
        message = "Could not find profile with the name: {}".format(self.fritzbox_profile_name)
        self.log(message)
        self.notifier.notify(self.notify_name, message)
    else:
      message = "Could not find device with the hostname: {}".format(host_name)
      self.log(message)
      self.notifier.notify(self.notify_name, message)


    

  def terminate(self):
    for listen_event_handle in self.listen_event_handle_list:
      self.cancel_listen_event(listen_event_handle)
