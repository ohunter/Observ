import math
import multiprocessing as mp
import os
import queue
import sched
import time
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

        self.prnt_w = self.scr_w - 2 * self.init_x
        self.prnt_h = self.scr_h - 2 * self.init_y

        # Open the file to read before the function is called to avoid opening a file every call
        if module_name == "CPU":
            self.data = open("/proc/stat", "r")
            self.func = self.CPU
            self.last = [[0] * 6] * mp.cpu_count()

            # The minimal possible length of a message in this module
            assert self.prnt_w > 15, "Printable width is less than the minimal print width"
        elif module_name == "CPU_LOAD":
            self.data = open("/proc/stat", "r")
            self.func = self.CPU_LOAD
            self.last = [0] * 6
            self.history = [" " * self.prnt_h] * self.prnt_w

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
        try:
            self.data.seek(0)
            loads = [""]
            while not loads[-1].startswith("intr"):
                loads.append(self.data.readline())
            loads = [[float(x) for x in line.split()[1:]] for line in loads[1:]]

            cl = [x[0]+x[2] for x in loads]
            ct = [x[0]+x[2]+x[3] for x in loads]
            ll = [x[0]+x[2] for x in self.last]
            lt = [x[0]+x[2]+x[3] for x in self.last]

            cur = [(x-x1)/(t-t1)*100 for x, t, x1, t1 in zip(cl, ct, ll, lt)]

            cpu_width = math.ceil(math.log10(mp.cpu_count()))

            strs = [f"Core {str(i).rjust(cpu_width, ' ')}: {x:5.1f}% " for i, x in enumerate(cur)]

            # As all the strings are the same length just take the length of the first string
            slen = len(strs[0])

            max_fit_w = self.prnt_w // slen
            num_fit_w = max_fit_w
            for i in range(max_fit_w, 1, -1):
                if len(strs) // i == len(strs) / i:
                    num_fit_w = i
                    break

            # Horizontal centering

            horz_rem = self.prnt_w - num_fit_w * slen
            horz_pad = horz_rem // num_fit_w

            # Vertical centering

            vert_pad = self.prnt_h // (len(strs) // num_fit_w)
            top_pad = vert_pad // 2
            bot_pad = vert_pad - top_pad
            tmp = []

            for s in ["".join([x.center(slen + horz_pad) for j, x in enumerate(strs) if j % (len(strs) // num_fit_w) == i]) for i in range(len(strs) // num_fit_w)]:
                # assert len(s) <= self.prnt_w
                tmp.extend(["\n"] * top_pad)
                tmp.append(s)
                tmp.extend(["\n"] * bot_pad)
            # egrep 'cpu[0-9]+' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {print usage }'
            msg = "".join(tmp)
            self.last = loads[:mp.cpu_count()]

            if __name__ == "__main__":
                print (msg)
            else:
                self.queue.put(message(msg, self.init_x, self.init_y))
        except BaseException as e:
            if __name__ == "__main__":
                print(f"Exception occured: {e}")
                import pdb; pdb.set_trace()
            else:
                self.queue.put(message(f"Exception occured: {e}", typ="log"))

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

            # Separate the value into its integer and decimal components
            cur = math.modf((cl - ll) / (ct - lt) * self.prnt_h)
            full = '█' * int(cur[1])

            # lst = [0, 1/8, 2/8, 3/8/ 4/8, 5/8, 6/8, 7/8]
            # rem = [' ', '▁', '▂', '▃', '▄', '▅', '▆', '▇'][min(range(8), key = lambda i: abs(lst[i]-(cur - int(cur))))]

            # tmp = cur - int(cur)

            # rem = " "

            # TODO: Figure out how to remove the branching from this section as it decreases the performance drastically

            # if tmp > 7/8:
            #     rem = 
            # elif tmp > 6/8:
            #     rem = 
            # elif tmp > 5/8:
            #     rem = 
            # elif tmp > 4/8:
            #     rem = 
            # elif tmp > 3/8:
            #     rem = 
            # elif tmp > 2/8:
            #     rem = 
            # elif tmp > 1/8:
            #     rem = 

            self.history.append(f"{full}".ljust(self.prnt_h, " "))

            if len(self.history) > self.prnt_w:
                del self.history[0]

            msg = "\n".join(reversed(["".join(x) for x in zip(*self.history)]))

            self.last = loads

            if __name__ == "__main__":
                print (msg)
            else:
                self.queue.put(message(msg, self.init_x, self.init_y))
        except BaseException as e:
            if __name__ == "__main__":
                print(f"Exception occured: {e}")
                import pdb; pdb.set_trace()
            else:
                self.queue.put(message(f"Exception occured: {e}", typ="log"))

    def RAM(self):
        pass

    def HDD(self):
        pass


if __name__ == "__main__":
    tmp_q = queue.Queue()
    module("CPU_LOAD", tmp_q, 64, 58, False, 1)
