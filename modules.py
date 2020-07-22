import os
import queue
import sched
import time
import multiprocessing as mp
from typing import Iterable, Union

class message():
    def __init__(self, message: str, x: int = 0, y: int = 0, typ: str = "msg") -> None:
        self.x = x
        self.y = y
        self.content = message
        self.type = typ

class module():
    def __init__(self, module_name: str, q: mp.Queue, width: int, height: int, border: Union[bool, Iterable], rate: float) -> None:
        self.queue = q
        self.sch = sched.scheduler(time.time, time.sleep)
        self.init_x = 0 if not border else 1
        self.init_y = 0 if not border else 1
        self.scr_w = width
        self.scr_h = height

        self.history = []

        # Open the file to read before the function is called to avoid opening a file every call
        if module_name == "CPU":
            self.data = open("/proc/stat", "r")
            self.func = self.CPU
        elif module_name == "CPU_LOAD":
            self.data = open("/proc/stat", "r")
            self.func = self.CPU_LOAD
            self.last = [0] * 6

        self.run(rate, self.func)

    def run(self, rate, func):
        def tick():
            t = time.time()
            cnt = 0
            while 1:
                cnt += 1
                yield max(t + cnt/rate - time.time(),0)

        gen = tick()
        while 1:
            func()
            time.sleep(next(gen))

    def CPU(self):
        self.data.seek(0)
        msg = self.data.readlines(13)

        # egrep 'cpu[0-9]+' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {print usage }'

        self.queue.put(message("".join(msg), self.init_x, self.init_y))

    def CPU_LOAD(self):
        """
        This function calculates the current load of all the CPU's on the system through `/proc/stat`. Essentially the function is equivalent to the following bash command:

        awk '{u=$2+$4; t=$2+$4+$5; if (NR==1){u1=u; t1=t;} else print ($2+$4-u1) * 100 / (t-t1) "%"; }' (grep 'cpu ' /proc/stat) <(sleep 1;grep 'cpu ' /proc/stat)
        """
        try:
            self.data.seek(0)
            loads = [float(x) for x in self.data.readline().split()[1:]]

            cl = loads[0]+loads[2]
            ct = loads[0]+loads[2]+loads[3]
            ll = self.last[0]+self.last[2]
            lt = self.last[0]+self.last[2]+self.last[3]

            cur = round((cl - ll) / (ct - lt) * (self.scr_h - 2 * self.init_y))

            self.history.append(f"{'|' * cur}{' ' * ((self.scr_h - 2 * self.init_y) - cur)}")

            if len(self.history) > (self.scr_w - (self.init_x * 2)):
                self.history.pop(0)

            msg = "\n".join(reversed(["".join(x) for x in zip(*self.history)]))

            self.last = loads

            if __name__ == "__main__":
                print (msg)
            else:
                self.queue.put(message(msg, self.init_x, self.init_y))
        except BaseException as e:
            if __name__ == "__main__":
                print(f"Exception occured: {e}")
            else:
                self.queue.put(message(f"Exception occured: {e}", typ="log"))

    def RAM(self):
        pass

    def HDD(self):
        pass


if __name__ == "__main__":
    tmp_q = queue.Queue()
    module("CPU_LOAD", tmp_q, 10, 10, False, 2)