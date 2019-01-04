import json
import random
import threading
import time

DISTRACTORS = 3
ABANDON_TIME = 600
ABANDON_ATTEMPTS = 4
BY_LETTER = ['A', 'B', 'C', 'D']


class Questions():
    def __init__(self, bot, chatpointsObj, chateventsObj, jsonpath):
        self.bot = bot
        self.chatpointsObj = chatpointsObj
        self.chateventsObj = chateventsObj
        self.jsonpath = jsonpath
        self.lock = threading.Lock()
        self.questions = {}
        self.current_question = None
        self.current_answers = {}
        try:
            with open(self.jsonpath, 'r+') as file:
                self.questions = json.load(file)
        except Exception:
            print('Questions could not be loaded! From: ' + jsonpath)
            pass

    def __output_to_chat(self, channel, msg):
        self.bot.privmsg(channel, msg)

    def __question_as_str(self, q):
        if q.get('c', False):
            # with distractors
            return """Solve for {points} chatpoints: "{question}" Your choices: {choices}""".format(**{
                'points': q.get('p'),
                'question': q.get('q'),
                'choices': "; ".join(q.get('c')),
            })
        # without distractors
        return """Solve for {points} chatpoints: "{question}""".format(**{
            'points': q.get('p'),
            'question': q.get('q')
        })

    def __end_question(self):
        self.current_question['answers'] = self.current_answers
        self.chateventsObj.addEvent('question', self.current_question)
        self.current_question = {}
        self.current_answers = {}

    def get_tags(self, id, channel):
        tags = {}
        for q in self.questions:
            for t in q.get('tags'):
                tags[t] = tags.get(t, 0) + 1
        self.__output_to_chat(channel, "There are {n} questions in total, by tags: {t}".format(**{
            "n": len(self.questions),
            "t": repr(tags),
        }))

    def question(self, id, channel, tags=[]):
        self.lock.acquire()
        if self.current_question:
            self.lock.release()
            self.__output_to_chat(channel, "There is already a question to solve!")
            self.__output_to_chat(channel, self.__question_as_str(self.current_question))
            return False
        questions = self.questions
        if tags:
            for tag in tags:
                questions = [q for q in self.questions if tag in q.get("tags", [])]
                if len(questions) == 0:
                    self.lock.release()
                    self.__output_to_chat(channel, "No question satisfies all tags!")
                    return False
        i = random.randint(0, len(questions) - 1)
        print(questions)
        q = questions[i]
        correct = q.get("a")[random.randint(0, len(q.get("a")) - 1)]
        all_correct = q.get('a')
        all_correct.extend(q.get('ha', []))
        self.current_question = {
            'by': id,
            'req_tag': tags,
            'req_t': time.time(),
            'channel': channel,
            'i': i,
            'q': q.get("q"),
            'a': [a.lower() for a in all_correct],  # accept all valid answers, no matter which is shown
            'p': random.randint(q.get('p')[0], q.get('p')[1]),
        }
        if q.get('d'):
            c = random.sample(q.get("d"), DISTRACTORS) + [correct]
            random.shuffle(c)
            self.current_question['c'] = [BY_LETTER[ind] + ') ' + c[ind] for ind in range(len(c))]
            # add A), a) etc as valid answers
            index = c.index(correct)
            self.current_question['a'].append(BY_LETTER[index].lower())
            self.current_question['a'].append(BY_LETTER[index].lower() + ')')
        self.lock.release()
        print(self.current_question['a'])
        self.__output_to_chat(channel, self.__question_as_str(self.current_question))
        return True

    def answer(self, id, channel, answer):
        self.lock.acquire()
        if not self.current_question:
            self.lock.release()
            return False
        if self.current_answers.get(id):
            self.lock.release()
            self.__output_to_chat(id, "You already attempted an answer!")
            return False
        answer = (" ".join(answer)).lower()
        if answer in self.current_question.get('a', []):
            self.current_question['answered_by'] = id
            self.current_question['answered_with'] = answer
            self.chatpointsObj.updateById(id, delta={'p': self.current_question.get('p', 0)},
                                          allowNegative=False,
                                          partial=False)
            self.chatpointsObj.updateById(id, delta={'questions': self.current_question.get('p', 0)},
                                          allowNegative=False,
                                          partial=False)
            self.__end_question()
            self.lock.release()
            self.__output_to_chat(channel, "{} answered correctly!".format(id))
            return True
        self.current_answers[id] = answer
        self.lock.release()
        return False

    def abandon_question(self, id, channel):
        self.lock.acquire()
        r = False
        if len(self.current_answers.values()) >= ABANDON_ATTEMPTS and \
                time.time() > self.current_question.get('req_t', time.time()) + ABANDON_TIME:
            self.current_question['abandoned_by'] = id
            self.__end_question()
            self.__output_to_chat(channel, "Abandoned the current question!")
            r = True
        self.lock.release()
        return r
