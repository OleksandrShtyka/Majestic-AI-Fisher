cmake_minimum_required(VERSION 3.20)

project(MajesticAIFisherNative LANGUAGES CXX)

# The desktop UI and the ML model stay in Python. This target builds only the
# Windows-native fishing primitives consumed by native_fishing.py via ctypes.
add_subdirectory("Backend C")
