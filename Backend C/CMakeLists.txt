add_library(fishing_native SHARED fishing_engine.cpp)

target_compile_features(fishing_native PRIVATE cxx_std_17)
target_compile_definitions(fishing_native PRIVATE FISHING_NATIVE_EXPORTS WIN32_LEAN_AND_MEAN NOMINMAX)
target_link_libraries(fishing_native PRIVATE user32 gdi32)
if(MINGW)
    target_link_options(fishing_native PRIVATE -static-libgcc -static-libstdc++)
    get_filename_component(MINGW_BIN_DIR "${CMAKE_CXX_COMPILER}" DIRECTORY)
    set(MINGW_PTHREAD_DLL "${MINGW_BIN_DIR}/libwinpthread-1.dll")
    if(EXISTS "${MINGW_PTHREAD_DLL}")
        add_custom_command(TARGET fishing_native POST_BUILD
            COMMAND ${CMAKE_COMMAND} -E copy_if_different
                "${MINGW_PTHREAD_DLL}" "$<TARGET_FILE_DIR:fishing_native>"
        )
    endif()
endif()

set_target_properties(fishing_native PROPERTIES
    OUTPUT_NAME "fishing_native"
    PREFIX ""
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}"
)
