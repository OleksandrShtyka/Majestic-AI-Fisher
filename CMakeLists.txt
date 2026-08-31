cmake_minimum_required(VERSION 3.20)

project(MajesticAIFisher LANGUAGES CXX)

# The application is fully native; the DLL is also kept for compatibility with
# existing installations that used the previous Python bridge.
add_subdirectory("Backend C")

add_executable(MajesticAIFisher WIN32
    src/native_app.cpp
    src/dqn_agent.cpp
    src/app_services.cpp
    src/remote_auth.cpp
    third_party/imgui/imgui.cpp
    third_party/imgui/imgui_draw.cpp
    third_party/imgui/imgui_tables.cpp
    third_party/imgui/imgui_widgets.cpp
    third_party/imgui/backends/imgui_impl_win32.cpp
    third_party/imgui/backends/imgui_impl_dx11.cpp
)
target_compile_features(MajesticAIFisher PRIVATE cxx_std_17)
target_compile_definitions(MajesticAIFisher PRIVATE UNICODE _UNICODE WIN32_LEAN_AND_MEAN NOMINMAX)
target_include_directories(MajesticAIFisher PRIVATE third_party/imgui third_party/imgui/backends)
target_link_libraries(MajesticAIFisher PRIVATE fishing_native comctl32 dwmapi bcrypt gdiplus d3d11 dxgi d3dcompiler winhttp)
set(MAJESTIC_SITE_URL "https://my-site-swart-rho-22.vercel.app" CACHE STRING "Public website URL used for account authentication")
target_compile_definitions(MajesticAIFisher PRIVATE MAJESTIC_SITE_URL="${MAJESTIC_SITE_URL}")
if(MINGW)
    target_link_options(MajesticAIFisher PRIVATE -static-libgcc -static-libstdc++)
    get_filename_component(MINGW_BIN_DIR "${CMAKE_CXX_COMPILER}" DIRECTORY)
    foreach(runtime libgcc_s_seh-1.dll libwinpthread-1.dll)
        if(EXISTS "${MINGW_BIN_DIR}/${runtime}")
            add_custom_command(TARGET MajesticAIFisher POST_BUILD
                COMMAND ${CMAKE_COMMAND} -E copy_if_different
                    "${MINGW_BIN_DIR}/${runtime}" "$<TARGET_FILE_DIR:MajesticAIFisher>")
        endif()
    endforeach()
endif()
set_target_properties(MajesticAIFisher PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}")
