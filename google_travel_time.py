import appdaemon.plugins.hass.hassapi as hass
import googlemaps
import datetime
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
        self.gmaps = googlemaps.googlemaps.Client(secrets.GOOGLE_MAPS_API_TOKEN)
    
        self.handle = None
        self.max_api_calls = 2500
        self.delay = int(round(3600 * 24 / self.max_api_calls * 2))
        self.log("Delay is: {}".format(self.delay))
        if "entities" in self.args:
            self.delay = int(round(self.delay * len(self.args["entities"])))
            self.log("Found {} entities to update. Setting delay to {}".format(str(len(self.args["entities"])), str(self.delay)))
        else:
            self.log("No entities defined", level = "ERROR")

        self.calculate_travel_times()
        self.run_in(self.calculate_travel_times, self.delay)            

    
    def calculate_travel_times(self, *kwargs):
        if "entities" in self.args:
            for entity in self.args["entities"]:
                _from = self.args["entities"][entity]["from"]
                if _from.startswith("secret_"):
                    _from = self.get_secret(_from)
                _to = self.args["entities"][entity]["to"]
                if _to.startswith("secret_"):
                    _to = self.get_secret(_to)
                travelTime = self.get_distance_matrix(_from, _to)
                roundedTravelTime = int(round(travelTime["duration_in_traffic"]["value"] / 60))
                self.log("Updating {} to {} minutes".format(entity, str(roundedTravelTime)))
                self.set_state(entity, state = roundedTravelTime)
        else:
            self.log("No entities defined", level = "ERROR")

    def get_distance_matrix(self, origin, destination):
        now = datetime.datetime.now()
        matrix = self.gmaps.distance_matrix(origin,
                                            destination,
                                            mode="driving",
                                            departure_time=now,
                                            language="de",
                                            traffic_model = "best_guess")
        distance = matrix['rows'][0]['elements'][0]['distance']
        duration = matrix['rows'][0]['elements'][0]['duration']
        duration_in_traffic = matrix['rows'][0]['elements'][0]['duration_in_traffic']
        return {"distance": distance, "duration": duration, "duration_in_traffic": duration_in_traffic}

    def get_secret(self, key):
        if key in secrets.secret_dict:
            return secrets.secret_dict[key]
        else:
            self.log("Could not find {} in secret_dict".format(key))