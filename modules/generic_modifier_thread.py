import threading
import time
from datetime import datetime


class StartOverException(Exception):
    """Raise to restart the tails thread loop"""
    pass


class GenericModifierThread(threading.Thread):
    def __init__(self, bot_object, bot):
        threading.Thread.__init__(self)
        self.bot = bot
        self.bot_object = bot_object

    def run(self):
        while True:
            try:
                try:
                    time_to_wait, affected_person, earliest_effect_key = self._time_until_expiry()
                except (KeyError, TypeError, IndexError):
                    raise StartOverException
                time.sleep(1)
                for second in range(0, time_to_wait + 1):
                    time.sleep(1)
                    if second >= time_to_wait:
                        self.bot_object._clear_modifier_effect(affected_person, earliest_effect_key)
                        raise StartOverException
                raise StartOverException
            except StartOverException as ex:
                time.sleep(1)
                continue

    def _time_until_expiry(self):
        current_time = datetime.now()
        try:
            misc_effects = self.bot_object._Plugin__db_get(['misc_modifiers'])
            affected_person, earliest_effect_key = self._get_earliest_expiry()
            earliest_expiry_time = datetime.strptime(misc_effects[affected_person][earliest_effect_key]['expiration_date'], '%Y-%m-%d %H:%M:%S.%f')
        except (KeyError, IndexError, TypeError):
            return
        if current_time < earliest_expiry_time:
            difference = earliest_expiry_time - current_time
            time_to_wait = int(difference.total_seconds())
        else:
            time_to_wait = 1
        return time_to_wait, affected_person, earliest_effect_key

    def _get_earliest_expiry(self):
        misc_effects = self.bot_object._Plugin__db_get(['misc_modifiers'])
        earliest_expiry = '2200-01-01 00:00:00.000000'
        earliest_effect_key, user_key = None, None
        for user in misc_effects:
            for effect in misc_effects[user]:
                if misc_effects[user][effect]['expiration_date'] < earliest_expiry:
                    user_key = user
                    earliest_effect_key = effect
                    earliest_expiry = misc_effects[user][effect]['expiration_date']
        return user_key, earliest_effect_key
