import time
from datetime import datetime, timedelta
from random import randint, choice


BOT_NAME = 'NyAI'


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
            'Ready To Get Kicked': self.potion_closure(itemname='Ready To Get Kicked', modifier=13, min_lasting=2),
            'Lockpick': self.theft_closure(itemname='Lockpick', chance_increase=25, percent_steal=0.03),
            'Safe Cracker': self.theft_closure(itemname='Safe Cracker', chance_increase=50, percent_steal=0.05),
            'Sneak 100': self.theft_closure(itemname='Sneak 100', chance_increase=90, percent_steal=0.1)
        }

    def switch_getter(self):
        return self.switch

    def bomb_closure(self, tier=1, itemname='insert item name here'):
        def bomb(mask, target, item_target):
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
        def potion(mask, target, item_target):
            if not item_target:
                item_target = mask.nick
            with self.MODIFIERLOCK:
                if self.bot_instance.modifier.modifiers_arent_empty():
                    self.bot_instance.modifier.refresh_with_new_modifier()
                self.bot_instance._Plugin__db_add(['misc_modifiers', item_target], itemname,
                              {'modifier': modifier, 'time': str(time.strftime("%d-%m-%Y %H:%M:%S")),
                              'expiration_date': str(datetime.now() + timedelta(days=0,
                                                                               seconds=0,
                                                                               microseconds=0,
                                                                               milliseconds=0,
                                                                               minutes=min_lasting,
                                                                               hours=0,
                                                                               weeks=0))},
                              overwrite_if_exists=True, try_saving_with_new_key=False)
            self.bot_instance.pm_fix(mask, target, f'{mask.nick} uses {itemname} on {item_target}! His chatpoing gain from typing is '
                                                   f'modified by a factor of {modifier} for {min_lasting} minutes!')
        return potion

    def theft_closure(self, itemname='insert item name here', chance_increase=0, percent_steal=0):
        def theft(mask, target, item_target):
            security_items = {
                'Hardened Lock': {
                    'chance': 15,
                    'captured_msg': f'{mask.nick} uses {itemname} on {item_target}! But {item_target} had Hardened Locks installed! Failing to crack '
                                    f'the door in time, he gets spotted by {item_target} who promptly calls the police! '
                                    f'He will be in jail for 24 hours, unable to gain points from typing or use items! '
                                    f'He can use !paybail to get out immediately for 200 chatpoints.'
                },
                'High Grade Safe': {
                    'chance': 30,
                    'captured_msg': f'{mask.nick} uses {itemname} on {item_target}! But {item_target} keeps his money in a High Grade Safe! '
                                    f'After fiddling around for a while he gets hit in the back of his head with a bat after which he wakes up in jail! '
                                    f'He will be in jail for 24 hours, unable to gain points from typing or use items! '
                                    f'He can use !paybail to get out immediately for 200 chatpoints.'
                },
                'Secure Chambers': {
                    'chance': 60,
                    'captured_msg': f'{mask.nick} uses {itemname} on {item_target}! But {item_target} keeps his money in his personal Fun Box! '
                                    f'After entering his chambers, {mask.nick} encountered countless traps and horrors which made him break down and surrender immediately. '
                                    f'He will be in jail for 24 hours, unable to gain points from typing or use items! '
                                    f'He can use !paybail to get out immediately for 200 chatpoints.'
                }
            }

            if not item_target:
                self.bot_instance.pm_fix(mask.nick, target, f'You have to specify the target of theft.')
                return
            if self.bot_instance._is_a_channel(item_target):
                self.bot_instance.pm_fix(mask.nick, target, f'You can\'t steal from channels.')
                return
            if mask.nick == item_target:
                self.bot_instance.pm_fix(mask.nick, target, f'Really there? Is that some sort of split personality or just exceptionally high intelligence?')
                return
            captured_messages = [
                f'{mask.nick} uses {itemname} on {item_target}! He fails and is captured! '
                f'He will be in jail for 24 hours, unable to gain points from typing or use items! '
                f'He can use !paybail to get out immediately for 200 chatpoints.',
            ]
            default_fail_chance = 70
            chance_decrease = 0
            for item in security_items:
                try:
                    if self.bot_instance.Upgrades.has_item(item_target, item):
                        chance_decrease += security_items[item].get('chance', 0)
                        captured_messages.append(security_items[item].get('captured_msg', ''))
                except KeyError:
                    pass
            roll = randint(0, 100)
            if roll >= default_fail_chance - chance_increase + chance_decrease:
                success = True
            else:
                success = False
            if item_target == BOT_NAME:
                success = False
                bot_steal = True
                captured_messages = [
                    f'{mask.nick} uses {itemname} on {item_target}! As he breaks into NyAI\'s chambers he finds out it\'s a foxgirl dungeon! '
                    f'He gets captured and milked endlessly, losing 500 points, after which he gets handed to the authorities! '
                    f'He will be in jail for 24 hours, unable to gain points from typing or use items! '
                    f'He can use !paybail to get out immediately for 200 chatpoints.'
                ]
            else:
                bot_steal = False
            if success:
                with self.CHATLVLLOCK:
                    self.bot_instance.debugPrint('commandlock acquire item point manip')
                    try:
                        point_share = self.bot_instance.Chatpoints.getPointsById(item_target) * percent_steal
                        points = randint(200, 500) + point_share
                        target_account = self.bot_instance.Chatpoints.getPointsById(item_target)
                        check_pts = target_account - points
                        if check_pts < 0:
                            gain = target_account
                        else:
                            gain = points
                        if self.bot_instance.Chatpoints.is_in_chat_db(item_target):
                            self.bot_instance.Chatpoints.updateById(item_target, delta={'p': -gain}, allowNegative=False, partial=True)
                            self.bot_instance.Chatpoints.updateById(item_target, delta={'items': -gain}, allowNegative=True)

                            self.bot_instance.Chatpoints.updateById(mask.nick, delta={'p': gain}, allowNegative=False, partial=True)
                            self.bot_instance.Chatpoints.updateById(mask.nick, delta={'items': gain}, allowNegative=True)
                            self.bot_instance.Chatevents.addEvent('item_use', {
                                'by': mask.nick,
                                'target': item_target,
                                'points': -gain,
                            })
                    except KeyError:
                        gain = 0
                    self.bot_instance.debugPrint('commandlock release item point manip')

                    self.bot_instance.pm_fix(mask.nick, target, f'{mask.nick} uses {itemname} on {item_target}! He successfully steals {gain:.0f} points!')
            else:
                if bot_steal:
                    with self.CHATLVLLOCK:
                        self.bot_instance.Chatpoints.updateById(mask.nick, delta={'p': -500}, allowNegative=False, partial=True)
                        self.bot_instance.Chatpoints.updateById(mask.nick, delta={'items': -500}, allowNegative=True)
                with self.MODIFIERLOCK:
                    if self.bot_instance.modifier.modifiers_arent_empty():
                        self.bot_instance.modifier.refresh_with_new_modifier()
                    self.bot_instance._Plugin__db_add(['misc_modifiers', mask.nick], itemname,
                                  {'modifier': 0, 'jail': True, 'time': str(time.strftime("%d-%m-%Y %H:%M:%S")),
                                  'expiration_date': str(datetime.now() + timedelta(days=1,
                                                                                   seconds=0,
                                                                                   microseconds=0,
                                                                                   milliseconds=0,
                                                                                   minutes=0,
                                                                                   hours=0,
                                                                                   weeks=0))},
                                  overwrite_if_exists=True, try_saving_with_new_key=False)
                self.bot_instance.pm_fix(mask.nick, target, choice(captured_messages))
        return theft
