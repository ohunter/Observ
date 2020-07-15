import os
import sys
import curses
import json
import logging
import argparse

from typing import Iterable
from multiprocessing import Process

class screen_tree():
    def __init__(self, root : dict) -> None:

        # Assumes that the only node not given a name is the root node
        self.name : str = root["name"] if "name" in root else "root"
        # The step across the dimension for the subdivisions given as a percentage
        self.delta : float = root["delta"] if "delta" in root else -1
        # The refresh rate of the screen in Hz
        self.refresh : float = root["refresh"] if "refresh" in root else 1
        # Whether or not the region will have a border
        self.border : bool  = root["border"] if "border" in root else True
        # The type of the subdivisions of the screen
        self.type : str = root["subdivisions"]["type"] if "subdivisions" in root else "tiled"
        # The orientation of the subdivisions of the screen
        self.orientation : str = root["subdivisions"]["orientation"] if "subdivisions" in root else "vertical"
        # How the screen will be subdivided further
        self.subdivisions = []

        if "subdivisions" in root:
            self.subdivisions.extend([screen_tree(x) for x in root["subdivisions"]["screens"]])

        d = (1 - sum([x.delta for x in self.subdivisions if x.delta > 0])) / max(1, len([x for x in self.subdivisions if x.delta == -1]))
        for sub in [x for x in self.subdivisions if x.delta == -1]:
            sub.delta = d

    def __str__(self) -> str:
        l = []

        ntv = [(0, self)]

        while ntv:
            indent, current = ntv[0]
            l.append(f"{' ' * indent}{current.name} : delta: {current.delta}, refresh: {current.refresh}, border: {current.border}, orientation: {current.orientation}")
            ntv = [(indent+2, x) for x in current.subdivisions] + ntv[1:]

        return "\n".join(l)

    def validate(self) -> bool:
        if any([x.delta > 1 for x in self.subdivisions]) or sum([x.delta for x in self.subdivisions]) > 1:
            return False

        return True

    def validate_tree(self) -> bool:
        ntv = [self]

        while ntv:
            current = ntv[0]
            if not current.validate():
                return False
            ntv = current.subdivisions + ntv[1:]

        return True

class screen():
    def __init__(self, scr, node: screen_tree, init_x: int, init_y: int, width: int, height: int) -> None:
        self.super_window = scr
        try:
            self.window = scr.subwin(height, width, init_y, init_x)
        except BaseException as e:
            self.window = curses.newwin(height, width, init_y, init_x)
        self.sub_windows = []

        if node.border:
            self.window.box()

        logging.debug(f"initializing screen with area: ({init_x}, {init_y})\t({init_x+width}, {init_y+height})")

        # self.refresh = node.refresh

        if node.subdivisions:
            if node.type == "tiled":

                cur_x, cur_y = init_x, init_y
                cur_d = 0
                for sub in node.subdivisions:
                    if node.orientation == "vertical":
                        cur_d = int(sub.delta * height) if round(sub.delta * height) == int(sub.delta * height) else int(sub.delta * height) + 1
                        self.sub_windows.append(
                            screen(
                                self.window,
                                sub,
                                cur_x,
                                cur_y,
                                width,
                                cur_d
                            )
                        )
                        cur_y += cur_d
                    else:
                        cur_d = int(sub.delta * width) if round(sub.delta * width) == int(sub.delta * width) else int(sub.delta * width) + 1
                        self.sub_windows.append(
                            screen(
                                self.window,
                                sub,
                                cur_x,
                                cur_y,
                                cur_d,
                                height
                            )
                        )
                        cur_x += cur_d
            else:
                raise NotImplementedError

        self.window.refresh()

def main(stdscr, args):
    term_height, term_width = stdscr.getmaxyx()

    curses.noecho()
    curses.cbreak()

    config = None
    tree = None

    logging.info("Loading configuration file")
    with open(args.config) as fi:
        config = json.load(fi)
        tree = screen_tree(list(config.values())[0])
        tree.delta = 1

    valid = tree.validate_tree()
    logging.info(f"Configuration successfully validated: {valid}")

    if not valid:
        logging.error("Invalid configuration file")
        sys.exit(1)

    logging.debug(tree)

    logging.info("Setting up screens")
    screens = screen(stdscr, tree, 0, 0, term_width, term_height)

    logging.info("Successfully set up screens")
    while 1:
        pass

if __name__ == "__main__":

    import time

    parser = argparse.ArgumentParser(description='A system monitor written with modularity and customizability in mind')
    parser.add_argument("-c", "--config", type=str, default=os.path.abspath(os.path.dirname(__file__)) + "/conf.json", help="The path to the configuration file for the process")
    parser.add_argument("-l", "--log", type=str, nargs='?', const=os.path.abspath(os.path.dirname(__file__)) + f"/{'_'.join(time.ctime().split())}.log", help="The path to the configuration file for the process")

    args = parser.parse_args()

    if args.log:
        logging.basicConfig(level=logging.NOTSET, filename=args.log, filemode='w', format='%(asctime)s [%(levelname)s]\t%(message)s', datefmt='%d-%b-%y %H:%M:%S')
    else:
        logging.basicConfig(level=logging.CRITICAL+1)

    logging.info("Starting application")
    logging.info(f"Using configuration located at {args.config}")
    logging.info(f"Allowing curses to handle terminal setup")
    curses.wrapper(main, args)