"""
This files finds the system's gpus and load's them correctly

itg.py corresponds to Intel GPUs
nvml.py corresponds to Nvidia GPUs

TODO: Figure out what to do with AMD GPUs

"""
import ctypes as ct
import os
from enum import IntEnum, unique
from importlib.machinery import SourceFileLoader
from inspect import getsourcefile
from typing import Any, Callable, DefaultDict, Dict, List, Tuple, Type, Union

nvml = SourceFileLoader("nvml", f"{os.path.dirname(os.path.abspath(getsourcefile(lambda:0)))}/nvml.py").load_module()
igt = SourceFileLoader("igt", f"{os.path.dirname(os.path.abspath(getsourcefile(lambda:0)))}/igt.py").load_module()

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

    def initialize(self) -> None:
        pass

    def load_function(self, lib: ct.CDLL, function_name: str, arg_type: List[Type] = [], ret_type: Type = None) -> None:
        assert self.status >= LibStatus.Loaded, f"{self.library_name} has to be loaded before functions can be loaded"

        func = getattr(lib, function_name)
        func.argtype = arg_type
        func.restype = ret_type
        self._funcs[lib].append(func)

    def execute(self, lib: ct.CDLL, function_name: str, *args) -> None:
        if function_name not in self._init_funcs[lib]:
            assert self.status >= LibStatus.Initialized, f"{self.library_name} has to be initialized before functions can be executed"
            assert self.status < LibStatus.Shutdown, f"{self.library_name} can not be shutdown when executing functions"
        assert function_name in [x.__name__ for x in self._funcs[lib]], "Attempted execution of unknown function"
        
        func = [x for x in self._funcs[lib] if x.__name__ == function_name][0]
        self._result = func(*args)

    @property
    def status(self) -> LibStatus:
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

    def setup(self, path: Union[str, os.PathLike, None] = None) -> None:
        libs = {"libnvidia-ml.so": path or "libnvidia-ml.so"}
        super(NVML, self).setup(libs)
        self._lib = self._libs["libnvidia-ml.so"]
        self._status = LibStatus.Loaded

    def initialize(self) -> None:
        assert self.status >= LibStatus.Loaded, f"{self.library_name} has to be loaded before initialized"
        assert self.status != LibStatus.Initialized, f"{self.library_name} has already been initialized"
        assert self.status < LibStatus.Shutdown, f"{self.library_name} can not be initialized after shutdown"

        funcs = [
            ("nvmlInit_v2",
                [],
                nvml.nvml_result_t),
            ("nvmlDeviceGetCount_v2",
                [ct.POINTER(ct.c_uint)],
                nvml.nvml_result_t),
            ("nvmlDeviceGetHandleByIndex_v2",
                [ct.c_uint, ct.POINTER(nvml.nvml_device_t)],
                nvml.nvml_result_t),
            ("nvmlDeviceGetName",
                [nvml.nvml_device_t, ct.c_char_p, ct.c_uint],
                nvml.nvml_result_t),
            ("nvmlDeviceGetMemoryInfo",
                [nvml.nvml_device_t, ct.POINTER(nvml.nvml_memory_t)],
                nvml.nvml_result_t),
            ("nvmlDeviceGetTemperature",
                [nvml.nvml_device_t, nvml.nvml_temperature_sensors_t, ct.POINTER(ct.c_uint)],
                nvml.nvml_result_t),
            ("nvmlDeviceGetPowerUsage",
                [nvml.nvml_device_t, ct.POINTER(ct.c_uint)],
                nvml.nvml_result_t),
            ("nvmlDeviceGetFanSpeed",
                [nvml.nvml_device_t, ct.POINTER(ct.c_uint)],
                nvml.nvml_result_t),
            ("nvmlDeviceGetClockInfo",
                [nvml.nvml_device_t, nvml.nvml_clock_type_t, ct.POINTER(ct.c_uint)],
                nvml.nvml_result_t),
            ("nvmlDeviceGetMaxClockInfo",
                [nvml.nvml_device_t, nvml.nvml_clock_type_t, ct.POINTER(ct.c_uint)],
                nvml.nvml_result_t),
            ("nvmlDeviceGetUtilizationRates",
                [nvml.nvml_device_t, ct.POINTER(nvml.nvml_utilization_t)],
                nvml.nvml_result_t),
            ("nvmlShutdown",
                [],
                nvml.nvml_result_t),
        ]

        self._init_funcs[self._lib].append(funcs[0][0])

        for func, args, ret in funcs:
            self.load_function(self._lib, func, args, ret)

        self.execute("nvmlInit_v2")

        self._status = LibStatus.Initialized

    def shutdown(self) -> None:
        assert self.status > LibStatus.Loaded, f"{self.library_name} has to be loaded before it can be shutdown"
        assert self.status > LibStatus.Initialized, f"{self.library_name} has to be initialized before it can be shutdown"
        assert self.status != LibStatus.Shutdown, f"{self.library_name} has already been shutdown"

        self.execute("nvmlShutdown")

        self._status = LibStatus.Shutdown

    def execute(self, function_name: str, *args) -> None:
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

class Intel(GPU):
    pass

class IGT(Library):
    def __init__(self, *args, **kwargs) -> None:
        super(IGT, self).__init__(*args, **kwargs)
        self.library_name = "IGT"

    def setup(self) -> None:
        libs = {
            "libudev.so" : "libudev.so",
            "libglib.so" : "libglib.so"
            }
        super(IGT, self).setup(libs)
        self._status = LibStatus.Loaded

    def initialize(self) -> None:
        # Load the neccessary functions

        self._igt_devices = igt.igt_devs_struct()
        udev = self._libs["libudev.so"]
        udev_funcs = [
            ("udev_new",
                [],
                igt.udev),
            ("udev_enumerate_new",
                [igt.udev],
                igt.udev_enumerate),
            ("udev_enumerate_add_match_subsystem",
                [igt.udev_enumerate, ct.c_char_p],
                ct.c_int),
            ("udev_enumerate_add_match_property",
                [igt.udev_enumerate, ct.c_char_p, ct.c_char_p],
                ct.c_int),
            ("udev_enumerate_scan_devices",
                [igt.udev_enumerate],
                ct.c_int),
            ("udev_enumerate_get_list_entry",
                [igt.udev_enumerate],
                ct.c_int),
            ("udev_list_entry_get_next",
                [igt.udev_list_entry],
                igt.udev_list_entry)
            ("udev_list_entry_get_name",
                [igt.udev_list_entry],
                ct.c_char_p),
            ("udev_device_new_from_syspath",
                [igt.udev, ct.c_char_p],
                igt.udev_device),
        ]

        # TODO: Import all the right glib functions

        glib = self._libs["libglib.so"]
        glib_funcs = [
            ("g_hash_table_new_full",
                [],
                igt.glib_ghashtable),
        ]

        for func, args, ret in udev_funcs:
            self.load_function(udev, func, args, ret)

        self._status = LibStatus.Initialized

        import pdb; pdb.set_trace()

    def execute(self, lib: ct.CDLL, function_name: str, *args) -> None:
        super(IGT, self).execute(lib, function_name, *args)

        if lib == self._libs["libudev.so"]:
            assert self.result != None, f"Udev function {function_name}() returned invalid pointer"

    def _scan_devices(self, force: bool) -> None:
        if force and self._igt_devices.devs_scanned:
            import pdb; pdb.set_trace()

        if self._igt_devices.devs_scanned:
            return

        self.__prep_scan()
        self.__scan_drm_devices()

        self._igt_devices.devs_scanned = True

    def __prep_scan(self):
        self.___igt_init_list_head(ct.byref(self._igt_devices.all))
        self.___igt_init_list_head(ct.byref(self._igt_devices.filtered))

    def __scan_drm_devices(self):
        lib = self._libs["libudev.so"]
        
        self.execute(lib, "udev_new")
        udev = self.result

        self.execute(lib, "udev_enumerate_new", ct.byref(udev))
        udev_enum = self.result

        self.execute(udev, "udev_enumerate_add_match_subsystem", udev_enum, "drm".encode('ascii'))
        assert self.result >= 0, f"Udev function udev_enumerate_add_match_subsystem() returned invalid integer"

        self.execute(udev, "udev_enumerate_add_match_property", udev_enum, "DEVNAME".encode('ascii'), "/dev/dri/*".encode('ascii'))
        assert self.result >= 0, f"Udev function udev_enumerate_add_match_property() returned invalid integer"

        self.execute(udev, "udev_enumerate_scan_devices", udev_enum)
        assert self.result >= 0, f"Udev function udev_enumerate_scan_devices() returned invalid integer"

        self.execute(udev, "udev_enumerate_get_list_entry", udev_enum)
        if not self.result:
            return
        devices = self.result

        dev_list_entry = devices

        while dev_list_entry:
            path = ct.c_char_p()
            udev_dev = igt.udev_device()
            idev = igt.igt_device_struct()

            self.execute(lib, "udev_list_entry_get_name", dev_list_entry)
            path = self.result

            self.execute(lib, "udev_device_new_from_syspath", udev, path)
            udev_dev = self.result

            

            self.execute(udev, "udev_list_entry_get_next", dev_list_entry)
            dev_list_entry = self.result

    def ___igt_init_list_head(self, lst: ct.POINTER(igt.igt_list_head)):
        lst.prev = lst
        lst.next = lst

    def ___igt_device_new_from_udev(self, dev: igt.udev_device):
        idev = 0

    def ____igt_device_new(self) -> igt.igt_device_struct:
        dev = igt.igt_device_struct()
        dev.atters_ht = 


def get_library(library_name: str) -> Library:
    if library_name.upper() in _libraries:
        return _libraries[library_name.upper()]

    lib: Library = None

    if library_name.upper() == "NVIDIA":
        lib = NVML()
    elif library_name.upper() == "INTEL":
        lib = IGT()
    elif library_name.upper() == "AMD":
        raise NotImplementedError
    else:
        raise NotImplementedError
    lib.setup()
    lib.initialize()

    _libraries[library_name.upper()] = lib
    return lib


_libraries: Dict[str, Any] = {}



if __name__ == "__main__":
    tmp = get_library("Intel")
    import pdb; pdb.set_trace()
