import time
from datetime import datetime, timedelta


class SpecialEffectHandler:
    def __init__(self, bot, chatlvllock, modlock):
        self.bot_instance = bot
        self.bot = bot.bot
        self.CHATLVLLOCK = chatlvllock
        self.MODIFIERLOCK = modlock
        self.switch = {
            'Fireworks': self.bomb_closure(tier=1, itemname='Fireworks'),
            'Bomb': self.bomb_closure(tier=2, itemname='Bomb'),
            'Jihad Suit': self.bomb_closure(tier=3, itemname='Jihad Suit'),
            # 'Tripwire': self.trap_closure(tier=1, itemname='Tripwire'),
            # 'Pitfall': self.trap_closure(tier=2, itemname='Pitfall'),
            # 'Landmine': self.trap_closure(tier=3, itemname='Landmine'),
            'Small Energy Potion': self.potion_closure(itemname='Small Energy Potion', modifier=1.5, min_lasting=720),
            'Medium Energy Potion': self.potion_closure(itemname='Medium Energy Potion', modifier=2, min_lasting=720),
            'Large Energy Potion': self.potion_closure(itemname='Large Energy Potion', modifier=3, min_lasting=720),
            'Chatwarrior Potion': self.potion_closure(itemname='Chatwarrior Potion', modifier=4, min_lasting=60),
            'Berserker Potion': self.potion_closure(itemname='Berserker Potion', modifier=7, min_lasting=15),
            'Ready To Get Kicked': self.potion_closure(itemname='Ready To Get Kicked', modifier=13, min_lasting=2)
        }

    def switch_getter(self):
        return self.switch

    def bomb_closure(self, tier=1, itemname='insert item name here'):
        def bomb(mask, target):
            userlist = list(self.bot.channels[target])
            with self.CHATLVLLOCK:
                self.bot_instance.debugPrint('commandlock acquire item point manip')
                for user in userlist:
                    try:
                        name, points = user, (tier ** 2) * 20
                        if self.bot_instance.Chatpoints.is_in_chat_db(name):
                            self.bot_instance.Chatpoints.updateById(name, delta={'p': -points}, allowNegative=False, partial=True)
                            self.bot_instance.Chatpoints.updateById(name, delta={'items': -points}, allowNegative=True)
                            self.bot_instance.Chatevents.addEvent('item_use', {
                                'by': mask.nick,
                                'target': 'all_online',
                                'points': -points,
                            })
                    except KeyError:
                        pass
                self.bot_instance.debugPrint('commandlock release item point manip')

            self.bot_instance.pm_fix(mask.nick, target, f'{mask.nick} uses {itemname}! Everyone in this channel loses {points} points!')
        return bomb

    # def trap_closure(self, tier=1, itemname='insert item name here'):
    #     def trap(mask, target, tier=tier):
    #         userlist = list(self.bot.channels[target])
    #         with self.CHATLVLLOCK:
    #             self.bot_instance.debugPrint('commandlock acquire item point manip')
    #             for user in userlist:
    #                 try:
    #                     name, points = user, (tier ** 2) * 20
    #                     print(self.bot_instance.Chatpoints.is_in_chat_db(name))
    #                     if self.bot_instance.Chatpoints.is_in_chat_db(name):
    #                         self.bot_instance.Chatpoints.updateById(name, delta={'p': -points}, allowNegative=False, partial=True)
    #                         self.bot_instance.Chatpoints.updateById(name, delta={'items': -points}, allowNegative=True)
    #                         self.bot_instance.Chatevents.addEvent('item_use', {
    #                             'by': mask.nick,
    #                             'target': 'all_online',
    #                             'points': -points,
    #                         })
    #                 except KeyError:
    #                     pass
    #             self.bot_instance.debugPrint('commandlock release item point manip')

    #         self.bot_instance.pm_fix(mask.nick, target, f'{mask.nick} uses {itemname}! Everyone in this channel loses {points} points!')
    #     return trap

    # highest possible stacked modifier with all potions + best tails effect = x51 points gain xDDDDD
    def potion_closure(self, itemname='insert item name here', modifier=1, min_lasting=1):
        def potion(mask, target):
            with self.MODIFIERLOCK:
                self.bot_instance._Plugin__db_add(['misc_modifiers', mask.nick], itemname,
                              {'modifier': modifier, 'time': str(time.strftime("%d-%m-%Y %H:%M:%S")),
                              'expiration_date': str(datetime.now() + timedelta(days=0,
                                                                               seconds=0,
                                                                               microseconds=0,
                                                                               milliseconds=0,
                                                                               minutes=min_lasting,
                                                                               hours=0,
                                                                               weeks=0))},
                              overwrite_if_exists=True, try_saving_with_new_key=False)
            self.bot_instance.pm_fix(mask.nick, target, f'{mask.nick} uses {itemname}! His chatpoing gain from typing is '
                                                        f'modified by a factor of {modifier} for {min_lasting} minutes!')
        return potion
