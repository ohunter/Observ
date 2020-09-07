import ctypes as ct
from ctypes import POINTER
import glob
import os
import pathlib
from enum import Enum
from typing import Any, Callable, Dict, Iterable, Type, Union


_nvml_result_t = ct.c_int
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

class nvml_device_t(ct.Structure):
    pass

class Device():
    def __init__(self, funcs: Iterable[Callable[..., Any]], args: Dict[str, Iterable[Any]]) -> None:
        self._funcs = funcs
        self._args = args

    @property
    def name(self):
        func = [x for x in self._funcs if x.__name__ == "nvmlDeviceGetName"][0]
        result = nvml_result_t(func(*self._args["nvmlDeviceGetName"]))
        assert result == nvml_result_t.NVML_SUCCESS, f"Function {func.__name__} returned with {result.name}"
        return str(self._args["nvmlDeviceGetName"][1].value, "ascii")
class NVML():
    def __init__(self) -> None:
        self._loaded = False
        self._initialized = False
        self._result: _nvml_result_t
        self._created_devices = []

    def setup(self, path: Union[str, os.PathLike, None] = None):
        assert not self.loaded, "NVML can only be loaded once"

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
        self._loaded = True

    def initialize(self):
        assert self.loaded, "NVML has to be loaded before initialized"
        assert not self.initialized, "NVML can only be initialized once"

        funcs = [
            self._lib.nvmlInit,
            self._lib.nvmlDeviceGetCount,
            self._lib.nvmlDeviceGetHandleByIndex,
            self._lib.nvmlDeviceGetName,
            self._lib.nvmlShutdown,
        ]

        for func in funcs:
            func.restype = _nvml_result_t

        self._result = nvml_result_t(self._lib.nvmlInit())

        assert self.result == nvml_result_t.NVML_SUCCESS, f"Function nvmlInit() returned {self.result.name}"

        self._initialized = True

    def shutdown(self):
        assert self.loaded, "NVML has to be loaded before being shutdown"
        assert self.initialized, "NVML has to be initialized before being shutdown"

        self._result = nvml_result_t(self._lib.nvmlShutdown())

        assert self.result == nvml_result_t.NVML_SUCCESS, f"Function nvmlShutdown() returned {self.result.name}"

        self.initialized = False

    def device(self, i: int = 0):
        assert self.loaded and self.initialized, "NVML has to be loaded and initialized before device count is known"
        assert i < self.device_count, "Requested device index is greater than the number of devices"

        device = nvml_device_t()
        self._result = nvml_result_t(self._lib.nvmlDeviceGetHandleByIndex(ct.c_uint(i), ct.byref(device)))

        assert self.result == nvml_result_t.NVML_SUCCESS, f"Function nvmlDeviceGetHandleByIndex() returned {self.result.name}"

        name = ct.create_string_buffer(64)

        funcs = [self._lib.nvmlDeviceGetName]
        args = {self._lib.nvmlDeviceGetName.__name__: [ct.byref(device), name, ct.sizeof(name)]}
        self._created_devices.append(Device(funcs, args))
        return self._created_devices[-1]

    @property
    def loaded(self) -> bool:
        return self._loaded
    @property
    def initialized(self) -> bool:
        return self._initialized
    @property
    def device_count(self) -> int:
        assert self.loaded and self.initialized, "NVML has to be loaded and initialized before device count is known"
        dev_count = ct.c_uint(0)
        self._result = nvml_result_t(self._lib.nvmlDeviceGetCount(ct.byref(dev_count)))

        assert self.result == nvml_result_t.NVML_SUCCESS, f"Function nvmlDeviceGetCount() returned {self.result.name}"
        return dev_count.value
    @property
    def result(self) -> _nvml_result_t:
        return self._result

if __name__ == "__main__":
    n = NVML()
    n.setup()
    n.initialize()
    dev = n.device(0)
    print(dev.name)
