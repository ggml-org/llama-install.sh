#define VK_NO_PROTOTYPES
#include <vulkan/vulkan.h>

#if defined(_WIN32)
#define VK_STUB_EXPORT __declspec(dllexport)
#else
#define VK_STUB_EXPORT __attribute__((visibility("default")))
#endif

#define VK_STUB_ENTRY(T) VK_STUB_EXPORT VKAPI_ATTR T VKAPI_CALL

VK_STUB_ENTRY(PFN_vkVoidFunction)
vkGetInstanceProcAddr(VkInstance i, const char *c)
{
    return 0;
}

VK_STUB_ENTRY(PFN_vkVoidFunction)
vkGetDeviceProcAddr(VkDevice d, const char *c)
{
    return 0;
}

VK_STUB_ENTRY(void)
vkGetPhysicalDeviceFeatures2(VkPhysicalDevice pd, VkPhysicalDeviceFeatures2 *pdf2)
{ }

VK_STUB_ENTRY(void)
vkCmdCopyBuffer(VkCommandBuffer cb, VkBuffer b0, VkBuffer b1, uint32_t u, const VkBufferCopy *bc)
{ }

VK_STUB_ENTRY(VkResult)
vkCreateInstance(const VkInstanceCreateInfo *ic, const VkAllocationCallbacks *ac, VkInstance *i)
{
    return VK_ERROR_INITIALIZATION_FAILED;
}

VK_STUB_ENTRY(VkResult)
vkEnumeratePhysicalDevices(VkInstance i, uint32_t *u, VkPhysicalDevice *pd)
{
    if (u) *u = 0;
    return VK_SUCCESS;
}

VK_STUB_ENTRY(void)
vkGetPhysicalDeviceProperties(VkPhysicalDevice pd, VkPhysicalDeviceProperties *pdp)
{ }

VK_STUB_ENTRY(void)
vkGetPhysicalDeviceQueueFamilyProperties(VkPhysicalDevice pd, uint32_t *u, VkQueueFamilyProperties *qfp)
{
    if (u) *u = 0;
}
