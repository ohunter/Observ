from io import TextIOWrapper
import math
import multiprocessing as mp
import threading as th
import os
import queue
import time
from typing import Any, Callable, Iterable, List, Mapping, Tuple, TypedDict, Union

size_list = ["B", "k", "M", "G", "T", "P"]

def CPU(files: Mapping[str, TextIOWrapper], *args, **kwargs) -> List[Tuple[float, float]]:
    data = files["/proc/stat"]

    data.seek(0)

    loads = [""]
    while not loads[-1].startswith("intr"):
        loads.append(data.readline())
    loads = [[float(x) for x in line.split()[1:]] for line in loads[1:]]

    cl = [x[0]+x[2] for x in loads]
    ct = [x[0]+x[2]+x[3] for x in loads]

    return [(x, t) for x, t in zip(cl, ct)]

def CPU_LOAD(files: Mapping[str, TextIOWrapper], *args, **kwargs) -> Tuple[float, float]:
    data = files["/proc/stat"]
    data.seek(0)

    loads = [float(x) for x in data.readline().split()[1:]]

    return (loads[0]+loads[2], loads[0]+loads[2]+loads[3])

def RAM(files: Mapping[str, TextIOWrapper], *args, **kwargs) -> Tuple[float, str, float, str]:
    data = files["/proc/meminfo"]
    data.seek(0)

    loads = []
    for i in range(3):
        loads.append([float(x) if j % 2 == 0 else x for j, x in enumerate(data.readline().split()[1:])])

    usage = loads[0][0] - loads[2][0] * 1000 ** (size_list.index(loads[0][1][0]) - size_list.index(loads[2][1][0]))
    cur = usage / loads[0][0] * 100

    ui = size_list.index(loads[2][1][0])
    ui += math.floor(math.log10(usage)/3)
    usage /= 1000 ** (ui-size_list.index(loads[2][1][0]))

    ti = size_list.index(loads[0][1][0])
    ti += math.floor(math.log10(loads[0][0])/3)
    loads[0][0] /= 1000 ** (ti-size_list.index(loads[0][1][0]))

    size_w = math.ceil(math.log10(loads[0][0])) + 3

    total = round(loads[0][0], 2)
    used = round(usage, 2)
    #     if module_name == "RAM":
    #         self.data = open("/proc/meminfo", "r")
    #         self.func = self.RAM
    #     elif module_name == "RAM_LOAD":
    #         self.data = open("/proc/meminfo", "r")
    #         self.func = self.RAM_LOAD
    #         self.history = [" " * self.prnt_h] * self.prnt_w
    #     elif module_name == "SWAP":
    #         self.data = open("/proc/meminfo", "r")
    #         self.func = self.SWAP
    #     elif module_name == "HDD":
    #         self.data = open("/proc/diskstats", "r")
    #         self.func = self.HDD


    #     self.run(rate, self.func)

    # def run(self, rate, func):
    #     def tick():
    #         t = time.time()
    #         cnt = 0
    #         while 1:
    #             cnt += 1
    #             yield max(t + cnt/rate - time.time(),0)

    #     gen = tick()
    #     while 1:
    #         func()
    #         time.sleep(next(gen))

    def RAM(self):
        try:
            self.data.seek(0)

            loads = []
            for i in range(3):
                loads.append([float(x) if j % 2 == 0 else x for j, x in enumerate(self.data.readline().split()[1:])])

            usage = loads[0][0] - loads[2][0] * 1000 ** (size_list.index(loads[0][1][0]) - size_list.index(loads[2][1][0]))
            cur = usage / loads[0][0] * 100

            ui = size_list.index(loads[2][1][0])
            ui += math.floor(math.log10(usage)/3)
            usage /= 1000 ** (ui-size_list.index(loads[2][1][0]))

            ti = size_list.index(loads[0][1][0])
            ti += math.floor(math.log10(loads[0][0])/3)
            loads[0][0] /= 1000 ** (ti-size_list.index(loads[0][1][0]))

            size_w = math.ceil(math.log10(loads[0][0])) + 3

            total = round(loads[0][0], 2)
            used = round(usage, 2)

            strs = f"RAM: {cur:5.1f}% {str(used).rjust(size_w)} {size_list[ui]}B / {str(total).rjust(size_w)} {size_list[ti]}B"

            # Horizontal centering is already computed since there is only one string

            # Vertical centering

            vert_pad = self.prnt_h - 1
            top_pad = vert_pad // 2
            bot_pad = vert_pad - top_pad

            msg = "".join(["\n"] * top_pad + [strs.center(self.prnt_w)] + ["\n"] * bot_pad)

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

    # def RAM_LOAD(self):
    #     try:
    #         self.data.seek(0)

    #         loads = []
    #         for i in range(3):
    #             loads.append([float(x) if j % 2 == 0 else x for j, x in enumerate(self.data.readline().split()[1:])])

    #         usage = loads[0][0] - loads[2][0] * 1000 ** (size_list.index(loads[0][1][0]) - size_list.index(loads[2][1][0]))
    #         cur = math.modf(usage / loads[0][0] * self.prnt_h)
    #         full = '█' * int(cur[1])

    #         self.history.append(f"{full}".ljust(self.prnt_h, " "))

    #         if len(self.history) > self.prnt_w:
    #             del self.history[0]

    #         msg = "\n".join(reversed(["".join(x) for x in zip(*self.history)]))
    #         if __name__ == "__main__":
    #             print (msg)
    #         else:
    #             self.queue.put(message(msg, self.init_x, self.init_y))
    #     except BaseException as e:
    #         if __name__ == "__main__":
    #             print(f"Exception occured: {e}")
    #             import pdb; pdb.set_trace()
    #         else:
    #             self.queue.put(message(f"Exception occured: {e}", typ="log"))

    # def SWAP(self):
    #     try:
    #         self.data.seek(0)

    #         loads = []
    #         for i in range(17):
    #             loads.append([float(x) if j % 2 == 0 else x for j, x in enumerate(self.data.readline().split()[1:])])
    #         loads = loads[15:]
    #         cur = loads[1][0] / loads[0][0] * 100

    #         ui = size_list.index(loads[1][1][0])
    #         ui += math.floor(math.log10(max(1, loads[1][0]))/3)
    #         loads[1][0] /= 1000 ** (ui-size_list.index(loads[1][1][0]))

    #         ti = size_list.index(loads[0][1][0])
    #         ti += math.floor(math.log10(loads[0][0])/3)
    #         loads[0][0] /= 1000 ** (ti-size_list.index(loads[0][1][0]))

    #         size_w = math.ceil(math.log10(loads[0][0])) + 3

    #         total = round(loads[0][0], 2)
    #         used = round(loads[1][0], 2)

    #         strs = f"SWAP: {cur:5.1f}% {str(used).rjust(size_w)} {size_list[ui]}B / {str(total).rjust(size_w)} {size_list[ti]}B"

    #         # Horizontal centering is already computed since there is only one string

    #         # Vertical centering

    #         vert_pad = self.prnt_h - 1
    #         top_pad = vert_pad // 2
    #         bot_pad = vert_pad - top_pad

    #         msg = "".join(["\n"] * top_pad + [strs.center(self.prnt_w)] + ["\n"] * bot_pad)

    #         if __name__ == "__main__":
    #             print (msg)
    #         else:
    #             self.queue.put(message(msg, self.init_x, self.init_y))
    #     except BaseException as e:
    #         if __name__ == "__main__":
    #             print(f"Exception occured: {e}")
    #             import pdb; pdb.set_trace()
    #         else:
    #             self.queue.put(message(f"Exception occured: {e}", typ="log"))

    # def HDD(self):
    #     try:
    #         self.data.seek(0)
    #         loads = [[float(x) if i != 2 else x for i, x in enumerate(line.split())] for line in self.data.readlines()]

    #         devs = [line[2] for line in loads]
    #         reads = [line[3] for line in loads]
    #         total_read_time = [line[6] for line in loads]
    #         writes = [line[7] for line in loads]
    #         total_write_time = [line[10] for line in loads]


    #         msg = "\n".join([f"{dev.ljust(max([len(x) for x in devs]))} : Average Read Time: {trt/max(1, read):.2f} ms | Average Write Time: {twt/max(1, write):.2f} ms" for dev, read, trt, write, twt in zip(devs, reads, total_read_time, writes, total_write_time)])

    #         if __name__ == "__main__":
    #             print (msg)
    #             pass
    #         else:
    #             self.queue.put(message(msg, self.init_x, self.init_y))
    #     except BaseException as e:
    #         if __name__ == "__main__":
    #             print(f"Exception occured: {e}")
    #             import pdb; pdb.set_trace()
    #         else:
    #             self.queue.put(message(f"Exception occured: {e}", typ="log"))

    # """
    # - GPU Monitoring
    #     - Intel
    #     - Nvidia
    #     - AMD
    # - Network Activity
    #     - Wifi
    #     - Wired
    # - Disk usage
    # - Thermals
    # """

if __name__ == "__main__":
    kwargs = {
        'files': {"/proc/stat": open("/proc/stat")}
    }
    history = [(0, 0)] * 10
    while 1:
        history.append(CPU_LOAD(**kwargs))
        while len(history) > 10:
            history.pop(0)
        load_pairs = [(a, b) for a, b in zip(history[:-1], history[1:])]
        loads = [(fl-sl)/max(ft-st, 1) for ((sl, st), (fl, ft)) in load_pairs]
        print (loads)
        time.sleep(1)
