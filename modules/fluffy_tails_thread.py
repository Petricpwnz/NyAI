import threading
import time
from datetime import datetime


class StartOverException(Exception):
    """Raise to restart the tails thread loop"""
    pass


class FluffyTailsThread(threading.Thread):
    def __init__(self, bot_object, bot):
        threading.Thread.__init__(self)
        # self.new_reminder = threading.Event()
        self.bot = bot
        self.bot_object = bot_object

    def run(self):
        while True:
            try:
                try:
                    time_to_wait, affected_person = self._time_until_expiry()
                except (KeyError, TypeError, IndexError):
                    raise StartOverException
                time.sleep(1)
                for second in range(0, time_to_wait + 1):
                    # print(second)
                    time.sleep(1)
                    if second >= time_to_wait:
                        self.bot_object._clear_tails_effect(affected_person)
                        raise StartOverException
                raise StartOverException
            except StartOverException as ex:
                time.sleep(1)
                continue

    def _time_until_expiry(self):
        current_time = datetime.now()
        try:
            tail_effects = self.bot_object._Plugin__db_get(['fluffy_tails'])
            affected_person = self._get_earliest_expiry()
            earliest_expiry_time = datetime.strptime(tail_effects[affected_person]['expiration_date'], '%Y-%m-%d %H:%M:%S.%f')
        except (KeyError, IndexError, TypeError):
            return
        if current_time < earliest_expiry_time:
            difference = earliest_expiry_time - current_time
            time_to_wait = int(difference.total_seconds())
        else:
            time_to_wait = 1
        return time_to_wait, affected_person

    def _get_earliest_expiry(self):
        tail_effects = self.bot_object._Plugin__db_get(['fluffy_tails'])
        earliest_expiry = '2200-01-01 00:00:00.000000'
        earliest_username_key = None
        for i, user in enumerate(tail_effects):
            if tail_effects[user]['expiration_date'] < earliest_expiry:
                earliest_username_key = user
        return earliest_username_key
