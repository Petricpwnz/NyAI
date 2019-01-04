import threading
import time
import asyncio


class periodicCallback(threading.Thread):
    def __init__(self, callbackf, isAsyncioCallback=False, args={}, seconds=10):
        threading.Thread.__init__(self)
        self.daemon = True
        self.callback = callbackf
        self.isAsyncioCallback = isAsyncioCallback
        self.keepRunning = False
        self.seconds = seconds
        self.args = args
        self.next = time.time() + self.seconds
        self.lock = threading.Lock()
        if self.isAsyncioCallback:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

    def run(self):
        self.keepRunning = True
        while self.keepRunning:
            time.sleep(self.seconds)
            self.lock.acquire()
            if self.isAsyncioCallback:
                self.keepRunning = self.loop.run_until_complete(self.callback(self.args))
            else:
                self.keepRunning = self.callback(self.args)
            self.lock.release()
        if self.isAsyncioCallback:
            self.loop.close()

    def stop(self):
        self.keepRunning = False
        if self.isAsyncioCallback:
            self.loop.close()

    def isRunning(self):
        return self.keepRunning
