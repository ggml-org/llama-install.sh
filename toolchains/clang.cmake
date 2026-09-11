include("${CMAKE_CURRENT_LIST_DIR}/init.cmake")

if(LLAMA_INSTALL_OS STREQUAL "windows")
    find_program(CLANG_C
        NAMES clang-cl clang-cl.exe
        PATHS "${CMAKE_CURRENT_LIST_DIR}/../deps/clang/bin"
        NO_DEFAULT_PATH)
    set(CLANG_CXX "${CLANG_C}")
    set(CMAKE_CUDA_HOST_COMPILER "cl")
else()
    find_program(CLANG_C
        NAMES clang
        PATHS "${CMAKE_CURRENT_LIST_DIR}/../deps/clang/bin"
        NO_DEFAULT_PATH REQUIRED)
    find_program(CLANG_CXX
        NAMES clang++
        PATHS "${CMAKE_CURRENT_LIST_DIR}/../deps/clang/bin"
        NO_DEFAULT_PATH REQUIRED)
    set(CMAKE_CUDA_HOST_COMPILER "${CLANG_C}")
    set(CMAKE_EXE_LINKER_FLAGS_INIT    "-fuse-ld=lld")
    set(CMAKE_SHARED_LINKER_FLAGS_INIT "-fuse-ld=lld")
    set(CMAKE_MODULE_LINKER_FLAGS_INIT "-fuse-ld=lld")
endif()

set(CMAKE_C_COMPILER   "${CLANG_C}")
set(CMAKE_CXX_COMPILER "${CLANG_CXX}")

include("${CMAKE_CURRENT_LIST_DIR}/exit.cmake")
