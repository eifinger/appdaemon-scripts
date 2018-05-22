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
    