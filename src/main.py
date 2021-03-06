import argparse
import json
import logging
import os
import signal
from signal import SIGWINCH
from typing import Any, Mapping

import blessed as bl

import tiles as ti
import sched as sc

class screen():
    def __init__(self, conf: Mapping[str, Any]) -> None:
        self.term = bl.Terminal()

        self.root: ti.tile = ti.tile.from_conf(conf["screen"])

        self.sched = sc.scheduler(self.root.timing())

    def run(self) -> None:
        try:
            self.root.start_concurrent()
            with self.term.fullscreen(), self.term.cbreak(), self.term.hidden_cursor():
                for time, tiles in self.sched.next_timing():

                    inp = self.term.inkey(timeout=time)
                    if inp in ["q", "Q"]:
                        logging.info("Exit input recieved. Terminating...")
                        return

                    for tile in tiles:
                        tile.render(self.term)
        except BaseException as e:
            import traceback; traceback.print_exc()
            import pdb; pdb.set_trace()

    def redraw(self) -> None:
        self.root.redraw(self.term)

def main(args: argparse.Namespace) -> None:
    """
    The rough steps for creating the application layout:
        1) Read the configuration data
        2) Create a reduced structure of all the different areas
        3) Validate that the configuration is correct
        4) Using configuration data, construct the different tiles
    """
    config: dict
    scr: screen

    def sig_resize(sig, action) -> None:
        scr.redraw()

    signal.signal(SIGWINCH, sig_resize)

    logging.info("Loading configuration file")
    with open(args.config) as fi:
        config = json.load(fi)

    logging.info("Creating screen layout")
    scr = screen(config)

    scr.run()


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
        default=0,
        help="The level the logger will output for. Corresponds to 1/10 of the logging levels for python. Only works if the log flag is given."
    )

    parser.add_argument(
        "--debug",
        type=int,
        nargs='?',
        const=42069,
        help="Opens a port and waits for a debugger to attach to the process using debugpy. If no additional argument is specified, the default port is 42069"
    )

    args = parser.parse_args()

    args.log_level = 0 if not args.log_level else args.log_level

    if args.log:
        logging.basicConfig(level=args.log_level * 10, filename=args.log, filemode='w', format='%(asctime)s [%(levelname)s]\t%(message)s', datefmt='%d-%b-%y %H:%M:%S')
    else:
        logging.basicConfig(level=logging.CRITICAL+1)

    if args.debug:
        import debugpy
        debugpy.listen(('127.0.0.1', args.debug))
        debugpy.wait_for_client()

    logging.info("Starting application")
    logging.info(f"Using configuration located at {os.path.abspath(args.config)}")
    main(args)
