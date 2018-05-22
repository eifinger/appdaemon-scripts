language = "de"

def journey_start():
    if language == "de":
        return "@here Du kannst losfahren nach {}"
    if language == "en":
        return "@here You can start your journey to {}"
    return "@here You can start your journey to {}"

def isHome_off():
    if language == "de":
        return "Es ist keiner mehr zu Hause. Setze isHome auf off"
    if language == "en":
        return "Everyone left home. Setting isHome to off"
    return "Everyone left home. Setting isHome to off"

def unknown_device_connected():
    if language == "de":
        return "Unbekanntes Gerät entdeckt: {}"
    if language == "en":
        return "Unknown device connected: {}"
    return "Unknown device connected: {}"

def device_change_alert():
    if language == "de":
        return "Alarm: {} ist gewechselt auf {}"
    if language == "en":
        return "Alarm: {} changed to {}"
    return "Alarm: {} changed to {}"

    
    
    