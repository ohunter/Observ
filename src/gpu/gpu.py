"""
This files finds the system's gpus and load's them correctly

itg.py corresponds to Intel GPUs
nvml.py corresponds to Nvidia GPUs

TODO: Figure out what to do with AMD GPUs

"""

from collections import defaultdict
from typing import Dict, List, Tuple

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

# def locate_gpus(paths: Dict[str, str] = defaultdict(None)) -> List[GPU]:
#     from . import nvml
#     from . import itg
#     nv_lib = nvml.NVML()

#     try:
#         nv_lib.setup(paths["NVidia"])
#     except AssertionError:
#         # There is no Nvidia library so nvidia cards cant be monitored
#         pass
