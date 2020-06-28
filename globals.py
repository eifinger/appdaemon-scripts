import random


def random_arg(argList):
    ############################################
    # pick a random text from a list
    ############################################
    if isinstance(argList, list):
        text = random.choice(argList)
    else:
        text = argList
    return text
