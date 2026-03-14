cmake_minimum_required(VERSION 3.10)
project(LZ4DecompressionPS5)

# PS5 SDK Settings
set(PS5_SDK_PATH "/opt/ps5-sdk" CACHE PATH "PS5 SDK installation path")

# Compilers
set(CMAKE_C_COMPILER "${PS5_SDK_PATH}/bin/x86_64-scei-ps5-gcc")
set(CMAKE_CXX_COMPILER "${PS5_SDK_PATH}/bin/x86_64-scei-ps5-g++")

# Optimization flags
set(CMAKE_C_FLAGS_RELEASE "-O3 -march=native -flto")
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native -flto")

# Include directories
include_directories("${PS5_SDK_PATH}/include")

# Link directories
link_directories("${PS5_SDK_PATH}/lib")

# Create executable
add_executable(LZ4DecompressionPS5.elf LZ4DecompressionPS5.c)

# Link LZ4 library
target_link_libraries(LZ4DecompressionPS5.elf lz4)

# Set output directory
set_target_properties(LZ4DecompressionPS5.elf PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
)

# Print build info
message(STATUS "Building LZ4 Decompression ELF for PS5")
message(STATUS "PS5 SDK: ${PS5_SDK_PATH}")
message(STATUS "Compiler: ${CMAKE_C_COMPILER}")
message(STATUS "Build Type: ${CMAKE_BUILD_TYPE}")
