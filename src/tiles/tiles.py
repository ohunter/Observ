import importlib as il
import math
import os
import time
from itertools import accumulate, chain, product, zip_longest
from typing import Any, Iterable, List, Dict, Tuple, Type, Union

import blessed as bl

mo = il.import_module("modules", ".")
rt = il.import_module("realtime", ".")
gpu = il.import_module("gpu", ".")

                    # T    B    L    R    TL   TR    BL   BR
passive_border =    ["─", "─", "│", "│", "┌", "┐", "└", "┘"]

def _adjust_prefix(value: int, start_index = 0):
    size_list = ["B", "k", "M", "G", "T", "P"]
    idx = start_index
    idx += math.floor(math.log10(value)/3)
    value /= 1024 ** idx

    return f"{value:.2f} {size_list[idx] + 'B' if idx != 0 else ''}"

def _min_diff(_iter: Iterable[float], val) -> float:
    diff = float("inf")
    key = -1
    for x in _iter:
        if abs(val - x) < diff:
            key = x
            diff = abs(val - x)

    return key

def _rotate_strings(_iter: Iterable[str]) -> Iterable[str]:
    return ["".join(x) for x in zip(*_iter)][::-1]

def _divisors(val: int) -> List[int]:
    return [i for i in range(1, val+1) if val % i == 0]

# Note: Not a great implementation as it sort of assumes that the border will be made up of UTF-8 characters and that the title wont
def _overlay(s1: str, s2: str, char=" ") -> str:
    """
    A function to overlay two strings on top of each other.
    """
    return "".join([min(x, y) if min(x,y) != char else max(x,y) for x, y in zip_longest(s1, s2, fillvalue=char)])

class _Position():
    def __init__(self, x: int = 0, y: int = 0) -> None:
        self.x = round(x)
        self.y = round(y)

    def __add__(self, o: Union[int, Tuple[int, int], Type]):
        if isinstance(o, int):
            return _Position(self.x + o, self.y + o)
        elif isinstance(o, Tuple):
            return _Position(self.x + o[0], self.y + o[1])
        elif type(self) == type(o):
            return _Position(self.x + o.x, self.y + o.y)

    def __sub__(self, o: Union[int, Tuple[int, int], Type]):
        if isinstance(o, int):
            return _Position(self.x - o, self.y - o)
        elif isinstance(o, Tuple):
            return _Position(self.x - o[0], self.y - o[1])
        elif type(self) == type(o):
            return _Position(self.x - o.x, self.y - o.y)

    def __floordiv__(self, o: Union[int, Tuple[int, int], Type]):
        if isinstance(o, int):
            return _Position(self.x // o, self.y // o)
        elif isinstance(o, Tuple):
            return _Position(self.x // o[0], self.y // o[1])
        elif type(self) == type(o):
            return _Position(self.x // o.x, self.y // o.y)

    def __truediv__(self, o: Union[int, Tuple[int, int], Type]):
        return self//o

    def __eq__(self, o: Union[Tuple[int, int], Type]) -> bool:
        if isinstance(o, Tuple):
            return self.x == o[0] and self.y == o[1]
        elif type(self) == type(o):
            return self.x == o.x and self.y == o.y

    def __ne__(self, o: Union[Tuple[int, int], Type]) -> bool:
        return not self == o

    def __str__(self) -> str:
        return f"{(self.x, self.y)}"

    def __iter__(self):
        tmp = [self.x, self.y]
        for v in tmp:
            yield v

class tile():
    """
    The base class for all tile objects in the monitor

    Args:

        Origin:
            A Tuple[float, float] describing the initial position (as a percentage) for the tile's top left corner
        Offset:
            A Tuple[float, float] describing the final position (as a percentage) for the tile's bottom right
        Border:
            Bool: If True the tile will use the default border provided by the program, else no border is provided
            Iterable: An iterable containing each of the elements for the borders in the following order: [TOP, BOTTOM, LEFT, RIGHT, TOP LEFT, TOP RIGHT, BOTTOM LEFT, BOTTOM RIGHT]
            None: The tile will have no border
        Title:
            A string that will be displayed in the top center of the tile
    """
    def __init__(self, origin: Tuple[float, float] = (0, 0), offset: Tuple[float, float] = (1, 1), border: Union[bool, Iterable[str], None]=None, title: str = None, *args, **kwargs) -> None:
        self.origin = origin
        self.offset = offset
        self.title = title

        self.frequency = kwargs["frequency"] if "frequency" in kwargs else 1

        if isinstance(border, bool) and border:
            self.border = passive_border
            self._original_border = passive_border
        elif isinstance(border, Iterable):
            assert len(border) == 8, f"Border can only contain 8 elements. The given element contained {len(border)}"
            self.border = border
            self._original_border = border
        else:
            self.border = None
            self._original_border = None

    def render(self, term: bl.Terminal) -> None:
        """
        Draws the relevant information to the tile's location in the terminal
        """
        # TODO: Figure out how to detect if the edges need to be updated or not
        self._update_edges(term)

    def move(self, delta: Tuple[float, float]) -> None:
        """
        Moves the tile to in the direction of the vector given
        """
        self.origin = (self.origin[0] + delta[0], self.origin[1] + delta[1])
        self.offset = (self.offset[0] + delta[0], self.offset[1] + delta[1])

    def scale(self, scale: Union[Tuple[float, float], float]) -> None:
        """
        Scales the tile by the value provided
        """
        if isinstance(scale, Tuple):
            self.origin = (scale[0] * self.origin[0], scale[1] * self.origin[1])
            self.offset = (scale[0] * self.offset[0], scale[1] * self.offset[1])
        else:
            self.origin = (scale * self.origin[0], scale * self.origin[1])
            self.offset = (scale * self.offset[0], scale * self.offset[1])

    def _base_str(self) -> str:
        return f"{type(self)} @ {self.origin} -> {self.offset}"

    def redraw(self, term: bl.Terminal) -> None:
        """
        Forces a complete redraw of the tile ensuring that all the content is overwritten
        """
        filler = " " * self.dimensions.x + term.move_left(self.dimensions.x)

        with term.location(*self.start_loc):
            print(term.move_down(1).join([filler] * self.dimensions.y), end="")

        self.render(term)

    def timing(self) -> Iterable[float]:
        return [(self.frequency, self)]

    def _update_edges(self, term) -> None:

        self.start_loc = start_loc = _Position(round(self.origin[0] * term.width), round(self.origin[1] * term.height))
        end_loc = _Position(round(self.offset[0] * term.width), round(self.offset[1] * term.height))

        self.dimensions = end_loc - start_loc
        reset = term.move_down(1) + term.move_x(start_loc.x) #"\033[1E" + f"\033[{start_loc.x+1}G"

        top:    str = " " * (self.dimensions.x)
        middle: str = term.move_right(self.dimensions.x)
        bot:    str = term.move_right(self.dimensions.x)

        if self.border or self.title:

            self.start_loc += (0, 1)
            self.dimensions = end_loc - self.start_loc

            if self.border:
                self.start_loc += (1, 0)
                end_loc -= 1
                self.dimensions = end_loc - self.start_loc


                top = self.border[4] + self.border[0] * (self.dimensions.x) + self.border[5]
                middle = self.border[2] + term.move_right(self.dimensions.x) + self.border[3]
                bot = self.border[6] + self.border[1] * (self.dimensions.x) + self.border[7]

            if self.title:
                top = _overlay(top, self.title.center(self.dimensions.x))

                if not self.border:
                    middle = reset + term.move_right(1)
                    bot = reset + term.move_right(1)

            top += reset
            middle += reset

        with term.location(*start_loc):
            print (top + middle * self.dimensions.y + bot, end="")

    def start_concurrent(self) -> None:
        if isinstance(self, split):
            [x.start_concurrent() for x in self.sections]
        elif isinstance(self, tabbed):
            [x.start_concurrent() for x in self.tabs]
        elif isinstance(self, realtime_tile) and self.module and not self.module.started:
            self.module.start()
        else:
            return

    def __contains__(self, position: Tuple[float, float]) -> bool:
        return position[0] >= self.origin[0] and position[0] <= self.offset[0] and position[1] >= self.origin[1] and position[1] <= self.offset[1]

    @staticmethod
    def from_conf(conf: Dict[str, Any]):
        root = None

        if "partitions" in conf:
            root = _tile_dict[conf["partitions"]["type"]].from_conf(conf["partitions"])
        else:
            root = _tile_dict[conf["module"]].from_conf(conf)

        return root

class split(tile):
    def __init__(self, splits: Union[None, Iterable[float]], sections: Iterable[tile], *args, **kwargs) -> None:
        super(split, self).__init__(*args, **kwargs)

        assert not splits or len(splits) == len(sections) - 1, f"Expected {len(sections) - 1} split points, but was given {len(splits)}"
        self.splits = splits if isinstance(splits, Iterable) and splits else accumulate([1 / len(sections)] * (len(sections) - 1))
        self.splits = [x for x in chain([0], self.splits, [1])]
        self.sections = sections

        for start, stop, t in zip(self.splits[:-1], self.splits[1:], self.sections):
            if isinstance(self, v_split):
                t.scale((1, stop - start))
                t.move((0, start))
            elif isinstance(self, h_split):
                t.scale((stop - start, 1))
                t.move((start, 0))

    def render(self, term: bl.Terminal) -> None:
        for x in self.sections:
            x.render(term)

    def move(self, delta: Tuple[float, float]) -> None:
        super(split, self).move(delta)

        for t in self.sections:
            t.move(delta)

    def scale(self, scale: Union[Tuple[float, float], float]) -> None:
        super(split, self).scale(scale)

        if isinstance(scale, Tuple):
            if isinstance(self, v_split):
                self.splits = [s*scale[1] for s in self.splits]
            elif isinstance(self, h_split):
                self.splits = [s*scale[0] for s in self.splits]

            for t in self.sections:
                t.scale(scale)
        else:
            raise NotImplementedError

    def redraw(self, term: bl.Terminal) -> None:
        """
        Forces a complete redraw of the tile ensuring that all the content is overwritten
        """
        for t in self.sections:
            t.redraw(term)

        self.render(term)

    def timing(self) -> Iterable[float]:
        return [y for x in self.sections for y in x.timing()]

    def __str__(self) -> str:
        strs = [f"{self._base_str()} | splits: {self.splits}"]
        strs.extend([str(x) for x in self.sections])
        return "\n".join(strs)

    def __contains__(self, position: Tuple[float, float]) -> bool:
        if super(split, self).__contains__(position):
            return [t.__contains__(position) for t in self.sections if position in t][0]
        else:
            return False

    @staticmethod
    def from_conf(conf: Dict[str, Any]):
        tiles = []

        for s in conf["screens"]:
            tiles.append(tile.from_conf(s))

        clss = v_split if conf["orientation"] == "vertical" else h_split

        return clss(conf.get("splits"), tiles)

class tabbed(tile):
    def __init__(self, tabs: Iterable[tile], *args, **kwargs) -> None:
        super(tabbed, self).__init__(*args, **kwargs)
        self.tabs = tabs
        self.active_tab = self.tabs[0]
        self.title = ""
        raise NotImplementedError

    def render(self, term: bl.Terminal) -> None:
        active_index = self.tabs.index(self.active_tab)
        max_index = len(self.tabs)
        printable_width = round((self.offset[0] - self.origin[0]) * term.width) - round(math.ceil(math.log10(active_index * max_index)) + 4)
        title = f"{self.active_tab.title.ljustify(printable_width, ' ')[:printable_width]} ({active_index}/{max_index})"
        tmp = self.active_tab.title

        self.active_tab.title = title
        self.active_tab.render(term)
        self.active_tab.title = tmp

    def move(self, delta:Tuple[float, float]) -> None:
        super(tabbed, self).move(delta)

        for t in self.tabs:
            t.move(delta)

    def scale(self, scale: Union[Tuple[float, float], float]) -> None:
        super(tabbed, self).scale(scale)

        if isinstance(scale, Tuple[float, float]):
            for t in self.tabs:
                t.scale(scale)
        else:
            raise NotImplementedError

    def select(self, position: Tuple[float, float], term: bl.Terminal):
        index = self.tabs.index(self.active_tab)

        if index == 0:
            pass
        elif index == len(self.tabs) - 1:
            pass
        else:
            pass
        tmp = [k[0] for k in [(i, x.deselect(term)) for i, x in enumerate(self.tabs) if position not in x]]
        return [x.select(position, term) for i, x in enumerate(self.tabs) if i not in tmp][0]

    def deselect(self, term) -> None:
        [x.deselect(term) for x in self.tabs]

    def __str__(self) -> str:
        strs = [f"{self._base_str()} | splits: {self.splits}"]
        strs.extend([str(x) for x in self.tabs])
        return "\n".join(strs)

    def __contains__(self, position: Tuple[float, float]) -> bool:
        if super(tabbed, self).__contains__(position):
            return self.active_tab.__contains__(position)
        else:
            return False

    def _direction(self, position: Tuple[float, float]) -> int:
        pass

    @staticmethod
    def from_conf(conf: Dict[str, Any]):
        tiles = []

        for s in conf["screens"]:
            tiles.append(tile.from_conf(s))

        return tabbed(tiles)

class h_split(split):
    def __init__(self, *args, **kwargs) -> None:
        super(h_split, self).__init__(*args, **kwargs)

class v_split(split):
    def __init__(self, *args, **kwargs) -> None:
        super(v_split, self).__init__(*args, **kwargs)

class line_tile(tile):
    def __init__(self, text: str, *args, **kwargs) -> None:
        super(line_tile, self).__init__(*args, **kwargs)
        self.text = text

    def render(self, term: bl.Terminal) -> None:
        super(line_tile, self).render(term)
        with term.location(*self.start_loc + self.dimensions/2 - (len(self.text)//2, 0)):
            print(self.text, end="")

    def __str__(self) -> str:
        return f"{self._base_str()} | text: {self.text}"

class multi_line_tile(tile):
    def __init__(self, num_lines, *args, **kwargs) -> None:
        super(multi_line_tile, self).__init__(*args, **kwargs)
        self.positions = []
        self._num_lines = num_lines

    def render(self, term: bl.Terminal) -> None:
        super(multi_line_tile, self).render(term)

    def move(self, delta: Tuple[float, float]) -> None:
        super(multi_line_tile, self).move(delta)

        self.distribute_lines(self._num_lines)

    def scale(self, scale: Union[Tuple[float, float], float]) -> None:
        super(multi_line_tile, self).scale(scale)

        self.distribute_lines(self._num_lines)

    def distribute_lines(self, num: int) -> None:
        N = self.offset[0] - self.origin[0]
        M = self.offset[1] - self.origin[1]

        divisors = _divisors(num)
        target_ratio = N / M

        ratios = [(a, b, a/b) for a,b in product(divisors, repeat=2) if a * b == num]

        ratio = ratios[0]

        for a, b, c in ratios[1:]:
            ratio = (a, b, c) if abs(target_ratio - c) < abs(target_ratio - ratio[2]) else ratio

        pos_x = [N / ratio[0] * i for i in range(ratio[0]+1)]
        pos_x = [(a+b)/2 + self.origin[0] for a, b in zip(pos_x[:-1], pos_x[1:])]
        pos_y = [M / ratio[1] * i for i in range(ratio[1]+1)]
        pos_y = [(a+b)/2 + self.origin[1] for a, b in zip(pos_y[:-1], pos_y[1:])]

        self.positions = [(x, y) for x in pos_x for y in pos_y]

class realtime_tile(tile):
    def __init__(self, *args, **kwargs) -> None:
        super(realtime_tile, self).__init__(*args, **kwargs)
        self.module = rt.execution.procure(self, *args, **kwargs)

class time_tile(line_tile, realtime_tile):
    def __init__(self, *args, **kwargs) -> None:
        kwargs.update({ "func": time.time,
                        "func_kwargs": {}, "return_type": float, "text": ""})
        super(time_tile, self).__init__(*args, **kwargs)

    def render(self, term: bl.Terminal) -> None:
        self.text = f"{self.module.fetch(self):.3f}"
        super(time_tile, self).render(term)

    @staticmethod
    def from_conf(conf: Dict[str, Any]):
        return time_tile(**conf)

class ctime_tile(line_tile, realtime_tile):
    def __init__(self, *args, **kwargs) -> None:
        kwargs.update({ "func": time.ctime,
                        "func_kwargs": {}, "return_type": str, "text": ""})
        super(ctime_tile, self).__init__(*args, **kwargs)

    def render(self, term: bl.Terminal) -> None:
        self.text = self.module.fetch(self)
        super(ctime_tile, self).render(term)

    @staticmethod
    def from_conf(conf: Dict[str, Any]):
        return ctime_tile(**conf)

class cpu_tile(multi_line_tile, realtime_tile):
    def __init__(self, *args, **kwargs) -> None:
        kwargs.update({"num_lines": os.cpu_count(),
                        "func": mo.CPU,
                        "func_kwargs": {"files": ["/proc/stat"]},
                        "return_type": list,
                        "initial": [(0, 0)] * os.cpu_count(),
                        "store_results": True})
        super(cpu_tile, self).__init__(*args, **kwargs)

    def render(self, term: bl.Terminal) -> None:
        super(cpu_tile, self).render(term)

        out = self.module.fetch(self)
        while len(out) > 2:
            out.pop(0)

        cur = [(cl-ll)/max(ct-lt, 1) * 100 for (ll, lt), (cl, ct) in zip(*out)]
        num_core_width = math.ceil(math.log10(os.cpu_count()+0.1))
        strs = [f"Core {str(i).rjust(num_core_width)}: {x:5.1f}%" for i, x in enumerate(cur)]

        for (_x, _y), s in zip(self.positions, strs):
            pos = _Position(_x * term.width, _y * term.height) - (len(s)//2, 0)
            with term.location(*pos):
                print(s, end="")

    @staticmethod
    def from_conf(conf: Dict[str, Any]):
        return cpu_tile(**conf)

class plot_tile(realtime_tile):
    def __init__(self, *args, **kwargs) -> None:
        self._raw_history = []
        self._line_history = []
        self.history = []
        super(plot_tile, self).__init__(*args, **kwargs)

    def render(self, term: bl.Terminal) -> None:
        super(plot_tile, self).render(term)

        while len(self._line_history) < self.dimensions.x-1:
            self._line_history.append(" " * self.dimensions.y)
        while len(self._line_history) >= self.dimensions.x:
            self._line_history.pop(0)

        while len(self._raw_history) < self.dimensions.x-1:
            self._raw_history.append((0, 0))
        while len(self._raw_history) >= self.dimensions.x:
            self._raw_history.pop(0)

        while len(self.history) >= self.dimensions.x:
            self.history.pop(0)

    def plot(self, term: bl.Terminal):
        decimal, integer = math.modf(self.history[-1]*self.dimensions.y)
        s = f"{'█' * int(integer)}" + _line_subdivisions[_min_diff(range(9), decimal)/8]
        s = s.ljust(self.dimensions.y)
        self._line_history.append(s)

        vert_lines = _rotate_strings(self._line_history)

        self.text = f"{term.move_down(1) + term.move_x(self.start_loc.x)}".join(vert_lines)

class cpu_load_tile(plot_tile):
    def __init__(self, *args, **kwargs) -> None:
        kwargs.update({ "func": mo.CPU_LOAD,
                        "func_kwargs": {"files": ["/proc/stat"]},
                        "return_type": float,
                        "initial": (0, 0)})
        super(cpu_load_tile, self).__init__(*args, **kwargs)
        self._raw_history.append((0, 0))

    def render(self, term: bl.Terminal) -> None:
        super(cpu_load_tile, self).render(term)

        self._raw_history.append(self.module.fetch(self))
        last = self._raw_history[-2]
        cur = self._raw_history[-1]
        self.history.append((cur[0]-last[0])/max(cur[1]-last[1], 1))

        super(cpu_load_tile, self).plot(term)

        with term.location(*self.start_loc):
            print(self.text, end="")

    @staticmethod
    def from_conf(conf: Dict[str, Any]):
        return cpu_load_tile(**conf)

class ram_tile(multi_line_tile, realtime_tile):
    def __init__(self, *args, **kwargs) -> None:
        kwargs.update({ "num_lines": 4, "func": mo.RAM,
                        "func_kwargs": {"files": ["/proc/meminfo"]},
                        "return_type": tuple,
                        "initial": ((0, ""), (0, ""), (0, ""))})
        super(ram_tile, self).__init__(*args, **kwargs)

    def render(self, term: bl.Terminal) -> None:
        super(ram_tile, self).render(term)

        out = self.module.fetch(self)

        names = ["Free:", "In Use:", "Available:", "Total:"]

        strs = [f"{_type.ljust(max([len(x) for x in names]))} {x:.2f} {size + 'B' if size != 'B' else size}" for _type, (x, size) in zip(names, out)]

        for (_x, _y), s in zip(self.positions, strs):
            pos = _Position(_x * term.width, _y * term.height) - (len(s)//2, 0)
            with term.location(*pos):
                print(s, end="")

    @staticmethod
    def from_conf(conf: Dict[str, Any]):
        return ram_tile(**conf)

class ram_load_tile(plot_tile):
    def __init__(self, *args, **kwargs) -> None:
        kwargs.update({ "func": mo.RAM_LOAD,
                        "func_kwargs": {"files": ["/proc/meminfo"]}, "return_type": float})
        super(ram_load_tile, self).__init__(*args, **kwargs)
        self._raw_history.append((0, 0))

    def render(self, term: bl.Terminal) -> None:
        super(ram_load_tile, self).render(term)

        self.history.append(self.module.fetch(self))

        super(ram_load_tile, self).plot(term)

        with term.location(*self.start_loc):
            print(self.text, end="")

    @staticmethod
    def from_conf(conf: Dict[str, Any]):
        return ram_load_tile(**conf)

class gpu_tile(multi_line_tile, realtime_tile):
    def __init__(self, gpu_type: str = "Nvidia", gpu_index: int = 0, *args, **kwargs) -> None:
        lib = None
        if gpu_type == "Nvidia":
            lib = gpu.NVML()
            lib.setup()
            lib.initialize()
            device = lib.device(gpu_index)
        else:
            raise NotImplementedError
        kwargs.update({ "num_lines": 8, "func": mo.GPU,
                        "func_kwargs": {"device" : device}, "return_type": tuple, "initial": ("",( 1, 1, 1, 1, 1, 1, 1)),  "libs": [lib]})
        super(gpu_tile, self).__init__(*args, **kwargs)

    def render(self, term: bl.Terminal) -> None:
        super(gpu_tile, self).render(term)

        name, out = self.module.fetch(self)

        names = ["Name:", "Memory Free:", "Memory Total:", "Temperature:", "Powerdraw:", "Fan RPM:", "Clockspeed:", "Utilization:"]
        nam_w = max([len(x) for x in names])
        strs = [
            f"{names[0].ljust(nam_w)} {name}",
            f"{names[1].ljust(nam_w)} {_adjust_prefix(out[0])}",
            f"{names[2].ljust(nam_w)} {_adjust_prefix(out[1])}",
            f"{names[3].ljust(nam_w)} {out[2]} C",
            f"{names[4].ljust(nam_w)} {out[3]/1000} W",
            f"{names[5].ljust(nam_w)} {out[4]} % RPM",
            f"{names[6].ljust(nam_w)} {out[5]} MHz",
            f"{names[7].ljust(nam_w)} {out[6]} %",
            ]

        for (_x, _y), s in zip(self.positions, strs):
            pos = _Position(_x * term.width, _y * term.height) - (len(s)//2, 0)
            with term.location(*pos):
                print(s, end="")

    @staticmethod
    def from_conf(conf: Dict[str, Any]):
        return gpu_tile(**conf)

_tile_dict = {
    "tiled": split,
    "tabbed": tabbed,
    "time": time_tile,
    "ctime": ctime_tile,
    "cpu": cpu_tile,
    "cpu load": cpu_load_tile,
    "ram": ram_tile,
    "ram load": ram_load_tile,
    "gpu": gpu_tile,
}

_line_subdivisions = {
    0/8: " ",
    1/8: "▁",
    2/8: "▂",
    3/8: "▃",
    4/8: "▄",
    5/8: "▅",
    6/8: "▆",
    7/8: "▇",
    8/8: "█",
}
