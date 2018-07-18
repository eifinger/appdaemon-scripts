language = "de"

def journey_start():
    if language == "de":
        return "Du kannst losfahren nach {}"
    if language == "en":
        return "You can start your journey to {}"
    return "You can start your journey to {}"

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

def failed_login_detected():
    if language == "de":
        return "Alarm: {}"
    if language == "en":
        return "Alarm: {}"
    return "Alarm: {}"

def welcome_home():
    if language == "de":
        return "Willkommen zu Hause {}."
    if language == "en":
        return "Welcome Home {}."
    return "Welcome Home {}."

def forgot_window_open():
    if language == "de":
        return "Du hast {} offen gelassen Dummie."
    if language == "en":
        return "You left open {} Dummy."
    return "You left open {} Dummy."

def forgot_light_on():
    if language == "de":
        return "Du hast {} angelassen. Ich habe es für dich ausgemacht."
    if language == "en":
        return "You left on {}. I turned it off for you"
    return "You left on {}. I turned it off for you"

def user_is_leaving_zone():
    if language == "de":
        return "{} ist gerade von {} weg."
    if language == "en":
        return "{} just left {}"
    return "{} just left {}" 

def user_is_heading_to_zone():
    if language == "de":
        return "{} ist auf dem Weg nach {}."
    if language == "en":
        return "{} is on his way to {}"
    return "{} is on his way to {}" 

def user_is_still_heading_to_zone():
    if language == "de":
        return "{} ist auf immer noch dem Weg nach {}."
    if language == "en":
        return "{} is still on his way to {}"
    return "{} is still on his way to {}" 

def time_to_leave():
    if language == "de":
        return "Es ist Zeit loszufahren nach {}. Du brauchst {} Minuten. Hier ist ein Google Maps Link: {}"
    if language == "en":
        return "It's time to leave to {}. It will take {} minutes. Here is a Google Maps Link: {}"
    return "It's time to leave to {}. It will take {} minutes. Here is a Google Maps Link: {}"

def identified_face():
    if language == "de":
        return "Ich habe {} erkannt"
    if language == "en":
        return "I have recognized {}."
    return "I have recognized {}."

def unknown_face_detected():
    if language == "de":
        return "Ich habe dieses Gesicht nicht erkannt. Kennst du es?"
    if language == "en":
        return "I have not recognized this face. Do you know it?"
    return "I have not recognized this face. Do you know it?"

def noface_detected():
    if language == "de":
        return "Ich konnte kein Gesicht finden"
    if language == "en":
        return "I could not detect a face"
    return "I could not detect a face"

def facebox_not_responding():
    if language == "de":
        return "Facebox antwortet nicht. Hier ist das Bild"
    if language == "en":
        return "Facebox is not responding. Here is the photo"
    return "Facebox is not responding. Here is the photo"

def plants_watering_reminder():
    if language == "de":
        return "Die Regenwahrscheinlichkeit beträgt heute nur {}. Vergiss nicht die Pflanzen zu gießen!"
    if language == "en":
        return "The Rain Propability is only {}. Don't forget to water the plants!"
    return "The Rain Propability is only {}. Don't forget to water the plants!"

def plants_watering_not_needed():
    if language == "de":
        return "Es wird heute mit einer Wahrscheinlichkeit von {} Prozent ungefähr {} Millimeter pro Stunde regnen. Du brauchst nicht selbst gießen."
    if language == "en":
        return "It will rain today {} millimeter per hour with a propability of {}. You don't have to water your plants"
    return "It will rain today {} millimeter per hour with a propability of {}. You don't have to water your plants"

def plants_watering_reminder_evening():
    if language == "de":
        return "Ich bin mir nicht sicher ob du vergessen hast die Pflanzen zu gießen, deswegen erinnere ich dich lieber noch einmal daran."
    if language == "en":
        return "I'm not sure whether you waterd your plants, so I thought I better remind you again"
    return "I'm not sure whether you waterd your plants, so I thought I better remind you again"

def power_usage_on():
    if language == "de":
        return "{} ist gestartet."
    if language == "en":
        return "{} just started."
    return "{} just started."

def power_usage_off():
    if language == "de":
        return "{} ist fertig."
    if language == "en":
        return "{} just finished."
    return "{} just finished."
    
    
    
    