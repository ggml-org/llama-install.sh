find_path(VULKAN_HEADERS
    NAMES vulkan/vulkan.h
    HINTS "/opt/vulkan-sdk/include"
)

list(INSERT CMAKE_MODULE_PATH 0 "${CMAKE_CURRENT_LIST_DIR}")

if (VULKAN_HEADERS)
    set(SPIRV-Headers_DIR "${CMAKE_CURRENT_LIST_DIR}" CACHE PATH "SPIRV-Headers config directory")

    add_library(vulkan_stub SHARED ${CMAKE_CURRENT_LIST_DIR}/stub.c)

    target_include_directories(vulkan_stub PUBLIC ${VULKAN_HEADERS})

    set_target_properties(vulkan_stub PROPERTIES
        OUTPUT_NAME vulkan
        VERSION 1.2.0
        POSITION_INDEPENDENT_CODE ON
        C_VISIBILITY_PRESET default
    )

    if(WIN32)
        set_target_properties(vulkan_stub PROPERTIES
            OUTPUT_NAME "vulkan-1"
            PREFIX ""
            SUFFIX ".dll"
        )
    elseif(APPLE)
        set_target_properties(vulkan_stub PROPERTIES
            SOVERSION 1
            SUFFIX ".dylib"
        )
    else()
        set_target_properties(vulkan_stub PROPERTIES
            SOVERSION 1
            SUFFIX ".so"
        )
    endif()
endif()
