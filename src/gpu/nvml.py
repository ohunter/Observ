"""
This file takes care of all GPUs that can be monitored by NVidia's NVML library
"""

import ctypes as ct
from enum import Enum, IntEnum, auto, unique

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
