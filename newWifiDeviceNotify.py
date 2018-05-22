import appdaemon.appapi as appapi
import messages

class DeviceNotify(appapi.AppDaemon):
  def initialize(self):
    self.listen_event(self.newDevice, "device_tracker")

  def newDevice(self, event_name, data, kwargs):
    if event_name == "device_tracker_new_device":
        message = messages.unknown_device_connected().format(data)
        self.call_service("notify/slack",message=message)
