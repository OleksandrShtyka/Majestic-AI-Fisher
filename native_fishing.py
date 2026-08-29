"""Optional ctypes bridge for the C++ fishing primitives.

Python keeps the GUI, callbacks and DQN model; when the DLL is present, C++
performs the per-frame colour scan and direct keyboard taps.
"""

from __future__ import annotations

import ctypes
import os
from pathlib import Path

import numpy as np


class NativeFishing:
    def __init__(self) -> None:
        self._dll = self._load()
        if self._dll:
            self._dll.fishing_process_bgr.argtypes = [
                ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int, ctypes.c_int,
                ctypes.c_int, ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_int),
            ]
            self._dll.fishing_process_bgr.restype = ctypes.c_int
            self._dll.fishing_tap_key.argtypes = [ctypes.c_ushort, ctypes.c_int]
            self._dll.fishing_tap_key.restype = ctypes.c_int

    @staticmethod
    def _load():
        root = Path(__file__).resolve().parent
        for path in (
            root / "Backend C" / "build" / "fishing_native.dll",
            root / "build" / "fishing_native.dll",
            root / "cmake-build-debug" / "fishing_native.dll",
        ):
            if path.is_file():
                try:
                    if hasattr(os, "add_dll_directory"):
                        os.add_dll_directory(str(path.parent))
                    return ctypes.WinDLL(str(path))
                except OSError:
                    pass
        return None

    @property
    def available(self) -> bool:
        return self._dll is not None

    def process_bgr(self, frame: np.ndarray) -> tuple[float, bool, bool]:
        if not self._dll or frame is None or frame.ndim != 3 or frame.shape[2] != 3:
            return 0.0, False, False
        image = np.ascontiguousarray(frame, dtype=np.uint8)
        distance, in_zone = ctypes.c_double(), ctypes.c_int()
        found = self._dll.fishing_process_bgr(
            image.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte)), image.shape[1], image.shape[0],
            image.strides[0], ctypes.byref(distance), ctypes.byref(in_zone),
        )
        return distance.value, bool(in_zone.value), bool(found)

    def tap_key(self, scancode: int, duration_ms: int) -> bool:
        return bool(self._dll and self._dll.fishing_tap_key(scancode, duration_ms))


native_fishing = NativeFishing()
