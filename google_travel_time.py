import appdaemon.plugins.hass.hassapi as hass
import googlemaps
import datetime
import secrets
import messages

#
# App which calculates travel time between two locations and if wanted notifies the user if the travel time is within a normal amount
#
#
# Args:
#
# entities: Entity state to update
# notify_input_boolean: input_boolean determining whether to notify
# entity.from : Location from where to drive
# entity.to : Location to drive to
# example:
# entities:
#  input_number.travel_from_home_to_work:
#    notify_input_boolean: input_boolean.travel_from_home_to_work
#    from: Mainz
#    to: Wiesbaden
#
# Release Notes
#
# Version 1.1:
#   Add notification feature
#
# Version 1.0:
#   Initial Version

class GoogleTravelTime(hass.Hass):

    def initialize(self):
        self.gmaps = googlemaps.googlemaps.Client(secrets.GOOGLE_MAPS_API_TOKEN)
    
        self.max_api_calls = 2500
        self.delay = int(round(3600 * 24 / self.max_api_calls * 2))
        self.log("Delay is: {}".format(self.delay))
        if "entities" in self.args:
            self.delay = int(round(self.delay * len(self.args["entities"])))
            self.log("Found {} entities to update. Setting delay to {}".format(str(len(self.args["entities"])), str(self.delay)))
        else:
            self.log("No entities defined", level = "ERROR")
        self.timer_handle = self.run_in(self.calculate_travel_times, self.delay)            

    
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
                #Notify component
                if roundedTravelTime <= travelTime["duration"]["value"] * 1.2 and self.get_state(self.args["entities"][entity]["notify_input_boolean"]) == "on":
                    message = messages.journey_start().format(_to)
                    self.log("Notify user")
                    self.call_service("notify/slack",message=message)
                    self.turn_off(self.args["entities"][entity]["notify_input_boolean"])
        else:
            self.log("No entities defined", level = "ERROR")
        self.run_in(self.calculate_travel_times, self.delay) 

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

    def terminate(self):
        self.cancel_timer(self.timer_handle)