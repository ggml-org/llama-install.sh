#include <cstdio>
#include <cstdlib>
#include <sycl/sycl.hpp>

#ifdef __linux__
#include <sys/epoll.h>
#endif

int
main(void)
{
#ifdef __linux__
    // Force GLIBC_2.35, waiting for a better solution
    if (getenv("_probe_glibc_floor")) {
        struct epoll_event e{0};
        (void)epoll_pwait2(-1, &e, 0, NULL, NULL);
    }
#endif

    try {
        for (const auto &device : sycl::device::get_devices(sycl::info::device_type::gpu)) {
            if (device.get_backend() != sycl::backend::ext_oneapi_level_zero)
                continue;

            if (!device.has(sycl::aspect::fp16))
                continue;

            std::puts("fp16");
            return 0;
        }
    } catch (const sycl::exception &) {
        return 1;
    }
    return 2;
}
