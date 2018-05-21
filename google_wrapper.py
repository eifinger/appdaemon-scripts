import googlemaps
from datetime import datetime

class GoogleWrapper:

    def __init__(self, key):
        self.gmaps = googlemaps.Client(key)

    def get_distance_matrix(self, origin, destination):
        now = datetime.now()
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

    def get_geocode_for_location(self, location_name):
        result = self.gmaps.geocode(location_name)
        locations = []
        if len(result) > 0:
            for place in result:
                location = {}
                location["address"] = place["formatted_address"]
                location["geocode"] = place["geometry"]["location"]
                locations.append(location)
            return locations
        else:
            result = self.gmaps.places(location_name)
            if len(result["results"]) > 0:
                for place in result["results"]:
                    location = {}
                    location["address"] = place["formatted_address"]
                    location["geocode"] = place["geometry"]["location"]
                    locations.append(location)
                return locations
            else:
                return None