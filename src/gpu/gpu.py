"""
This files finds the system's gpus and load's them correctly

itg.py corresponds to Intel GPUs
nvml.py corresponds to Nvidia GPUs

TODO: Figure out what to do with AMD GPUs

"""
import ctypes as ct
import importlib as il
import importlib.machinery as mach
import os
import pathlib as pl
from enum import Enum, IntEnum, auto, unique
from inspect import getsourcefile
from typing import Any, Callable, DefaultDict, Dict, Tuple, Type, Union, List

nvml = il.import_module("nvml", ".")

@unique
class LibStatus(IntEnum):
    Unknown = -1
    Not_loaded = 0
    Loaded = 1
    Initialized = 2
    Shutdown = 3

    def __gt__(self, x) -> bool:
        if isinstance(x, LibStatus):
            return self.value > x.value
        else:
            return self.value > x

    def __lt__(self, x) -> bool:
        if isinstance(x, LibStatus):
            return self.value < x.value
        else:
            return self.value < x

    def __eq__(self, x) -> bool:
        if isinstance(x, LibStatus):
            return self.value == x.value
        else:
            return self.value == x

    def __ne__(self, x) -> bool:
        if isinstance(x, LibStatus):
            return not self.value == x.value
        else:
            return not self.value == x

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

class Library():
    def __init__(self, *args, **kwargs) -> None:
        self.library_name = "UNKNOWN LIBRARY"
        self._status = LibStatus(0)
        self._funcs: Dict[ct.CDLL, List[Callable[..., Any]]] = DefaultDict(list)
        self._libs: Dict[str, ct.CDLL] = {}
        self._init_funcs: Dict[ct.CDLL, List[str]] = DefaultDict(list)
        self._result = None
    
    def setup(self, libs: Dict[str, Union[str, os.PathLike]]) -> Dict[str, ct.CDLL]:
        assert self._status == LibStatus.Not_loaded, f"{self.library_name} can only be loaded once"

        for name, path in libs.items():
            if isinstance(path, str):
                self._libs[name] = ct.cdll.LoadLibrary(path)
            else:
                self._libs[name] = ct.CDLL(path)

    def initialize(self):
        pass

    def load_function(self, lib: ct.CDLL, function_name: str, arg_type: List[Type] = [], ret_type: Type = None):
        assert self.status >= LibStatus.Loaded, f"{self.library_name} has to be loaded before functions can be loaded"

        func = getattr(lib, function_name)
        func.argtype = arg_type
        func.restype = ret_type
        self._funcs[lib].append(func)

    def execute(self, lib: ct.CDLL, function_name: str, *args):
        if function_name not in self._init_funcs[lib]:
            assert self.status >= LibStatus.Initialized, f"{self.library_name} has to be initialized before functions can be executed"
            assert self.status < LibStatus.Shutdown, f"{self.library_name} can not be shutdown when executing functions"
        assert function_name in [x.__name__ for x in self._funcs[lib]], "Attempted execution of unknown function"
        
        func = [x for x in self._funcs[lib] if x.__name__ == function_name][0]
        self._result = func(*args)

    @property
    def status(self):
        return self._status
    @property
    def result(self) -> Any:
        return self._result

class Nvidia(GPU):
    def __init__(self, library, device_ptr: nvml.nvml_device_t, *args, **kwargs) -> None:
        super(Nvidia, self).__init__(*args, **kwargs)
        self._lib = library
        self._ptr = device_ptr

    @property
    def name(self) -> str:
        """The GPU's general name"""
        name = ct.create_string_buffer(64)
        self._lib.execute("nvmlDeviceGetName", self._ptr, name, ct.sizeof(name))
        return str(name.value, "ascii")
    @property
    def memory(self) -> Tuple[int, int, int]:
        """The GPU's current amount of free, total, and used memory respectively"""
        mem = nvml.nvml_memory_t()
        self._lib.execute("nvmlDeviceGetMemoryInfo", self._ptr, ct.byref(mem))
        return (mem.free, mem.total, mem.used)
    @property
    def temperature(self) -> int:
        """The GPU's current temperature in celsius"""
        temp = ct.c_uint(0)
        self._lib.execute("nvmlDeviceGetTemperature", self._ptr, nvml.nvml_temperature_sensors_t(0).value, ct.byref(temp))
        return temp.value
    @property
    def power(self) -> int:
        """The GPU's current powerdraw in milliwatts"""
        power = ct.c_uint(0)
        self._lib.execute("nvmlDeviceGetPowerUsage", self._ptr, ct.byref(power))
        return power.value
    @property
    def fan_speed(self) -> int:
        """The GPU's current fan speed as a percentage of the max fan speed"""
        fan_speed = ct.c_uint(0)
        self._lib.execute("nvmlDeviceGetFanSpeed", self._ptr, ct.byref(fan_speed))
        return fan_speed.value
    @property
    def clock_speed(self) -> Tuple[int, int]:
        """The GPU's current and max clock speed respectively"""
        cur_clock = ct.c_uint(0)
        max_clock = ct.c_uint(0)
        self._lib.execute("nvmlDeviceGetClockInfo", self._ptr, nvml.nvml_clock_type_t.NVML_CLOCK_GRAPHICS.value, ct.byref(cur_clock))
        self._lib.execute("nvmlDeviceGetMaxClockInfo", self._ptr, nvml.nvml_clock_type_t.NVML_CLOCK_GRAPHICS.value, ct.byref(max_clock))

        return cur_clock.value, max_clock.value
    @property
    def utilization(self) -> Tuple[int, int]:
        """The GPU's utilization since the last query"""
        util = nvml.nvml_utilization_t()
        self._lib.execute("nvmlDeviceGetUtilizationRates", self._ptr, ct.byref(util))

        return util.gpu, util.memory

class NVML(Library):
    def __init__(self, *args, **kwargs) -> None:
        super(NVML, self).__init__(*args, **kwargs)
        self.library_name = "NVML"
        self._created_devices = []

    def setup(self, path: Union[str, os.PathLike, None] = None):
        libs = {"libnvidia-ml.so": path or "libnvidia-ml.so"}
        super(NVML, self).setup(libs)
        self._lib = self._libs["libnvidia-ml.so"]
        self._status = LibStatus.Loaded

    def initialize(self):
        assert self.status >= LibStatus.Loaded, f"{self.library_name} has to be loaded before initialized"
        assert self.status != LibStatus.Initialized, f"{self.library_name} has already been initialized"
        assert self.status < LibStatus.Shutdown, f"{self.library_name} can not be initialized after shutdown"

        funcs = [
            "nvmlInit_v2",
            "nvmlDeviceGetCount_v2",
            "nvmlDeviceGetHandleByIndex_v2",
            "nvmlDeviceGetName",
            "nvmlDeviceGetMemoryInfo",
            "nvmlDeviceGetTemperature",
            "nvmlDeviceGetPowerUsage",
            "nvmlDeviceGetFanSpeed",
            "nvmlDeviceGetClockInfo",
            "nvmlDeviceGetMaxClockInfo",
            "nvmlDeviceGetUtilizationRates",
            "nvmlShutdown",
        ]

        self._init_funcs[self._lib].append(funcs[0])

        for func in funcs:
            self.load_function(func)

        self.execute("nvmlInit_v2")

        self._status = LibStatus.Initialized

    def shutdown(self):
        assert self.status > LibStatus.Loaded, f"{self.library_name} has to be loaded before it can be shutdown"
        assert self.status > LibStatus.Initialized, f"{self.library_name} has to be initialized before it can be shutdown"
        assert self.status != LibStatus.Shutdown, f"{self.library_name} has already been shutdown"

        self.execute("nvmlShutdown")

        self._status = LibStatus.Shutdown

    def load_function(self, function_name: str):
        super(NVML, self).load_function(self._lib, function_name, [], nvml.nvml_result_t)

    def execute(self, function_name: str, *args):
        super(NVML, self).execute(self._lib, function_name, *args)

        assert self.result == nvml.nvml_result_t.NVML_SUCCESS, f"Function {function_name}() returned {self.result.name}"

    def device(self, i: int = 0) -> Nvidia:
        assert self.status == LibStatus.Initialized, f"{self.library_name} has to be initialized before devices can be retrieved"
        assert i < self.device_count, "Requested device index is greater than the number of devices"

        device = nvml.nvml_device_t()
        self.execute("nvmlDeviceGetHandleByIndex_v2", ct.c_uint(i), ct.byref(device))
        self._created_devices.append(Nvidia(self, device))

        return self._created_devices[-1]

    @property
    def device_count(self) -> int:
        assert self.status == LibStatus.Initialized, f"{self.library_name} has to be initialized before device count is known"
        dev_count = ct.c_uint(0)
        self.execute("nvmlDeviceGetCount_v2", ct.byref(dev_count))
        return dev_count.value

def get_library(library_name: str):
    if library_name.upper() in _libraries:
        return _libraries[library_name.upper()]

    if library_name.upper() == "NVIDIA":
        lib = NVML()
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
