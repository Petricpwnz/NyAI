from __future__ import print_function
from keras.models import Sequential
from keras.layers import Dense, Activation
from keras.layers import LSTM
from keras.optimizers import RMSprop
import numpy as np
import random
# import sys
import json

MAXLEN = 40


class LSTMGen():

    def __init__(self, bot):
        self.bot = bot
        self.canGenerate = False
        weightsfile = self.bot.config.get('lstm_weights', False)
        charfile = self.bot.config.get('lstm_chars', False)
        if not (weightsfile and charfile):
            print('Failed getting LSTM file paths')
            return

        with open(charfile, 'r') as file:
            self.chars = json.load(file)
            self.chars = sorted(self.chars)

        self.char_indices = dict((c, i) for i, c in enumerate(self.chars))
        self.indices_char = dict((i, c) for i, c in enumerate(self.chars))

        self.bot.config.get('spam_protect_time', 600)
        self.ready = False
        print('Building LSTM model...')
        self.model = Sequential()
        self.model.add(LSTM(128, input_shape=(MAXLEN, len(self.chars))))
        self.model.add(Dense(len(self.chars)))
        self.model.add(Activation('softmax'))
        try:
            self.model.set_weights(np.load(weightsfile))
        except Exception:
            print('Failed building LSTM model!')
            return
        optimizer = RMSprop(lr=0.01)
        self.model.compile(loss='categorical_crossentropy', optimizer=optimizer)
        self.canGenerate = True

    def sample(self, preds, temperature=1.0):
        # helper function to sample an index from a probability array
        preds = np.asarray(preds).astype('float64') + 0.00001
        preds = np.log(preds) / temperature
        exp_preds = np.exp(preds)
        preds = exp_preds / np.sum(exp_preds)
        probas = np.random.multinomial(1, preds, 1)
        return np.argmax(probas)

    def generate(self, start, diversity, size):
        if not self.canGenerate:
            return start
        sentence = start.lower()
        generated = ''
        if not len(sentence) == 40:
            print('cancel gen', len(sentence))
            return

        for i in range(size + 200):
            x = np.zeros((1, MAXLEN, len(self.chars)))
            for t, char in enumerate(sentence):
                x[0, t, self.char_indices.get(char, " ")] = 1.

            preds = self.model.predict(x, verbose=0)[0]
            next_index = self.sample(preds, diversity)
            next_char = self.indices_char[next_index]

            if next_char == ' ' and i >= size:
                next_char = '\n'
            if next_char == '\n':
                if random.random() * size < i:
                    break
                next_char = ' '

            generated += next_char
            sentence = sentence[1:] + next_char
        return generated
