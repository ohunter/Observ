"""
This files finds the system's gpus and load's them correctly

itg.py corresponds to Intel GPUs
nvml.py corresponds to Nvidia GPUs

TODO: Figure out what to do with AMD GPUs

"""
import os
from inspect import getsourcefile
from typing import Any, Dict, Tuple
import importlib.machinery as mach

class GPU():
    def __init__(self, *args, **kwargs) -> None:
        pass

    @property
    def name(self) -> str:
        """The GPU's general name"""
        raise NotImplementedError
    @property
    def memory(self) -> Tuple[int, int, int]:
        """The GPU's current amount of free, total, and used memory respectively"""
        raise NotImplementedError
    @property
    def temperature(self) -> int:
        """The GPU's current temperature in celsius"""
        raise NotImplementedError
    @property
    def power(self) -> int:
        """The GPU's current powerdraw in milliwatts"""
        raise NotImplementedError
    @property
    def fan_speed(self) -> int:
        """The GPU's current fan speed as a percentage of the max fan speed"""
        raise NotImplementedError
    @property
    def clock_speed(self) -> Tuple[int, int]:
        """The GPU's current and max clock speed respectively"""
        raise NotImplementedError
    @property
    def utilization(self) -> Tuple[int, int]:
        """The GPU's utilization since the last query"""
        raise NotImplementedError

def get_library(library_name: str):
    if library_name.upper() in _libraries:
        return _libraries[library_name.upper()]

    if library_name.upper() == "NVIDIA":
        nvml = mach.SourceFileLoader("nvml", f"{os.path.dirname(os.path.abspath(getsourcefile(lambda:0)))}/nvml.py").load_module()
        lib = nvml.NVML()
        lib.setup()
        lib.initialize()
        _libraries[library_name.upper()] = lib
        return lib
    elif library_name.upper() == "INTEL":
        raise NotImplementedError
    elif library_name.upper() == "AMD":
        raise NotImplementedError

_libraries: Dict[str, Any] = {}

if __name__ == "__main__":
    get_library("nvidia")