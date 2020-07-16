from time import sleep
from typing import Iterable, Union


class message():
    def __init__(self, message: str, x: int = 0, y: int = 0) -> None:
        self.x = x
        self.y = y
        self.content = message

def NONE():
    pass

def CPU(q, width: int, height: int, border: Union[bool, Iterable], rate: float):
    init_x = 0 if not border else 1
    init_y = 0 if not border else 1
    tmp = 0
    while 1:
        q.put(message(f"This is the CPU Module\nMessage {tmp}", init_x, init_y), False)
        tmp += 1

        # TODO:
        #  - Fix rate issue
        #  - Implement actual functionality of function

        # Note to self:
        # There are several issues with using `sleep()` here.
        # A few of which are:
        #  - It causes an issue when sent the `SIGTERM` signal ie `CTRL+C`
        #  - If the message formulation takes longer than the remainder of time it will get out of sync quickly

        sleep(rate)

def RAM(q, width: int, height: int, border: Union[bool, Iterable], rate: float):
    init_x = 0 if not border else 1
    init_y = 0 if not border else 1
    tmp = 0
    while 1:
        q.put(message(f"This is the RAM Module\nMessage {tmp}", init_x, init_y), False)
        tmp += 1

        # TODO:
        #  - Fix rate issue
        #  - Implement actual functionality of function

        # Note to self:
        # There are several issues with using `sleep()` here.
        # A few of which are:
        #  - It causes an issue when sent the `SIGTERM` signal ie `CTRL+C`
        #  - If the message formulation takes longer than the remainder of time it will get out of sync quickly

        sleep(rate)

def HDD(q, width: int, height: int, border: Union[bool, Iterable], rate: float):
    init_x = 0 if not border else 1
    init_y = 0 if not border else 1
    tmp = 0
    while 1:
        q.put(message(f"This is the HDD Module\nMessage {tmp}", init_x, init_y), False)
        tmp += 1

        # TODO:
        #  - Fix rate issue
        #  - Implement actual functionality of function

        # Note to self:
        # There are several issues with using `sleep()` here.
        # A few of which are:
        #  - It causes an issue when sent the `SIGTERM` signal ie `CTRL+C`
        #  - If the message formulation takes longer than the remainder of time it will get out of sync quickly

        sleep(rate)