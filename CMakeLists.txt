cmake_minimum_required(VERSION 3.18)

set(CMAKE_TRY_COMPILE_TARGET_TYPE "STATIC_LIBRARY")
set(CMAKE_COLOR_DIAGNOSTICS ON)

set(NUM_CORES 8 CACHE STRING "Number of cluster cores used")

project(siracusa-network LANGUAGES C ASM)

include(cmake/pulp-sdk-siracusa.cmake)

add_library(siracusa-network STATIC)
file(GLOB_RECURSE SOURCES CONFIGURE_DEPENDS gen/src/*.c util/*.c kernel/*.c)
target_sources(siracusa-network PRIVATE ${SOURCES})
target_include_directories(siracusa-network PUBLIC gen/inc util kernel)
target_link_libraries(siracusa-network PRIVATE pulp-sdk)

set(PULPNNVERSION XPULPV2)
set(PULPNNBITWIDTH 32)
add_subdirectory(third_party/pulp-nn-mixed)
target_link_libraries(pulp-nn-mixed PRIVATE pulp-sdk)
target_link_libraries(siracusa-network PUBLIC pulp-nn-mixed)

set(USE_NEUREKA ON)
add_subdirectory(third_party/pulp-nnx)
target_link_libraries(pulp-nnx PRIVATE pulp-sdk)
target_link_libraries(siracusa-network PUBLIC pulp-nnx)

add_executable(test test/src/main.c test/src/CycleCounter.c)
target_include_directories(test PRIVATE test/inc gen/test)
target_link_libraries(test PRIVATE pulp-sdk)
target_link_libraries(test PRIVATE siracusa-network)

include(cmake/simulation.cmake)
file(GLOB_RECURSE HEXFILES CONFIGURE_DEPENDS gen/hex/*.hex)
if (NOT HEXFILES)
	target_compile_options(test PRIVATE -DNOFLASH)
else()
	gvsoc_flags_add_files_to_hyperflash(GVSOC_EXTRA_FLAGS HEXFILES)
endif()
add_gvsoc_emulation(test siracusa)
