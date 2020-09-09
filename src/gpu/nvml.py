"""
This file takes care of all GPUs that can be monitored by NVidia's NVML library
"""

import importlib as il
import ctypes as ct
import glob
import os
import pathlib
from enum import Enum, IntEnum, auto, unique
from typing import Callable, Dict, Tuple, Union

gpu = il.import_module("gpu", ".")

### Enums
class nvml_result_t(Enum):
    NVML_SUCCESS = 0
    NVML_ERROR_UNINITIALIZED = 1
    NVML_ERROR_INVALID_ARGUMENT = 2
    NVML_ERROR_NOT_SUPPORTED = 3
    NVML_ERROR_NO_PERMISSION = 4
    NVML_ERROR_ALREADY_INITIALIZED = 5
    NVML_ERROR_NOT_FOUND = 6
    NVML_ERROR_INSUFFICIENT_SIZE = 7
    NVML_ERROR_INSUFFICIENT_POWER = 8
    NVML_ERROR_DRIVER_NOT_LOADED = 9
    NVML_ERROR_TIMEOUT = 10
    NVML_ERROR_IRQ_ISSUE = 11
    NVML_ERROR_LIBRARY_NOT_FOUND = 12
    NVML_ERROR_FUNCTION_NOT_FOUND = 13
    NVML_ERROR_CORRUPTED_INFOROM = 14
    NVML_ERROR_GPU_IS_LOST = 15
    NVML_ERROR_RESET_REQUIRED = 16
    NVML_ERROR_OPERATING_SYSTEM = 17
    NVML_ERROR_LIB_RM_VERSION_MISMATCH = 18
    NVML_ERROR_IN_USE = 19
    NVML_ERROR_MEMORY = 20
    NVML_ERROR_NO_DATA = 21
    NVML_ERROR_VGPU_ECC_NOT_SUPPORTED = 22
    NVML_ERROR_INSUFFICIENT_RESOURCES = 23
    NVML_ERROR_UNKNOWN = 999

class nvml_temperature_sensors_t(Enum):
    NVML_TEMPERATURE_GPU = 0
    NVML_TEMPERATURE_COUNT = auto()

class nvml_clock_type_t(Enum):
    NVML_CLOCK_GRAPHICS = 0
    NVML_CLOCK_SM = 1
    NVML_CLOCK_MEM = 2
    NVML_CLOCK_VIDEO = 3
    NVML_CLOCK_COUNT = auto()

### Structures
class nvml_device_t_struct(ct.Structure):
    pass
nvml_device_t = ct.POINTER(nvml_device_t_struct)

class nvml_memory_t(ct.Structure):
    _fields_ = [
        ("free", ct.c_ulonglong),
        ("total", ct.c_ulonglong),
        ("used", ct.c_ulonglong)
    ]

class nvml_utilization_t(ct.Structure):
    _fields_ = [
        ("gpu", ct.c_uint),
        ("memory", ct.c_uint)
    ]
@unique
class NVML_STATUS(IntEnum):
    Unknown = 0
    Loaded = 1
    Initialized = 2
    Shutdown = 3

    def __gt__(self, x) -> bool:
        if isinstance(x, NVML_STATUS):
            return self.value > x.value
        else:
            return self.value > x

    def __lt__(self, x) -> bool:
        if isinstance(x, NVML_STATUS):
            return self.value < x.value
        else:
            return self.value < x

    def __eq__(self, x) -> bool:
        if isinstance(x, NVML_STATUS):
            return self.value == x.value
        else:
            return self.value == x

    def __ne__(self, x) -> bool:
        if isinstance(x, NVML_STATUS):
            return not self.value == x.value
        else:
            return not self.value == x

class Nvidia(gpu.GPU):
    def __init__(self, library, device_ptr: nvml_device_t, *args, **kwargs) -> None:
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
        mem = nvml_memory_t()
        self._lib.execute("nvmlDeviceGetMemoryInfo", self._ptr, ct.byref(mem))
        return (mem.free, mem.total, mem.used)
    @property
    def temperature(self) -> int:
        """The GPU's current temperature in celsius"""
        temp = ct.c_uint(0)
        self._lib.execute("nvmlDeviceGetTemperature", self._ptr, nvml_temperature_sensors_t(0).value, ct.byref(temp))
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
        self._lib.execute("nvmlDeviceGetClockInfo", self._ptr, nvml_clock_type_t.NVML_CLOCK_GRAPHICS.value, ct.byref(cur_clock))
        self._lib.execute("nvmlDeviceGetMaxClockInfo", self._ptr, nvml_clock_type_t.NVML_CLOCK_GRAPHICS.value, ct.byref(max_clock))

        return cur_clock.value, max_clock.value
    @property
    def utilization(self) -> Tuple[int, int]:
        """The GPU's utilization since the last query"""
        util = nvml_utilization_t()
        self._lib.execute("nvmlDeviceGetUtilizationRates", self._ptr, ct.byref(util))

        return util.gpu, util.memory

class NVML():
    def __init__(self) -> None:
        self._status = NVML_STATUS(0)
        self._result: nvml_result_t(0)
        self._created_devices = []
        self._funcs: Dict[str, Callable[..., nvml_result_t]] = {}

    def setup(self, path: Union[str, os.PathLike, None] = None):
        assert self.status == NVML_STATUS(0), "NVML can only be loaded once"

        self._path: os.PathLike
        if isinstance(path, str):
            self._path = pathlib.Path(path)
        elif path == None:
            import platform
            cur_dir = os.getcwd()
            os.chdir('/usr/lib')
            paths = [pathlib.Path(x).resolve() for x in glob.glob('**/libnvidia-ml.so', recursive=True)]
            os.chdir(cur_dir)
            assert paths != [], "libnvidia-ml.so could not be located."

            self._path = [x for x in paths if any([y for y in x.parts if platform.machine() in y])][0] or paths[0]
        else:
            self._path = path

        self._lib = ct.CDLL(self._path)
        self._status += 1

    def initialize(self):
        assert self.status > NVML_STATUS(0), "NVML has to be loaded before initialized"
        assert self.status != NVML_STATUS(2), "NVML has already been initialized"
        assert self.status < NVML_STATUS(3), "NVML can not be initialized after shutdown"

        for func in [
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
        ]:
            self.load_function(func)

        self.execute("nvmlInit_v2")

        self._status += 1

    def shutdown(self):
        assert self.status > NVML_STATUS(0), "NVML has to be loaded before it can be shutdown"
        assert self.status > NVML_STATUS(2), "NVML has to be initialized before it can be shutdown"
        assert self.status != NVML_STATUS(3), "NVML has already been shutdown"

        self.execute("nvmlShutdown")

        self._status += 1

    def load_function(self, function_name: str):
        assert self.status >= NVML_STATUS(1), "NVML has to be loaded before functions can be loaded"
        func = getattr(self._lib, function_name)
        func.restype = nvml_result_t
        self._funcs[func.__name__] = func

    def execute(self, function_name: str, *args):
        if not function_name.startswith("nvmlInit"):
            assert self.status == NVML_STATUS(2), "NVML has to be initialized before functions can be executed"
            assert self.status < NVML_STATUS(3), "NVML can not be shutdown when executing functions"
        assert function_name in self._funcs, "Attempted execution of unknown function"

        self._result = nvml_result_t(self._funcs[function_name](*args))

        assert self.result == nvml_result_t.NVML_SUCCESS, f"Function {function_name}() returned {self.result.name}"

    def device(self, i: int = 0) -> Nvidia:
        assert self.status == NVML_STATUS(2), "NVML has to be initialized before devices can be retrieved"
        assert i < self.device_count, "Requested device index is greater than the number of devices"

        device = nvml_device_t()
        self.execute("nvmlDeviceGetHandleByIndex_v2", ct.c_uint(i), ct.byref(device))
        self._created_devices.append(Nvidia(self, device))

        return self._created_devices[-1]

    @property
    def status(self):
        return self._status
    @property
    def device_count(self) -> int:
        assert self.status == NVML_STATUS(2), "NVML has to be initialized before device count is known"
        dev_count = ct.c_uint(0)
        self.execute("nvmlDeviceGetCount_v2", ct.byref(dev_count))
        return dev_count.value
    @property
    def result(self) -> nvml_result_t:
        return self._result

if __name__ == "__main__":
    n = NVML()
    n.setup()
    n.initialize()
    dev = n.device(0)
    print(dev.name)
    print(dev.memory)
    print(dev.temperature)
    print(dev.power)
    print(dev.fan_speed)
    print(dev.clock_speed)
    print(dev.utilization)