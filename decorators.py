from functools import wraps
import asyncio
import configparser

config = configparser.ConfigParser()
# Disable conversion of config data to lowercase
config.optionxform = str
config.read('config.ini')

ADMINS = [n.split('@')[0].replace('!', '').replace('*', '') for n, v in config['irc3.plugins.command.masks'].items() if len(v) > 5]


def nickserv_identified(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            self, mask = args[0], args[1]
            if not (await self._Plugin__is_nick_serv_identified(mask.nick)):
                return
        except Exception:
            pass
        return func(*args, **kwargs)

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            self, mask = args[0], args[1]
            if not (await self._Plugin__is_nick_serv_identified(mask.nick)):
                return
        except Exception:
            pass
        return await func(*args, **kwargs)

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return wrapper


# admin_chan_only only restricts pm vs channels, not any channel vs specific channel
def channel_only(*args, admin_chan_only=False):
    channels = None
    if args:
        channels = args

    def outer_wrapper(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal channels
            try:
                self, nick, target = args[0], args[1].nick, args[2]
                if (nick not in ADMINS) and channels and (target not in channels):
                    return 'You can only use this command in {0}.'.format(channels)
                if (nick not in ADMINS or admin_chan_only) and not self._is_a_channel(target):
                    return 'You can only use this command in channels.'
            except Exception:
                pass
            return func(*args, **kwargs)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            nonlocal channels
            try:
                self, nick, target = args[0], args[1].nick, args[2]
                if (nick not in ADMINS) and channels and (target not in channels):
                    return 'You can only use this command in {0}.'.format(channels)
                if (nick not in ADMINS or admin_chan_only) and not self._is_a_channel(target):
                    return 'You can only use this command in channels.'
            except Exception:
                pass
            return await func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    return outer_wrapper
