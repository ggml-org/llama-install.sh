if(VULKAN_HEADERS)
    set(Vulkan_FOUND TRUE)
    set(Vulkan_VERSION "1.2.0")

    find_program(GLSLC
        NAMES glslc
        HINTS "${CMAKE_SOURCE_DIR}/deps/vulkan"
        PATH_SUFFIXES bin
        REQUIRED
    )
    set(Vulkan_GLSLC_EXECUTABLE "${GLSLC}")

    add_library(Vulkan::Vulkan ALIAS vulkan_stub)
else()
    set(Vulkan_FOUND FALSE)
endif()
