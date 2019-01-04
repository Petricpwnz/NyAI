import threading
import time


class timedInputAccumulatorThread(threading.Thread):
    def __init__(self, callbackf=False, args={}, seconds=10, maxduration=60):
        threading.Thread.__init__(self)
        self.daemon = True
        self.keepRunning = True
        self.hasCallback = False
        self.lock = threading.Lock()
        if callbackf:
            self.setCallback(callbackf, args=args, seconds=seconds, maxduration=maxduration)

    def run(self):
        while True:
            self.lock.acquire()
            if not self.keepRunning:
                self.lock.release()
                break
            if self.hasCallback and (time.time() > self.timeEnd):
                self.callback(self.args, self.inputs)
                self.hasCallback = False
            self.lock.release()
            time.sleep(0.5)

    def setCallback(self, callbackf, args={}, seconds=10, maxduration=60):
        self.lock.acquire()
        self.callback = callbackf
        self.originalSeconds = seconds
        self.timeEnd = time.time() + self.originalSeconds
        self.maxTimeEnd = self.timeEnd + maxduration
        self.args = args
        self.inputs = []
        self.hasCallback = True
        self.lock.release()

    def addInput(self, input, resetTimer=False, addSeconds=0):
        self.lock.acquire()
        response = False
        if self.keepRunning:
            self.inputs.append(input)
            if resetTimer:
                self.timeEnd = time.time() + self.originalSeconds
            self.timeEnd += addSeconds
            self.timeEnd = min([self.timeEnd, self.maxTimeEnd])
            response = True
        self.lock.release()
        return response

    def stop(self):
        # should be lock saved...
        self.keepRunning = False

    def hasPendingCallback(self):
        self.lock.acquire()
        response = self.hasCallback
        self.lock.release()
        return response
