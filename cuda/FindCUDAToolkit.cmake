list(LENGTH CMAKE_CUDA_ARCHITECTURES _arch_count)

if(_arch_count EQUAL 0)
    return()
endif()

if(CMAKE_HOST_SYSTEM_NAME STREQUAL "Windows" AND CMAKE_SYSTEM_PROCESSOR STREQUAL "x86_64")
    set(_CUDAToolkit_win_search_dirs "lib/x64")
    set(_CUDAToolkit_win_stub_search_dirs "lib/x64/stubs")
elseif(CMAKE_HOST_SYSTEM_NAME STREQUAL "Windows" AND CMAKE_SYSTEM_PROCESSOR STREQUAL "aarch64")
    set(_CUDAToolkit_win_search_dirs "lib/arm64")
    set(_CUDAToolkit_win_stub_search_dirs "lib/arm64/stubs")
endif()

include("${CMAKE_ROOT}/Modules/FindCUDAToolkit.cmake")

if(NOT CUDAToolkit_FOUND)
    return()
endif()

if(NOT _arch_count EQUAL 1)
    return()
endif()

find_program(_CUDA_NVPRUNE nvprune HINTS ${CUDAToolkit_BIN_DIR})

if(NOT _CUDA_NVPRUNE)
    message(STATUS "nvprune not found; skipping CUDA static-lib pruning")
    return()
endif()

find_program(_CUDA_CUOBJDUMP cuobjdump HINTS ${CUDAToolkit_BIN_DIR})

list(GET CMAKE_CUDA_ARCHITECTURES 0 _arch_raw)
string(REGEX REPLACE "-.*" "" _arch "${_arch_raw}")

set(_keep_ptx OFF)
if(_arch_raw STREQUAL _arch)
    set(_keep_ptx ON)
endif()

set(_pruned_dir "${CMAKE_CURRENT_BINARY_DIR}/pruned_libs")
file(MAKE_DIRECTORY ${_pruned_dir})

foreach(_lib cublas cublasLt)
    get_target_property(_loc CUDA::${_lib}_static IMPORTED_LOCATION)
    if(NOT _loc OR _loc MATCHES "/pruned_libs/")
        continue() # already pruned (re-entrant find_package call)
    endif()

    set(_prune_arch ${_arch})

    set(_available "")
    if(_CUDA_CUOBJDUMP)
        execute_process(
            COMMAND ${_CUDA_CUOBJDUMP} --list-elf "${_loc}"
            OUTPUT_VARIABLE _dump
            RESULT_VARIABLE _dump_rc
            OUTPUT_STRIP_TRAILING_WHITESPACE
            ERROR_QUIET
        )
        if(NOT _dump_rc)
            string(REPLACE "\n" ";" _dump_lines "${_dump}")
            foreach(_line ${_dump_lines})
                if(_line MATCHES "sm_([0-9]+)")
                    list(APPEND _available ${CMAKE_MATCH_1})
                endif()
            endforeach()
            list(REMOVE_DUPLICATES _available)
        endif()
    endif()

    set(_best 0)
    foreach(_a ${_available})
        if(_a LESS_EQUAL ${_arch} AND _a GREATER ${_best})
            set(_best ${_a})
        endif()
    endforeach()
    if(_best)
        set(_prune_arch ${_best})
    elseif(NOT _CUDA_CUOBJDUMP)
        message(WARNING "cuobjdump not found; cannot detect ${_lib} archs")
    elseif(_available)
        message(FATAL_ERROR "No architecture <= sm_${_arch} found in ${_lib}; pruned library would be empty")
    endif()

    set(_dst "${_pruned_dir}/lib${_lib}_sm${_arch}.a")
    message(STATUS "Pruning ${_lib} for sm_${_prune_arch}...")
    if(_keep_ptx)
        execute_process(
            COMMAND ${_CUDA_NVPRUNE}
                -gencode arch=compute_${_prune_arch},code=sm_${_prune_arch}
                -gencode arch=compute_${_prune_arch},code=compute_${_prune_arch}
                -o "${_dst}" "${_loc}"
            OUTPUT_QUIET
            RESULT_VARIABLE _rc
        )
    else()
        execute_process(
            COMMAND ${_CUDA_NVPRUNE} -arch sm_${_prune_arch} -o "${_dst}" "${_loc}"
            OUTPUT_QUIET
            RESULT_VARIABLE _rc
        )
    endif()
    if(_rc)
        message(FATAL_ERROR "nvprune failed (rc=${_rc}) pruning ${_lib}")
    endif()
    set_target_properties(CUDA::${_lib}_static PROPERTIES IMPORTED_LOCATION "${_dst}")
endforeach()
