include("${CMAKE_CURRENT_LIST_DIR}/init.cmake")

if(NOT DEFINED ROCM_PATH)
    set(ROCM_PATH "$ENV{ROCM_PATH}")
endif()

list(APPEND CMAKE_PREFIX_PATH "${ROCM_PATH}/lib/cmake")

if(LLAMA_INSTALL_OS STREQUAL "windows")
    set(CMAKE_C_COMPILER   "${ROCM_PATH}/lib/llvm/bin/clang-cl.exe")
    set(CMAKE_CXX_COMPILER "${ROCM_PATH}/lib/llvm/bin/clang-cl.exe")
    set(CMAKE_HIP_COMPILER "${ROCM_PATH}/lib/llvm/bin/clang++.exe")
else()
    set(CMAKE_C_COMPILER   "${ROCM_PATH}/lib/llvm/bin/clang")
    set(CMAKE_CXX_COMPILER "${ROCM_PATH}/lib/llvm/bin/clang++")
endif()

include("${CMAKE_CURRENT_LIST_DIR}/exit.cmake")
