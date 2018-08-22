import appdaemon.plugins.hass.hassapi as hass
import globals
#
# App which sets media player source on based on a entity state
#
# Args:
#
# app_switch: on/off switch for this app. example: input_boolean.turn_fan_on_when_hot
# trigger_entity: entity which triggers this app. example: input_boolean.is_home
# trigger_state: new state of trigger_entity which triggers this app. example: "off"
# after_sundown (optional): Only trigger after sundown. example: True
# media_player: Which media player to control. example: media_player.spotify
# source: Which source to set the media player to: Wohnung
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class SetMediaPlayerSource(hass.Hass):

  def initialize(self):
    self.listen_state_handle_list = []

    self.app_switch = globals.get_arg(self.args,"app_switch")
    try:
      self.after_sundown = globals.get_arg(self.args,"after_sundown")
    except KeyError:
            self.after_sundown = None
    self.trigger_entity = globals.get_arg(self.args,"trigger_entity")
    self.trigger_state = globals.get_arg(self.args,"trigger_state")
    self.media_player = globals.get_arg(self.args,"media_player")
    self.source = globals.get_arg(self.args,"source")

    self.SELECT_SOURCE_SERVICE = "media_player.select_source"
    
    self.listen_state_handle_list.append(self.listen_state(self.state_change, self.trigger_entity))
    
  def state_change(self, entity, attribute, old, new, kwargs):
    if self.get_state(self.app_switch) == "on":
      if new != "" and new == self.trigger_state:
        if self.after_sundown == None or ( ( self.after_sundown == True and self.sun_down() ) or self.after_sundown == False ):
          #entities_off
          self.log("Setting {} to {}".format(self.media_player, self.source))
          self.call_service(self.SELECT_SOURCE_SERVICE, entity_id=self.media_player, source=self.source)

  def terminate(self):
    for listen_state_handle in self.listen_state_handle_list:
      self.cancel_listen_state(listen_state_handle)
      
