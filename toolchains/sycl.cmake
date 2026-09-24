include("${CMAKE_CURRENT_LIST_DIR}/init.cmake")

if(NOT DEFINED ONEAPI_ROOT)
    set(ONEAPI_ROOT "$ENV{ONEAPI_ROOT}")
endif()

set(CMAKE_C_COMPILER   "icx")
set(CMAKE_CXX_COMPILER "icpx")

include("${CMAKE_CURRENT_LIST_DIR}/exit.cmake")
