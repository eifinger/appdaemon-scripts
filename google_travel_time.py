import appdaemon.plugins.hass.hassapi as hass
import google_wrapper
import secrets

#
# App to turn something on when motion detected then off again after a delay if no more motion was detected
#
#
# Args:
#
# entities: Entity state to update
# entity.from : Location from where to drive
# entity.to : Location to drive to
# example:
# entities:
#  input_number.travel_from_home_to_work:
#    from: Mainz
#    to: Wiesbaden
#
# Release Notes
#
# Version 1.1:
#   Add ability for other apps to cancel the timer
#
# Version 1.0:
#   Initial Version

class GoogleTravelTime(hass.Hass):

    def initialize(self):

        self.gmaps = google_wrapper.GoogleWrapper(key = secrets.GOOGLE_MAPS_API_TOKEN)
    
        self.handle = None
        self.max_api_calls = 2500
        self.delay = int(round(3600 * 24 / self.max_api_calls * 1,1))
        self.log("Delay is: {}".format(self.delay))

        self.calculate_travel_times()
        self.run_in(self.calculate_travel_times, self.delay)            

    
    def calculate_travel_times(self, *kwargs):
        if "entities" in self.args:
            self.delay = int(round(self.delay * len(self.args["entities"])))
            self.log("Found {} entities to update. Setting delay to {}".format(str(len(self.args["entities"])), str(self.delay)))
            for entity in self.args["entities"]:
                self.log("entitiy: {}".format(entity))
                travelTime = int(round(self.gmaps.get_distance_matrix(entity["from"], entity["to"])["duration_in_traffic"]["value"] / 60))
                self.log("Updating {} to {} minutes".format(entity, str(travelTime)))
                self.set_state(entity, travelTime)
        else:
            self.log("No entities defined", level = "ERROR")