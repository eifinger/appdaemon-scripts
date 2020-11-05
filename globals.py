import random


def random_arg(argList):
    """
    Return an argparse argument.

    Args:
        argList: (list): write your description
    """
    ############################################
    # pick a random text from a list
    ############################################
    if isinstance(argList, list):
        text = random.choice(argList)
    else:
        text = argList
    return text
