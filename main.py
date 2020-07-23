import argparse
import curses
import json
import logging
import multiprocessing as mp
import os
import sys

import modules

class screen_tree():
    def __init__(self, root : dict) -> None:

        # Assumes that the only node not given a name is the root node
        self.name : str = root["name"] if "name" in root else "root"
        # The step across the dimension for the subdivisions given as a percentage
        self.delta : float = root["delta"] if "delta" in root else -1
        # The frequency rate of the screen in Hz
        self.frequency : float = root["frequency"] if "frequency" in root else 1
        # Whether or not the region will have a border
        self.border : bool  = root["border"] if "border" in root else True
        # Defines the module being displayed within the given screen
        self.module : str = root["module"] if "module" in root else "NONE"
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
            l.append(f"{' ' * indent}{current.name} : delta: {current.delta}, frequency: {current.frequency}, border: {current.border}, orientation: {current.orientation}")
            ntv = [(indent+2, x) for x in current.subdivisions] + ntv[1:]

        return "\n".join(l)

    def validate(self) -> bool:
        if any([x.delta > 1 for x in self.subdivisions]) or sum([x.delta for x in self.subdivisions]) > 1:
            return False
        if self.subdivisions and self.module != "NONE":
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

        self.bounds = (init_x, init_y, init_x + width, init_y + height)

        if node.border:
            self.window.box()

        logging.debug(f"initializing screen with area: ({init_x}, {init_y})\t({init_x+width}, {init_y+height})")

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
        else:

            # Note to self:
            # Consider using a set of named Process objects in order to avoid duplicate system processes performing the same code

            logging.debug(f"Starting sub-process with target: {node.module}")
            self.q = mp.Queue()
            self.proc = mp.Process(target=modules.module, args=(node.module, self.q, width, height, node.border, node.frequency,), daemon=True)
            self.proc.start()

        self.window.refresh()

    def update_screen(self) -> bool:
        try:
            logging.debug(f"Updating window in region ({self.bounds[0]}, {self.bounds[1]}) - ({self.bounds[2]}, {self.bounds[3]})")
            if self.sub_windows:
                return any([scr.update_screen() for scr in self.sub_windows])
            else:
                if not self.q.empty():

                    # Note to self:
                    # Consider using a multiprocessing.sharedctypes.Array object to transport data between the processes.
                    # At first glance it seems faster than using normal IPC and has the added benefit of not having a scaling memory usage,
                    # Other benefits may include the ability to better work with the refresh rate option given a module

                    msg : modules.message = self.q.get(False)

                    if msg.type == "log":
                        logging.debug(msg.content)
                    else:
                        logging.debug(f"Recieved message with content: {msg.content}")

                        for y, line in enumerate(msg.content.split("\n"), msg.y):
                            self.window.addstr(y, msg.x, line)

                        self.window.noutrefresh()

                        return True
                return False
        except BaseException as e:
            curses.savetty()
            curses.echo()
            import pdb; pdb.set_trace()
            curses.resetty()

def main(stdscr, args):
    term_height, term_width = stdscr.getmaxyx()

    stdscr.nodelay(True)

    config: dict
    tree: screen_tree
    screens: screen

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

    logging.info("Setting up screens")
    screens = screen(stdscr, tree, 0, 0, term_width, term_height)

    logging.info("Successfully set up screens")

    # Note to self:
    # Instead of iterating through all the different modules. Use some sort of scheduling so that you only evaluate the modules that you know are gonna be updated every iteration and sleep until the next one.
    # Each iteration would have to evaluate which modules to check next
    while 1:
        try:
            inp = stdscr.getkey()

            if inp == "q":
                break
        except BaseException:
            pass

        if screens.update_screen():
            curses.doupdate()

if __name__ == "__main__":

    import time

    parser = argparse.ArgumentParser(
        description="A system monitor written with modularity and customizability in mind."
    )

    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default=os.path.abspath(os.path.dirname(__file__)) + "/conf.json",
        help=f"The path to the configuration file for the process. The default location is: {os.path.abspath(os.path.dirname(__file__))}/"
    )

    parser.add_argument(
        "-l",
        "--log",
        type=str,
        nargs='?',
        const=os.path.abspath(os.path.dirname(__file__)) + f"/{'_'.join(time.ctime().split())}.log",
        help=f"The path to the configuration file for the process. The default location is: {os.path.abspath(os.path.dirname(__file__))}/"
    )

    # Note to self:
    # Look into whether it is possible to make an argument be conditionally dependent on another argument.
    # eg: The `-ll`/`--log_level` argument can only be supplied when the `-l`/`--log` argument is present
    parser.add_argument(
        "-ll",
        "--log_level",
        type=int,
        default=3,
        help="The level the logger will output for. Corresponds to 1/10 of the logging levels for python. Only works if the log flag is given."
    )

    args = parser.parse_args()

    args.log_level = 0 if not args.log_level else args.log_level

    if args.log:
        logging.basicConfig(level=args.log_level * 10, filename=args.log, filemode='w', format='%(asctime)s [%(levelname)s]\t%(message)s', datefmt='%d-%b-%y %H:%M:%S')
    else:
        logging.basicConfig(level=logging.CRITICAL+1)

    logging.info("Starting application")
    logging.info(f"Using configuration located at {args.config}")
    logging.info(f"Allowing curses to handle terminal setup")
    curses.wrapper(main, args)
