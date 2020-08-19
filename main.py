import argparse
import json
import logging
import os
import signal
from itertools import chain
from signal import SIGWINCH
from typing import Any, Iterable, Mapping, Tuple

import blessed as bl

import observ as ob

meta_tiles = {
    "tiled": ob.split.from_conf,
    "tabbed": ob.tabbed.from_conf,
}

tile_dict = {
    "line": ob.line_tile.from_conf,
    "text": ob.text_tile.from_conf,
}

class scheduler():
    def __init__(self, timing: Iterable[Tuple[int, ob.tile]]) -> None:
        period = self._find_period([x for x,v in timing])
        steps = [{i/k : v for i in range(1, int(period * k)+1)} for k, v in timing]
        self.timings = {x:[d[x] for d in steps if x in d] for x in dict.fromkeys(sorted([b for a in steps for b in a]))}

        self.total = 0.0
        self.t = 0.0
        self.dt = 0.0

    def next_timing(self):
        while 1:
            self.t %= max(self.timings)
            self.t += self.dt
            try:
                self.dt = min([x - self.t for x in self.timings if x > self.t])
            except ValueError:
                self.dt = min(self.timings)

            self.total += self.dt
            yield self.dt, self.timings.get(self.t, self.timings[max(self.timings)])

    def _factorize(self, val: int) -> Mapping[int, int]:
        factors = {}
        while val > 1:
            for i in range(2, val+1):
                if val % i == 0:
                    factors[i] = factors[i] + 1 if i in factors else 1
                    val //= i
                    break
        return factors

    def _lcm(self, vals: Iterable[int]) -> int:
        lcm = 1
        factors = [self._factorize(round(x)) for x in vals]
        lcm_factors = {k: max([d.get(k, 0) for d in factors]) for k in dict.fromkeys([y for x in factors for y in x.keys()]).keys()}
        [lcm := lcm * k ** v for k,v in lcm_factors.items()]
        return lcm

    def _gcd(self, vals: Iterable[int]) -> int:
        gcd = 1
        factors = [self._factorize(round(x)) for x in vals]
        gcd_factors = {k: min([d.get(k, 0) for d in factors]) for k in dict.fromkeys([y for x in factors for y in x.keys()]).keys()}
        [gcd := gcd * k ** v for k,v in gcd_factors.items()]
        return gcd

    def _find_period(self, vals: Iterable[int]) -> float:
        return 1/self._gcd(vals)

    def __iter__(self):
        return self.next_timing()

    def __next__(self):
        return self.next_timing()

class screen():
    def __init__(self, conf: Mapping[str, Any]) -> None:
        self.term = bl.Terminal()

        self.root: ob.tile = ob.tile.from_conf(conf["screen"])
        self.active = self.root.select((0,0), self.term)

        self.sched = scheduler(self.root.timing())

        self.actions = {
            "KEY_UP" :    lambda pos, delta: (pos[0], max(0, pos[1] - delta[1])),
            "KEY_DOWN" :  lambda pos, delta: (pos[0], min(1, pos[1] + delta[1])),
            "KEY_LEFT" :  lambda pos, delta: (max(0, pos[0] - delta[0]), pos[1]),
            "KEY_RIGHT" : lambda pos, delta: (min(1, pos[0] + delta[0]), pos[1]),
        }

    def run(self) -> None:
        with self.term.fullscreen(), self.term.cbreak(), self.term.hidden_cursor():
            for time, tiles in self.sched.next_timing():

                inp = self.term.inkey(timeout=time)
                if inp in ["q", "Q"]:
                    return
                elif inp.name in ["KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT"]:
                    # Note: Once Python 3.9 comes out switch to using `math.nextafter` to figure out the next tile in a direction
                    pos = (self.active.origin[0] + (self.active.offset[0] - self.active.origin[0])/2, self.active.origin[1] + (self.active.offset[1] - self.active.origin[1])/2)
                    delta = ((self.active.offset[0] - self.active.origin[0])/2 + 0.1, (self.active.offset[1] - self.active.origin[1])/2 + 0.1)
                    self.active.deselect(self.term)
                    self.active = self.root.select(self.actions[inp.name](pos, delta), self.term)

                for tile in tiles:
                    tile.render(self.term)

    def redraw(self) -> None:
        self.root.redraw(self.term)

def main(args):
    """
    The rough steps for creating the application layout:
        1) Read the configuration data
        2) Create a reduced structure of all the different areas
        3) Validate that the configuration is correct
        4) Using configuration data, construct the different tiles
    """
    config: dict
    scr: screen

    def sig_resize(sig, action):
        scr.redraw()

    signal.signal(SIGWINCH, sig_resize)

    logging.info("Loading configuration file")
    with open(args.config) as fi:
        config = json.load(fi)

    scr = screen(config)

    try:
        scr.run()
    except BaseException as e:
        import traceback; traceback.print_exc()
        import pdb; pdb.set_trace()

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
    main(args)
