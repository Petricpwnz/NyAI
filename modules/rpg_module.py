import json
import threading
import time
from datetime import datetime, timedelta
import sys
sys.path.append("..")
from extra.chat_upgrades import CHAT_UPGRADES


MARKET_NAME = '#market'
FREE_MARKET_NAME = '#freemarket'

# upgrades = items from the market
# TODO refactor this uglyass disease and points json stuff and everything later into one proper db api (totally soon™)
class Upgrades:
    def __init__(self, bot, jsonpath):
        self.bot_instance = bot
        self.bot = bot.bot
        self.jsonpath = jsonpath
        self.lock = threading.Lock()
        try:
            with open(jsonpath, 'r+') as f:
                self.upgrades = json.load(f)
        except FileNotFoundError:
            # r+ doesn't auto create a file if it's not there, so we open file 2 times
            with open(jsonpath, 'w') as f:
                json.dump({}, f)
            with open(jsonpath, 'r') as f:
                self.upgrades = json.load(f)
        if MARKET_NAME not in self.upgrades or FREE_MARKET_NAME not in self.upgrades:
            self.set_initial_market_stock()

    def set_initial_market_stock(self):
        with self.lock:
            self.upgrades.get(MARKET_NAME, {})
            self.upgrades.get(FREE_MARKET_NAME, {})
            for item in CHAT_UPGRADES:
                if item not in self.upgrades[MARKET_NAME]:
                    self.upgrades[MARKET_NAME][item] = {}
                if 'quantity' not in self.upgrades[MARKET_NAME][item]:
                    self.upgrades[MARKET_NAME][item]['quantity'] = CHAT_UPGRADES[item].get('starting_stock', 0)
        self.set_initial_resupply_timers()

    def set_initial_resupply_timers(self):
        with self.lock:
            for item in CHAT_UPGRADES:
                hrs_to_wait = CHAT_UPGRADES[item].get('resupply_wait_hrs', 20)
                self.bot_instance._Plugin__db_add(['market_cd'], item,
                              {'time': str(time.strftime("%d-%m-%Y %H:%M:%S")),
                              'resupply_date': str(datetime.now() + timedelta(days=0,
                                                                              seconds=0,
                                                                              microseconds=0,
                                                                              milliseconds=0,
                                                                              minutes=0,
                                                                              hours=hrs_to_wait,
                                                                              weeks=0))},
                              overwrite_if_exists=True, try_saving_with_new_key=False)

    def get_upgrade_list(self):
        chat_upgrade_list = CHAT_UPGRADES
        try:
            quantities = [self.upgrades[MARKET_NAME][item].get('quantity', 'undefined') for item in chat_upgrade_list]
        except KeyError:
            self.set_initial_market_stock()
            quantities = [self.upgrades[MARKET_NAME][item].get('quantity', 'undefined') for item in chat_upgrade_list]
        return (chat_upgrade_list, quantities)

    @staticmethod
    def is_perma(upgrade):
        try:
            if CHAT_UPGRADES[upgrade].get('perma', False):
                return True
        except KeyError:
            pass
        return False

    def has_item(self, name, upgrade):
        # keyerror captured layer above, bad decision but idc since new version of the bot is in the works
        with self.lock:
            if self.upgrades[name][upgrade]:
                return True
            return False

    def save(self, path=False):
        with self.lock:
            if not path:
                path = self.jsonpath
            with open(path, 'w+') as file:
                json.dump(self.upgrades, file, indent=2)

    def getFilePath(self):
        return self.jsonpath

    def update_by_name(self, name, upgrade, quantity=0, allow_negative=False, partial=False):
        with self.lock:
            if name not in self.upgrades:
                self.upgrades[name] = {}
            if upgrade not in self.upgrades[name]:
                self.upgrades[name][upgrade] = {}
            if 'quantity' not in self.upgrades[name][upgrade]:
                self.upgrades[name][upgrade]['quantity'] = 0
            new_value = self.upgrades[name][upgrade]['quantity'] + quantity
            if not allow_negative and new_value < 0:
                if partial:
                    self.upgrades[name][upgrade]['quantity'] = 0
                return False
            self.upgrades[name][upgrade]['quantity'] = new_value
            if name != MARKET_NAME and self.upgrades[name][upgrade]['quantity'] <= 0:
                del self.upgrades[name][upgrade]
                if self.upgrades[name] == {}:
                    del self.upgrades[name]
            return True

    def _replenish_market_item(self, item):
        with self.lock:
            try:
                self.upgrades[MARKET_NAME][item]['quantity'] += 1
            except KeyError:
                self.upgrades[MARKET_NAME][item]['quantity'] = CHAT_UPGRADES[item].get('starting_stock', 0)
        self._restart_market_timer(item)

    def _restart_market_timer(self, item):
        with self.lock:
            hrs_to_wait = CHAT_UPGRADES[item].get('resupply_wait_hrs', 20)
            self.bot_instance._Plugin__db_add(['market_cd'], item,
                          {'time': str(time.strftime("%d-%m-%Y %H:%M:%S")),
                          'resupply_date': str(datetime.now() + timedelta(days=0,
                                                                          seconds=0,
                                                                          microseconds=0,
                                                                          milliseconds=0,
                                                                          minutes=0,
                                                                          hours=hrs_to_wait,
                                                                          weeks=0))},
                          overwrite_if_exists=True, try_saving_with_new_key=False)

    # Id as a string cause in json its a string; price is for single item
    def put_on_open_market(self, name, upgrade, quantity=0, price=0):
        with self.lock:
            id = 0
            if name not in self.upgrades[FREE_MARKET_NAME]:
                self.upgrades[FREE_MARKET_NAME][name] = {}
            id_exists = self.upgrades[FREE_MARKET_NAME][name].get(str(id))
            while id_exists:
                id += 1
                id_exists = self.upgrades[FREE_MARKET_NAME][name].get(str(id))
            str_id = str(id)
            self.upgrades[FREE_MARKET_NAME][name][str_id] = {}
            self.upgrades[FREE_MARKET_NAME][name][str_id][upgrade] = {}
            self.upgrades[FREE_MARKET_NAME][name][str_id][upgrade]['quantity'] = quantity
            self.upgrades[FREE_MARKET_NAME][name][str_id][upgrade]['price'] = price * quantity
            return True
            # if name != MARKET_NAME and self.upgrades[name][upgrade]['quantity'] <= 0:
            #     del self.upgrades[name][upgrade]
            #     if self.upgrades[name] == {}:
            #         del self.upgrades[name]
            # return True

    def remove_from_open_market(self, seller, id):
        with self.lock:
            if seller not in self.upgrades[FREE_MARKET_NAME] or id not in self.upgrades[FREE_MARKET_NAME].get(seller):
                return False
            del self.upgrades[FREE_MARKET_NAME][seller][id]
            return True

    def get_item_price(self, upgrade):
        stock_price = CHAT_UPGRADES[upgrade]['price']
        starting_stock = CHAT_UPGRADES[upgrade]['starting_stock']
        current_upgrade_stock = self.get_item_by_name(MARKET_NAME, upgrade)[0][1]
        try:
            modifier = current_upgrade_stock + starting_stock
            price = (stock_price * modifier) / (current_upgrade_stock * 2)
        except ZeroDivisionError:
            price = (stock_price * modifier) / 1.6
        return price

    def get_current_market_stock(self):
        return self.get_all_by_name(MARKET_NAME)

    def get_current_free_market_stock(self):
        return self.get_all_by_name(FREE_MARKET_NAME)

    def check_by_name(self, name, upgrade, quantity=0):
        with self.lock:
            new_value = self.upgrades[name][upgrade]['quantity'] + quantity
            if new_value < 0:
                return False
            return True

    def get_all_by_name(self, name):
        # keyerror handled one layer up in commands themselves
        with self.lock:
            upgrades = list(self.upgrades[name].items())
            return upgrades

    def get_item_by_name(self, name, upgrade):
        # TODO handle keyerror
        with self.lock:
            upgrade = list(self.upgrades[name][upgrade].items())
            return upgrade

    def reset(self):
        with self.lock:
            self.upgrades = {}

    # def add_new(self, id, name=False, data={}):
    #     """
    #     :param id: id of new element, will become name unless specified otherwise
    #     :param data: non default values
    #     """
    #     with self.lock:
    #         if not name:
    #             name = id
    #         self.upgrades[id] = self.__getNewDefault(name)
    #         for key in data.keys():
    #             self.upgrades[id][key] = data[key]

    # def __get_new_default(self, name="-", upgrades={'name': '', 'quantity': 0}):
    #     return {
    #         'n': name,         # name
    #         'u': upgrades,     # market items
    #         't': time.time()   # time of last update
    #     }
