"""
This file takes care of all GPUs that can be monitored the same way as Intel GPU Top.
It is purely based upon the following files:

    - https://github.com/freedesktop/xorg-intel-gpu-tools/blob/master/tools/intel_gpu_top.c

    - https://github.com/freedesktop/xorg-intel-gpu-tools/blob/master/include/drm-uapi/i915_drm.h

    - https://github.com/freedesktop/xorg-intel-gpu-tools/blob/master/lib/igt_device_scan.c

    - https://github.com/freedesktop/xorg-intel-gpu-tools/blob/master/lib/igt_list.c

All licensing that applies to these files applies to this as well.

"""

import ctypes as ct
import os
from enum import IntEnum, unique

# C Structs

# Udev Structs

class udev_struct(ct.Structure):
    pass
udev = ct.POINTER(udev_struct)

class udev_enumerate_struct(ct.Structure):
    pass
udev_enumerate = ct.POINTER(udev_enumerate_struct)

class udev_list_entry_struct(ct.Structure):
    pass
udev_list_entry = ct.POINTER(udev_list_entry_struct)

class udev_device_struct(ct.Structure):
    pass
udev_device = ct.POINTER(udev_device_struct)

# Glib Structs

class glib_ghashtable_struct(ct.Structure):
    pass
glib_ghashtable = ct.POINTER(glib_ghashtable_struct)

# Intel Structs

class igt_list_head(ct.Structure):
    pass

igt_list_head._fields_ = [
    ("prev", ct.POINTER(igt_list_head)),
    ("next", ct.POINTER(igt_list_head)),
]

class igt_devs_struct(ct.Structure):
    _fields_ = [
        ("all", igt_list_head),
        ("filtered", igt_list_head),
        ("devs_scanned", ct.c_bool),
    ]

class igt_device_struct(ct.Structure):
    pass

igt_device_struct._fields_ = [
    ("parent", ct.POINTER(igt_device_struct)),
    ("props_ht", glib_ghashtable),
    ("attrs_ht", glib_ghashtable),
    ("subsystem", ct.c_char_p),
    ("syspath", ct.c_char_p),
    ("devnode", ct.c_char_p),
    ("drm_card", ct.c_char_p),
    ("drm_render", ct.c_char_p),
    ("vendor", ct.c_char_p),
    ("device", ct.c_char_p),
    ("pci_slot_name", ct.c_char_p),
    ("link", igt_list_head),
]

# Intel definitions

# engine_ptr = lambda engines, n : ct.pointer(engines.contents.engine) + n
# is_igpu_pci = lambda x : x == "0000:00:02.0"
# is_igpu = lambda x : x == "i915"

# RAPL_ROOT  = "/sys/devices/power/"
# RAPL_EVENT = "/sys/devices/power/events/"
# IMC_ROOT   = "/sys/devices/uncore_imc/"
# IMC_EVENT  = "/sys/devices/uncore_imc/events/"
# IMC_ROOT   = "/sys/devices/uncore_imc/"
# IMC_EVENT  = "/sys/devices/uncore_imc/events/"

# def _open_pmu(type, cnt, pmu, fd):
#     # Look on line 445 in `intel_gpu_top.c`
#     import pdb; pdb.set_trace()

# def _open_imc(type, pmu, fd):
#     # Look on line 460 in `intel_gpu_top.c`
#     import pdb; pdb.set_trace()

# # STANDARD C TYPE EXTENSIONS

# class C_DIR(ct.Structure):
#     pass
# DIR = ct.POINTER(C_DIR)

# class dirent(ct.Structure):
#     _fields_ = [
#         ("d_ino", ct.c_uint),
#         ("off_t", ct.c_int),
#         ("d_reclen", ct.c_ushort),
#         ("d_type", ct.c_ubyte),
#         ("d_name", ct.create_string_buffer(256)),
#     ]

# # Intel GPU Top Types

# class pmu_pair(ct.Structure):
#     _fields_ = [
#         ("cur", ct.c_uint64),
#         ("free", ct.c_uint64),
#     ]

# class pmu_counter(ct.Structure):
#     _fields_ = [
#         ("present", ct.c_bool),
#         ("config", ct.c_uint64),
#         ("idx", ct.c_uint),
#         ("val", pmu_pair),
#     ]

# class engine(ct.Structure):
#     _fields_ = [
#         ("name", ct.c_char_p),
#         ("display_name", ct.c_char_p),
#         ("short_name", ct.c_char_p),
#         ("class", ct.c_uint),
#         ("instance", ct.c_uint),
#         ("num_counters", ct.c_uint),
#         ("busy", pmu_counter),
#         ("wait", pmu_counter),
#         ("sema", pmu_counter),
#     ]

#     @classmethod
#     def cmp(a: ct.c_void_p, b: ct.c_void_p):
#         _a = ct.cast(a, ct.POINTER(engine))
#         _b = ct.cast(b, ct.POINTER(engine))

#         if _a.contents.class != _b.contents.class:
#             return _a.contents.class - _b.contents.class
#         else:
#             return _a.contents.instance - _b.contents.instance

# class engines(ct.Structure):
#     _fields_ = [
#         ("num_engines", ct.c_uint),
#         ("num_counters", ct.c_uint),
#         ("root", DIR),
#         ("ts", pmu_pair),
#         ("rapl_fd", ct.c_int),
#         ("rapl_scale", ct.c_double),
#         ("rapl_unit", ct.c_char_p),
#         ("freq_req", pmu_counter),
#         ("freq_act", pmu_counter),
#         ("irq", pmu_counter),
#         ("rc6", pmu_counter),
#         ("rapl", pmu_counter),
#         ("imc_reads", pmu_counter),
#         ("imc_writes", pmu_counter),
#         ("discrete", ct.c_bool),
#         ("device", ct.c_char_p),
#         ("engine", engine),
#     ]

# class igt_list_head(ct.Structure):
#     pass

# igt_list_head._fields_ = [
#     ("prev", ct.POINTER(igt_list_head)),
#     ("next", ct.POINTER(igt_list_head)),
# ]

# class igt_devs(ct.Structure):
#     _fields_ = [
#         ("all", igt_list_head),
#         ("filtered", igt_list_head),
#         ("devs_scanned", ct.c_bool),
#     ]

# @unique
# class drm_i915_engine_class(IntEnum):
#     I915_ENGINE_CLASS_INVALID = -1
#     I915_ENGINE_CLASS_RENDER = 0
#     I915_ENGINE_CLASS_COPY = 1
#     I915_ENGINE_CLASS_VIDEO = 2
#     I915_ENGINE_CLASS_VIDEO_ENHANCE = 3

# def get_pmu_config(dir_fd : ct.c_int, name : ct.c_char_p, counter: ct.c_char_p) -> ct.c_uint:
#     buf = ct.create_string_buffer(128)
#     p = ct.c_char_p()

#     fd = ct.c_int(0)
#     ret = ct.c_int(0)

#     if ct.sizeof(buf) > len(f"{name}-{counter}"):
#         return ct.c_uint(-1)
    
#     assert os.open in os.supports_dir_fd, "Operating system does not support directory file descriptors"

#     with os.open(buf.value, flags='r', dir_fd= dir_fd) as fd:
#         import pdb; pdb.set_trace()

#     for c in buf:
#         if c == '0':
#             p = ct.byref(c)
#             break
    
#     return ct.c_uint64(int(p.value))

# def class_display_name(_class: ct.c_uint) -> str:
#     class_dict = {
#         drm_i915_engine_class.I915_ENGINE_CLASS_RENDER: "Render/3D",
#         drm_i915_engine_class.I915_ENGINE_CLASS_COPY: "Blitter",
#         drm_i915_engine_class.I915_ENGINE_CLASS_VIDEO: "Video",
#         drm_i915_engine_class.I915_ENGINE_CLASS_VIDEO_ENHANCE: "VideoEnhance",
#     }

#     return class_dict.get(_class.value, "[unknown]")

# def class_short_name(_class: ct.c_uint) -> str:
#     class_dict = {
#         drm_i915_engine_class.I915_ENGINE_CLASS_RENDER: "RCS",
#         drm_i915_engine_class.I915_ENGINE_CLASS_COPY: "BCS",
#         drm_i915_engine_class.I915_ENGINE_CLASS_VIDEO: "VCS",
#         drm_i915_engine_class.I915_ENGINE_CLASS_VIDEO_ENHANCE: "VECS",
#     }

#     return class_dict.get(_class.value, "UNKN")

# def discover_engines(device: ct.c_char_p) -> ct.pointer(engines):
#     sysfs_root = ct.create_string_buffer(4096)
#     _engines: ct.pointer(engines)
#     _dirent: ct.pointer(dirent)
#     d = DIR()
#     ret = ct.c_int(0)

#     # Continue from line 193 in `intel_gpu_top.c`

#     import pdb; pdb.set_trace()

# def filename_to_str(filename: ct.c_char_p) -> str:
#     with open(filename.value, 'r') as fd:
#         # Continue from line 304 in `intel_gpu_top.c`
#         import pdb; pdb.set_trace()

# def filename_to_u64(filename: ct.c_char_p, base: int) -> int:
#     buf = filename_to_str(filename)

#     assert buf != 0, "Unknown error with Intel GPU in function: filename_to_u64()"

#     # Continue from line 337 in `intel_gpu_top.c`
#     import pdb; pdb.set_trace()

# def filename_to_double(filename: ct.c_char_p) -> float:
#     buf = filename_to_str(filename)

#     assert buf != 0, "Unknown error with Intel GPU in function: filename_to_double()"

#     # Continue from line 352 in `intel_gpu_top.c`
#     import pdb; pdb.set_trace()

# def rapl_type_id() -> int:
#     return filename_to_u64(RAPL_ROOT + "type", 10)

# def rapl_gpu_power() -> int:
#     return filename_to_u64(RAPL_EVENT + "energy-gpu", 0)

# def rapl_gpu_power_scale() -> float:
#     return filename_to_double(RAPL_EVENT + "energy-gpu.scale")

# def rapl_gpu_power_unit() -> str:
#     buf = filename_to_str(RAPL_EVENT + "energy-gpu.unit")

#     assert buf != 0, "Unknown error with Intel GPU in function: rapl_gpu_power_unit()"

#     if buf != "Joules":
#         return "Watts"
    
#     return buf

# def imc_type_id() -> int:
#     return filename_to_u64(IMC_ROOT + "type", 10)

# def imc_data_reads() -> int:
#     return filename_to_u64(IMC_EVENT + "data_reads", 0)

# def imc_data_reads_scale() -> float:
#     return filename_to_double(IMC_EVENT + "data_reads.scale")

# def imc_data_reads_unit() -> str:
#     buf = filename_to_str(IMC_EVENT + "data_reads.unit")

#     assert buf != 0, "Unknown error with Intel GPU in function: imc_data_reads_unit()"
    
#     return buf

# def imc_data_writes() -> int:
#     return filename_to_u64(IMC_EVENT + "data_writes", 0)

# def imc_data_writes_scale() -> float:
#     return filename_to_double(IMC_EVENT + "data_writes.scale")

# def imc_data_writes_unit() -> str:
#     buf = filename_to_str(IMC_EVENT + "data_writes.unit")

#     assert buf != 0, "Unknown error with Intel GPU in function: imc_data_writes_unit()"
    
#     return buf

# def igt_devices_scan(force: bool):
#     pass

# class IGT():
#     def __init__(self) -> None:
#         self.devs = igt_devs()

#     def scan_devices(self, force: bool) -> None:
#         if force and self.devs.devs_scanned:
#             # Continue from line 659 in `igt_device_scan.c`
#             import pdb; pdb.set_trace()

#         if self.devs.devs_scanned:
#             return

#         self.prepare_scan()
#         self.scan_drm_devices()

#         self.devs.devs_scanned = True

#     def prepare_scan(self) -> None:
#         self._igt_init_list_head(self.devs.all)
#         self._igt_init_list_head(self.devs.filtered)

#     def scan_drm_devices(self) -> None:
#         pass

#     def _igt_init_list_head(self, lst: ct.pointer(igt_list_head)) -> None:
#         lst.prev = ct.byref(lst)
#         lst.next = ct.byref(lst)

# if __name__ == "__main__":
#     period = ct.c_uint(1)
#     con_w = ct.c_int(-1)
#     con_h = ct.c_int(-1)
#     engines = ct.POINTER()
#     i = ct.c_uint()
#     ret = ct.c_int(0)
#     ch = ct.c_int()
#     list_device = ct.c_bool(False)
