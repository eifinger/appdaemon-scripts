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
        return "@here Alarm: {}"
    if language == "en":
        return "@here Alarm: {}"
    return "@here Alarm: {}"

def welcome_home():
    if language == "de":
        return "Willkommen zu Hause {}."
    if language == "en":
        return "Welcome Home {}."
    return "Welcome Home {}."

def forgot_window_open():
    if language == "de":
        return "@here Du hast {} offen gelassen Dummie."
    if language == "en":
        return "@here You left open {} Dummy."
    return "@here You left open {} Dummy."

def forgot_light_on():
    if language == "de":
        return "Du hast {} angelassen. Ich habe es für dich ausgemacht."
    if language == "en":
        return "You left on {}. I turned it off for you"
    return "You left on {}. I turned it off for you"
    
    
    