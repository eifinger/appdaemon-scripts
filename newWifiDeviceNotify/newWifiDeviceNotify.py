import appdaemon.plugins.hass.hassapi as hass
import globals
#
# App which sends a notification if a new device is found
#
# Args:
#
# notify_name: Who to notify. example: group_notifications
# message_<LANG>: localized message to use in notification. e.g. "You left open {} Dummy."
#
# Release Notes
#
# Version 1.1:
#   use Notify App
#
# Version 1.0:
#   Initial Version

class DeviceNotify(hass.Hass):

  def initialize(self):
    self.listen_event_handle_list = []

    self.notify_name = globals.get_arg(self.args,"notify_name")
    self.message = globals.get_arg(self.args,"message_DE")

    self.notifier = self.get_app('Notifier')

    self.listen_event_handle_list.append(self.listen_event(self.newDevice, "device_tracker_new_device"))

  def newDevice(self, event_name, data, kwargs):
    self.log("event_name: {}".format(event_name))
    self.log("data: {}".format(data))
    message = self.message.format(data["host_name"],data["mac"])
    self.notifier.notify(self.notify_name, message)

  def terminate(self):
    for listen_event_handle in self.listen_event_handle_list:
      self.cancel_listen_event(listen_event_handle)
