find_package(MKL REQUIRED)
find_package(DNNL REQUIRED)

add_executable(probe probe.cpp)
target_compile_options(probe PRIVATE -fsycl)

# keep the runtime deps of llama-app, the probe must fail when one is missing
target_link_options(probe PRIVATE -fsycl -Wl,--no-as-needed)
target_link_libraries(probe PRIVATE MKL::MKL_SYCL::BLAS DNNL::dnnl)
set_target_properties(probe PROPERTIES CXX_STANDARD 17 OUTPUT_NAME "probe")
