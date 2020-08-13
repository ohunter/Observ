import multiprocessing as mp
from select import select
import signal
import sys
from itertools import accumulate, chain
from typing import Iterable, Union

import blessed as bl

import modules

                    # T    B    L    R    TL   TR    BL   BR
active_border =     ["━", "━", "┃", "┃", "┏", "┓", "┗", "┛"]
passive_border =    ["─", "─", "|", "|", "┌", "┐", "└", "┘"]

# Note: Not a great implementation as it sort of assumes that the border will be made up of UTC-8 characters and that the title wont
def _overlay(s1: str, s2: str, char=" ") -> str:
    return "".join([min(x, y) if min(x,y) != char else max(x,y) for x, y in zip(s1, s2)])

class tile():
    def __init__(self, origin: tuple = (0, 0), offset: tuple = (1, 1), border: Union[bool, Iterable, None]=None, title: str = None, *args, **kwargs) -> None:
        self.origin = origin
        self.offset = offset
        self.title = title

        if isinstance(border, bool) and border:
            self.border = passive_border
        elif isinstance(border, Iterable):
            assert len(border) == 8, f"Border can only contain 8 elements. The given element contained {len(border)}"
            self.border = border
        else:
            self.border = None

    def __contains__(self, position: tuple) -> bool:
        return position[0] >= self.origin[0] and position[0] <= self.offset[0] and position[1] >= self.origin[1] and position[1] <= self.offset[1]

    def render(self, term: bl.Terminal) -> None:
        start_pos = (round(self.origin[0] * term.width), round(self.origin[1] * term.height))
        end_pos = (round(self.offset[0] * term.width), round(self.offset[1] * term.height))

        displacement = (end_pos[0] - start_pos[0] - 2, end_pos[1] - start_pos[1] - 2)
        reset = term.move_left(displacement[0] + 2) + term.move_down(1)

        top:    str = ""
        middle: str = ""
        bot:    str = ""

        if self.border:
            top = self.border[4] + self.border[0] * displacement[0] + self.border[5]
            middle = self.border[2] + term.move_right(displacement[0]) + self.border[3]
            bot = self.border[6] + self.border[1] * displacement[0] + self.border[7]

        if self.title:
            top = _overlay(top, self.title.center(displacement[0] + 2))

        if self.border or self.title:
            top += reset

        with term.location(*start_pos):
            print (top + "".join([middle, reset] * displacement[1]) + bot, end="")

    def move(self, delta: tuple) -> None:
        self.origin = (self.origin[0] + delta[0], self.origin[1] + delta[1])
        self.offset = (self.offset[0] + delta[0], self.offset[1] + delta[1])

    def scale(self, scale: Union[tuple, float]) -> None:
        if isinstance(scale, tuple):
            self.origin = (scale[0] * self.origin[0], scale[1] * self.origin[1])
            self.offset = (scale[0] * self.offset[0], scale[1] * self.offset[1])
        else:
            self.origin = (scale * self.origin[0], scale * self.origin[1])
            self.offset = (scale * self.offset[0], scale * self.offset[1])

    def base_str(self) -> str:
        return f"{type(self)} @ {self.origin} -> {self.offset}"

    def select(self, position: tuple):
        self.border = active_border

        return self

    def deselect(self) -> None:
        self.border = passive_border

    @staticmethod
    def from_conf(conf: dict):
        root = None

        if "partitions" in conf:
            root = tile_dict[conf["partitions"]["type"]].from_conf(conf["partitions"])
        else:
            root = tile_dict[conf["module"]].from_conf(conf)

        return root

class split(tile):
    def __init__(self, splits: Union[None, Iterable], sections: Iterable, *args, **kwargs) -> None:
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

    def move(self, delta: tuple) -> None:
        super(split, self).move(delta)

        for t in self.sections:
            t.move(delta)

    def scale(self, scale: Union[tuple, float]) -> None:
        super(split, self).scale(scale)

        if isinstance(scale, tuple):
            if isinstance(self, v_split):
                self.splits = [s*scale[1] for s in self.splits]
            elif isinstance(self, h_split):
                self.splits = [s*scale[0] for s in self.splits]

            for t in self.sections:
                t.scale(scale)
        else:
            raise NotImplementedError

    def select(self, position: tuple):
        tmp = [k[0] for k in [(i, x.deselect()) for i, x in enumerate(self.sections) if position not in x]]
        return [x.select(position) for i, x in enumerate(self.sections) if i not in tmp][0]

    def deselect(self) -> None:
        [x.deselect() for x in self.sections]

    def __str__(self) -> str:
        strs = [f"{self.base_str()} | splits: {self.splits}"]
        strs.extend([str(x) for x in self.sections])
        return "\n".join(strs)

    def __contains__(self, position: tuple) -> bool:
        if super(split, self).__contains__(position):
            for t in self.sections:
                if position in t:
                    return t.select(position)
        else:
            return False

    @staticmethod
    def from_conf(conf: dict):
        tiles = []

        for s in conf["screens"]:
            tiles.append(tile.from_conf(s))

        clss = v_split if conf["orientation"] == "vertical" else h_split

        return clss(conf.get("splits"), tiles)

class tabbed(tile):
    def __init__(self, *args, **kwargs) -> None:
        super(tabbed, self).__init__(*args, **kwargs)
        self.items = args
        raise NotImplementedError

    def render(self, term: bl.Terminal) -> None:
        pass

    @staticmethod
    def from_conf(conf: dict):
        pass

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
        start_pos = (round(self.origin[0] * term.width), round(self.origin[1] * term.height))
        end_pos = (round(self.offset[0] * term.width), round(self.offset[1] * term.height))
        x = (end_pos[0] - start_pos[0]) // 2 - len(self.text)//2 + start_pos[0]
        y = (end_pos[1] - start_pos[1]) // 2 + start_pos[1]
        with term.location(x, y):
            print(self.text)

    def __str__(self) -> str:
        return f"{self.base_str()} | text: {self.text}"

    @staticmethod
    def from_conf(conf: dict):
        return line_tile(conf["text"], (0, 0), (1,1), conf.get("border"), conf.get("title"))

class text_tile(tile):
    def __init__(self, text: str, *args, **kwargs) -> None:
        super(line_tile, self).__init__(*args, **kwargs)
        self.text = text

    def render(self, term: bl.Terminal) -> None:
        super(line_tile, self).render(term)
        start_pos = (round(self.origin[0] * term.width), round(self.origin[1] * term.height))
        end_pos = (round(self.offset[0] * term.width), round(self.offset[1] * term.height))

        pass

    @staticmethod
    def from_conf(conf: dict):
        return text_tile(conf["text"], (0, 0), (1,1), conf.get("border"), conf.get("title"))

class chart(tile):
    def __init__(self, func, *args, **kwargs) -> None:
        super(chart, self).__init__(*args, **kwargs)

        self.func = func

class history(chart):
    def __init__(self, *args, **kwargs) -> None:
        super(history, self).__init__(*args, **kwargs)

        self.history = []

class bars(chart):
    def __init__(self, bar_titles: Iterable, *args, **kwargs) -> None:
        super(bars, self).__init__(*args, **kwargs)

tile_dict = {
    "tiled": split,
    "tabbed": tabbed,
    "line": line_tile,
    "text": text_tile,
}
