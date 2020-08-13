import argparse
import logging
import os
import json

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

class screen():
    def __init__(self, conf) -> None:
        self.term = bl.Terminal()
        self.tiles = ob.tile.from_conf(conf["screen"])

        print(self.tiles)

    def run(self):
        with self.term.fullscreen(), self.term.cbreak(), self.term.hidden_cursor():
            while 1:
                self.tiles.render(self.term)

                self.term.inkey()

def parse_config(conf: dict) -> list:
    tiles = []

    s = []
    ntv = [(conf["screen"], 0)]

    while ntv:
        cur, depth = ntv.pop()

        if "partitions" in cur:
            s.append(({k:v for k,v in cur["partitions"].items() if k != "screens"}, depth))
            ntv += [(x, depth + 1) for x in cur["partitions"]["screens"]]
        else:
            s.append((cur, depth))

    for i, (t, d) in enumerate(s[::-1], 1):
        idx = len(s) - i
        if "module" in t:
            tiles.append(tile_dict[t["module"]](t))
        else:
            j, k = idx+1, 0
            while j < len(s) and s[j][1] > d:
                j += 1
                k += 1

            meta_tiles[t["type"]](t, reversed(s[idx+1:j]))

    return tiles

def main(args):
    """
    1) Read the configuration data
    2) Create a reduced structure of all the different areas
    3) Validate that the configuration is correct
    4) Using configuration data, construct the different tiles
    """
    config: dict

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
