# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from enum import Enum

class Slot(Enum):
    HALF_HOUR = 1
    ONE_HOUR = 2
    TWO_HOURS = 3
    NONE = 4

class NoMeetingPeriod(Enum):
    BEFORE_8AM = 1
    DURING_LUNCH = 2
    AFTER_5PM = 3
    NONE = 4

class Transportation(Enum):
    CAR = 1
    BUS = 2
    BICYCLE = 3
    FOOT = 4

class UserProfile:
    def __init__(self, name: str = None, age: int = 0, addr: str = None, meetingslot = Slot.NONE, nomeetperiod = NoMeetingPeriod.NONE, transportation = Transportation.FOOT):
        self.name = name
        self.age = age
        self.addr = addr

        self.meetingSlot = meetingslot
        self.nomeetPeriod = nomeetperiod
        self.transportation = transportation
