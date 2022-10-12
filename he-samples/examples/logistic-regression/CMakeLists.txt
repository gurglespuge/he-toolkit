# Copyright (C) 2021 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

########################################################
## Logistic Regression Homomorphic Encryption Binary
########################################################

project(lr_test LANGUAGES CXX)

cmake_minimum_required(VERSION 3.13 FATAL_ERROR)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

include(../../cmake/gflags.cmake)

find_package(SEAL REQUIRED)

set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package(Threads REQUIRED)

find_package (OpenMP REQUIRED)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${OpenMP_C_FLAGS}")
set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} ${OpenMP_EXE_LINKER_FLAGS}")

file(GLOB CODE_SRCS ${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp)
add_executable(lr_test ${CODE_SRCS})

if(NOT TARGET OpenMP::OpenMP_CXX)
    find_package(Threads REQUIRED)
    add_library(OpenMP::OpenMP_CXX IMPORTED INTERFACE)
    set_property(TARGET OpenMP::OpenMP_CXX
                 PROPERTY INTERFACE_COMPILE_OPTIONS ${OpenMP_CXX_FLAGS})
    set_property(TARGET OpenMP::OpenMP_CXX
                 PROPERTY INTERFACE_LINK_LIBRARIES ${OpenMP_CXX_FLAGS} Threads::Threads)

endif()
target_link_libraries(lr_test PUBLIC OpenMP::OpenMP_CXX)


if(NOT TARGET OpenMP::OpenMP_C)
    find_package(Threads REQUIRED)
    add_library(OpenMP::OpenMP_C IMPORTED INTERFACE)
    set_property(TARGET OpenMP::OpenMP_C
                 PROPERTY INTERFACE_COMPILE_OPTIONS ${OpenMP_C_FLAGS})
    set_property(TARGET OpenMP::OpenMP_C
                 PROPERTY INTERFACE_LINK_LIBRARIES ${OpenMP_C_FLAGS} Threads::Threads)
endif()

target_link_libraries(lr_test PRIVATE OpenMP::OpenMP_CXX)
target_include_directories(lr_test PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)

target_link_libraries(lr_test PRIVATE SEAL::seal)
target_link_libraries(lr_test PRIVATE Threads::Threads)
target_link_libraries(lr_test PRIVATE libgflags)

add_subdirectory(datasets)
add_dependencies(lr_test genSyntheticData)
