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
        return "@here Unbekanntes Gerät entdeckt: {}"
    if language == "en":
        return "@here Unknown device connected: {}"
    return "@here Unknown device connected: {}"

def device_change_alert():
    if language == "de":
        return "@here Alarm: {} ist gewechselt auf {}"
    if language == "en":
        return "@here Alarm: {} changed to {}"
    return "@here Alarm: {} changed to {}"

def failed_login_detected():
    if language == "de":
        return "@here Alarm: Fehlgeschlagener Login festgestellt."
    if language == "en":
        return "@here Alarm: Failed login detected."
    return "@here Alarm: Failed login detected."

def welcome_home():
    if language == "de":
        return "Willkommen zu Hause {}."
    if language == "en":
        return "Welcome Home {}."
    return "Welcome Home {}."

    
    
    