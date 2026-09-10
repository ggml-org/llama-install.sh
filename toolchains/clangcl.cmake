include("${CMAKE_CURRENT_LIST_DIR}/init.cmake")

set(CMAKE_C_COMPILER   "clang-cl")
set(CMAKE_CXX_COMPILER "clang-cl")

if(NOT DEFINED CMAKE_CUDA_HOST_COMPILER)
    set(CMAKE_CUDA_HOST_COMPILER "clang-cl")
endif()

include("${CMAKE_CURRENT_LIST_DIR}/exit.cmake")
