import threading
import time
from datetime import datetime


class StartOverException(Exception):
    """Raise to restart the market thread loop"""
    pass


"""
Reusing reminder/tails code cause lazy and cause it's better to recharge each item independantly instead of all at once which
will be advantageous to certain timezones.
"""


class MarketResupplyThread(threading.Thread):
    def __init__(self, bot_object, bot):
        threading.Thread.__init__(self)
        self.bot = bot
        self.bot_object = bot_object
        if not self.bot_object._Plugin__db_get(['market_cd']):
            self.bot_object.Upgrades.set_initial_resupply_timers()

    def run(self):
        while True:
            try:
                try:
                    time_to_wait, item_to_replenish = self._time_until_replenishing()
                except (KeyError, TypeError, IndexError):
                    raise StartOverException
                time.sleep(1)
                for second in range(0, time_to_wait + 1):
                    time.sleep(1)
                    if second >= time_to_wait:
                        self.bot_object.Upgrades._replenish_market_item(item_to_replenish)
                        raise StartOverException
                raise StartOverException
            except StartOverException as ex:
                time.sleep(1)
                continue

    def _time_until_replenishing(self):
        current_time = datetime.now()
        try:
            market_cd = self.bot_object._Plugin__db_get(['market_cd'])
            item_to_replenish = self._get_earliest_expiry()
            earliest_resupply = datetime.strptime(market_cd[item_to_replenish]['resupply_date'], '%Y-%m-%d %H:%M:%S.%f')
        except (KeyError, IndexError, TypeError):
            return
        if current_time < earliest_resupply:
            difference = earliest_resupply - current_time
            time_to_wait = int(difference.total_seconds())
        else:
            time_to_wait = 1
        return time_to_wait, item_to_replenish

    def _get_earliest_expiry(self):
        market_cd = self.bot_object._Plugin__db_get(['market_cd'])
        earliest_resupply = '2200-01-01 00:00:00.000000'
        earliest_upgrade_key = None
        for i, item in enumerate(market_cd):
            if market_cd[item]['resupply_date'] < earliest_resupply:
                earliest_upgrade_key = item
                earliest_resupply = market_cd[item]['resupply_date']
        return earliest_upgrade_key

    def reset(self):
        self.bot_object.Upgrades.set_initial_market_stock()
