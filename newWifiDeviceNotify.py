import appdaemon.appapi as appapi

class DeviceNotify(appapi.AppDaemon):
  def initialize(self):
    self.listen_event(self.newDevice, "device_tracker")

  def newDevice(self, event_name, data, kwargs):
    if event_name == "device_tracker_new_device":
        message = "Unknown device connected: {}".format(data)
        self.call_service("notify/slack",message=message)
