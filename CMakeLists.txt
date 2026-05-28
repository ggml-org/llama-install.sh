cmake_minimum_required(VERSION 3.28)
project(llama-install LANGUAGES C CXX)

find_program(ZSTD zstd REQUIRED)

include(FetchContent)

macro(FetchDep NAME DEFAULT_REPO DEFAULT_VERSION)
    string(TOUPPER ${NAME} NAME_UPPER)

    if(NOT "$ENV{${NAME_UPPER}_REPO}" STREQUAL "")
        set(DEFAULT_REPO "$ENV{${NAME_UPPER}_REPO}")
    endif()
    set(${NAME_UPPER}_REPO "${DEFAULT_REPO}" CACHE STRING "${NAME} repository")

    if(NOT "$ENV{${NAME_UPPER}_VERSION}" STREQUAL "")
        set(DEFAULT_VERSION "$ENV{${NAME_UPPER}_VERSION}")
    endif()
    set(${NAME_UPPER}_VERSION "${DEFAULT_VERSION}" CACHE STRING "${NAME} version")

    if(EXISTS "${CMAKE_SOURCE_DIR}/deps/${NAME}/CMakeLists.txt")
        FetchContent_Declare(${NAME}
            SOURCE_DIR "${CMAKE_SOURCE_DIR}/deps/${NAME}"
            ${ARGN}
        )
    else()
        FetchContent_Declare(${NAME}
            GIT_REPOSITORY "${${NAME_UPPER}_REPO}"
            GIT_TAG        "${${NAME_UPPER}_VERSION}"
            SOURCE_DIR     "${CMAKE_SOURCE_DIR}/deps/${NAME}"
            ${ARGN}
        )
    endif()
endmacro()

FetchDep(boringssl
    "https://boringssl.googlesource.com/boringssl"
    "main"
    EXCLUDE_FROM_ALL
)

FetchDep(llamacpp
    "https://github.com/ggml-org/llama.cpp"
    "master"
)

set(CMAKE_BUILD_TYPE "Release" CACHE STRING "" FORCE)
set(BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)

set(CMAKE_INTERPROCEDURAL_OPTIMIZATION ON CACHE BOOL "" FORCE)
set(CMAKE_POSITION_INDEPENDENT_CODE    ON CACHE BOOL "" FORCE)

set(GGML_CCACHE OFF CACHE BOOL "" FORCE)
set(GGML_NATIVE OFF CACHE BOOL "" FORCE)
set(GGML_OPENMP OFF CACHE BOOL "" FORCE)
set(GGML_LTO    OFF CACHE BOOL "" FORCE)

set(LLAMA_BUILD_BORINGSSL ON  CACHE BOOL "" FORCE)
set(LLAMA_BUILD_COMMON    ON  CACHE BOOL "" FORCE)
set(LLAMA_BUILD_TOOLS     ON  CACHE BOOL "" FORCE)
set(LLAMA_BUILD_SERVER    ON  CACHE BOOL "" FORCE)
set(LLAMA_BUILD_APP       ON  CACHE BOOL "" FORCE)

# LibreSSL is supported as an alternative SSL backend in this cross Zig
# pipeline. It needs a few knobs to build cleanly when selected with
# -DLLAMA_BUILD_LIBRESSL=ON -DLLAMA_BUILD_BORINGSSL=OFF.
if(LLAMA_BUILD_LIBRESSL)
    # Zig clang in cross mode to x86_64-windows-gnu exposes glibc symbols
    # (syslog, getentropy, ...) that LibreSSL's check_function_exists picks up
    # as available but that fail to compile because the mingw headers do not
    # declare them. Pin these probes to FALSE so the compat layer keeps its
    # Windows fallbacks.
    set(HAVE_GETENTROPY FALSE CACHE INTERNAL "")
    set(HAVE_SYSLOG     FALSE CACHE INTERNAL "")

    # LibreSSL ships mingw64 perlasm output that uses COFF directives like
    # .def / .scl / .endef which the Zig clang assembler does not understand.
    # Disable the assembly path so the C fallback is used in this cross compile.
    set(ENABLE_ASM OFF CACHE BOOL "" FORCE)
endif()

#add_compile_options(
#    -ffp-model=fast
#    -fno-finite-math-only
#)

add_compile_options(
    -fmacro-prefix-map=${CMAKE_SOURCE_DIR}/deps/boringssl/=
    -fmacro-prefix-map=${CMAKE_SOURCE_DIR}/deps/llamacpp/=
    -ffunction-sections
    -fdata-sections
    -fno-ident
)

if(CMAKE_C_COMPILER_ID STREQUAL "Clang" OR CMAKE_C_COMPILER_ID STREQUAL "GNU")
    add_link_options(-static-libgcc -static-libstdc++)
    add_link_options(-Wl,--gc-sections -Wl,--strip-all)
elseif(CMAKE_C_COMPILER_ID STREQUAL "AppleClang")
    add_link_options(-Wl,-dead_strip -Wl,-S)
else()
    message(WARNING "Unknown compiler: ${CMAKE_C_COMPILER_ID}")
endif()

include("${CMAKE_CURRENT_LIST_DIR}/win32/shim.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/vulkan/stub.cmake")

if(LLAMA_INSTALL_PROBE)
    add_subdirectory(${LLAMA_INSTALL_PROBE})
    set(LLAMA_INSTALL_TARGET "probe")
else()
    FetchContent_MakeAvailable(llamacpp)
    set(LLAMA_INSTALL_TARGET "llama-app")
    # TODO: llvm issue ?
    set_property(SOURCE "${llamacpp_SOURCE_DIR}/ggml/src/ggml-cpu/amx/mmq.cpp"
        TARGET_DIRECTORY ggml-cpu
        APPEND PROPERTY COMPILE_OPTIONS "-fno-unroll-loops"
    )
endif()

llama_install_link_win32_shim(${LLAMA_INSTALL_TARGET})

include("${CMAKE_CURRENT_LIST_DIR}/cuda/prune.cmake")
llama_install_prune_cuda(${LLAMA_INSTALL_TARGET})

set(LLAMA_INSTALL_FILE "${LLAMA_INSTALL_DIR}/${LLAMA_INSTALL_TARGET}.zst")

add_custom_command(
    OUTPUT  ${LLAMA_INSTALL_FILE}.done
    COMMAND ${CMAKE_COMMAND} -E make_directory ${LLAMA_INSTALL_DIR}
    COMMAND ${ZSTD} -f --rm -19 $<TARGET_FILE:${LLAMA_INSTALL_TARGET}> -o ${LLAMA_INSTALL_FILE}
    COMMAND ${CMAKE_COMMAND} -E touch ${LLAMA_INSTALL_FILE}.done
    DEPENDS ${LLAMA_INSTALL_TARGET}
)
add_custom_target(llama-install DEPENDS ${LLAMA_INSTALL_FILE}.done)
