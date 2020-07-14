# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from enum import Enum


class Question(Enum):
    NAME = 1
    AGE = 2
    ADDR = 3
    NONE = 4

class Question2(Enum):
    MEETINGSOLT = 1
    NOMEETPERIOD = 2
    TRANSPORTATION = 3
    NONE = 4

class State(Enum):
    PROFILE = 1
    PREFERENCE = 2
    FILE = 3
    HELP = 4
    NONE = 5


class ConversationFlow:
    def __init__(
        self, last_question_asked: Question = Question.NONE, state=State.NONE, last_question_asked2=Question2.NONE
    ):
        self.last_question_asked = last_question_asked
        self.last_question_asked2 = last_question_asked2
        self.CalenderState = state
