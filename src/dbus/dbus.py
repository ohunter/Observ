import ctypes
import os
import glob
import pathlib
from typing import Union

import custom_types as ct

class dbus():
    def __init__(self) -> None:
        self._lib: ctypes.CDLL
        self._loaded = False
        self._connected = False

    @property
    def lib(self):
        return self._lib
    @property
    def loaded(self):
        return self._loaded
    @property
    def connected(self):
        return self._connected
    @property
    def connected(self):
        return self._connected

    def setup(self, path: Union[str, pathlib.Path] = None) -> None:
        dbus_path: pathlib.Path

        if isinstance(path, str):
            dbus_path = pathlib.Path(path)
        elif isinstance(path, pathlib.Path):
            dbus_path = path
        else:
            cur_dir = os.getcwd()
            os.chdir("/usr/lib")
            dbus_path = pathlib.Path(glob.glob("**/libdbus-1.so", recursive=True)[0]).absolute()
            os.chdir(cur_dir)

        self._lib = ctypes.CDLL(dbus_path)
        self._loaded = True

        self.lib.dbus_error_init.restype = ct.dbus_error
        self.lib.dbus_bus_get.restype = 

    def connect(self) -> None:
        assert self.loaded == True, "DBus has to be loaded before a connection can be established. Try calling setup()."

if __name__ == "__main__":
    d = dbus()