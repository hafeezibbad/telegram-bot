"""
Module containing helper functions to be used in the application.
"""
import string
import random
import CONSTANTS


def generate_secret_key(length=32):
    """
    Generates a secret key consisting of ascii characters, special characters
    and digits.
    e.g. IG0Z[00;QEq;Iy.sZp8>16dv)reQ(R8z
    :param: length of key (default=32)
    """
    return ''.join(random.choice(string.ascii_letters +
                                 string.digits +
                                 '!@#$%^&*().,;:[]{}<>?')
                   for _ in range(length))


def load_live_bots():
    """
    This function adds the set of live bots whose tokens are given in
    CONSTANTS file.
    :return:
    """
    from botapp.api_helpers import procedures
    total = 0
    started = 0
    for key in CONSTANTS.LIVE_BOTS.keys():
        try:
            status = procedures.add_bot(CONSTANTS.LIVE_BOTS.get(key),
                                        testing=False)
            total += 1
            started += 1 if status[1] else 0
        except:
            pass

    print '%d live bots added. %d bots started polling.' % (total, started)
