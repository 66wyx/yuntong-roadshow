#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
#include <stdio.h>

typedef struct libusb_context libusb_context;
typedef struct libusb_device libusb_device;
typedef struct libusb_device_handle libusb_device_handle;
typedef long long ssize_t;

struct libusb_device_descriptor {
    uint8_t bLength;
    uint8_t bDescriptorType;
    uint16_t bcdUSB;
    uint8_t bDeviceClass;
    uint8_t bDeviceSubClass;
    uint8_t bDeviceProtocol;
    uint8_t bMaxPacketSize0;
    uint16_t idVendor;
    uint16_t idProduct;
    uint16_t bcdDevice;
    uint8_t iManufacturer;
    uint8_t iProduct;
    uint8_t iSerialNumber;
    uint8_t bNumConfigurations;
};

typedef int (__cdecl *libusb_init_fn)(libusb_context **ctx);
typedef int (__cdecl *libusb_set_option_fn)(libusb_context *ctx, int option, ...);
typedef int (__cdecl *libusb_get_device_list_fn)(
    libusb_context *ctx, libusb_device ***list);
typedef void (__cdecl *libusb_free_device_list_fn)(
    libusb_device **list, int unref_devices);
typedef int (__cdecl *libusb_get_device_descriptor_fn)(
    libusb_device *dev, struct libusb_device_descriptor *desc);
typedef int (__cdecl *libusb_open_fn)(
    libusb_device *dev, libusb_device_handle **handle);
typedef void (__cdecl *libusb_close_fn)(libusb_device_handle *handle);
typedef int (__cdecl *libusb_claim_interface_fn)(
    libusb_device_handle *handle, int interface_number);
typedef int (__cdecl *libusb_release_interface_fn)(
    libusb_device_handle *handle, int interface_number);
typedef int (__cdecl *libusb_reset_device_fn)(libusb_device_handle *handle);
typedef int (__cdecl *libusb_control_transfer_fn)(
    libusb_device_handle *handle, uint8_t request_type, uint8_t request,
    uint16_t value, uint16_t index, unsigned char *data, uint16_t length,
    unsigned int timeout);
typedef uint8_t (__cdecl *libusb_get_bus_number_fn)(libusb_device *dev);
typedef uint8_t (__cdecl *libusb_get_device_address_fn)(libusb_device *dev);

#define LIBUSB_OPTION_USE_USBDK 1

static void *symbol(HMODULE module, const char *name)
{
    void *result = (void *)GetProcAddress(module, name);
    if (result == NULL) {
        fprintf(stderr, "Missing libusb symbol: %s\n", name);
        ExitProcess(2);
    }
    return result;
}

int main(void)
{
    HMODULE module;
    libusb_init_fn init;
    libusb_set_option_fn set_option;
    libusb_get_device_list_fn get_device_list;
    libusb_free_device_list_fn free_device_list;
    libusb_get_device_descriptor_fn get_descriptor;
    libusb_open_fn open_device;
    libusb_close_fn close_device;
    libusb_claim_interface_fn claim_interface;
    libusb_release_interface_fn release_interface;
    libusb_reset_device_fn reset_device;
    libusb_control_transfer_fn control_transfer;
    libusb_get_bus_number_fn get_bus;
    libusb_get_device_address_fn get_address;
    libusb_context *ctx = NULL;
    libusb_device **devices = NULL;
    libusb_device_handle *handle = NULL;
    ssize_t count;
    int result;
    int found = 0;
    unsigned char data[4] = {0};

    module = LoadLibraryA("libusb_original.dll");
    if (module == NULL) {
        fprintf(stderr, "LoadLibrary failed: %lu\n", GetLastError());
        return 2;
    }

    init = (libusb_init_fn)symbol(module, "libusb_init");
    set_option = (libusb_set_option_fn)symbol(module, "libusb_set_option");
    get_device_list =
        (libusb_get_device_list_fn)symbol(module, "libusb_get_device_list");
    free_device_list =
        (libusb_free_device_list_fn)symbol(module, "libusb_free_device_list");
    get_descriptor = (libusb_get_device_descriptor_fn)
        symbol(module, "libusb_get_device_descriptor");
    open_device = (libusb_open_fn)symbol(module, "libusb_open");
    close_device = (libusb_close_fn)symbol(module, "libusb_close");
    claim_interface =
        (libusb_claim_interface_fn)symbol(module, "libusb_claim_interface");
    release_interface = (libusb_release_interface_fn)
        symbol(module, "libusb_release_interface");
    reset_device =
        (libusb_reset_device_fn)symbol(module, "libusb_reset_device");
    control_transfer =
        (libusb_control_transfer_fn)symbol(module, "libusb_control_transfer");
    get_bus = (libusb_get_bus_number_fn)symbol(module, "libusb_get_bus_number");
    get_address = (libusb_get_device_address_fn)
        symbol(module, "libusb_get_device_address");

    result = init(&ctx);
    printf("libusb_init=%d\n", result);
    if (result != 0) {
        return 2;
    }

    result = set_option(ctx, LIBUSB_OPTION_USE_USBDK);
    printf("set_usbdk=%d\n", result);
    if (result != 0) {
        return 3;
    }

    count = get_device_list(ctx, &devices);
    printf("device_count=%lld\n", (long long)count);
    if (count < 0) {
        return 4;
    }

    for (ssize_t i = 0; i < count; i++) {
        struct libusb_device_descriptor descriptor;

        if (get_descriptor(devices[i], &descriptor) != 0) {
            continue;
        }
        printf("usb=%u.%u id=%04x:%04x\n",
               get_bus(devices[i]), get_address(devices[i]),
               descriptor.idVendor, descriptor.idProduct);
        if (descriptor.idVendor != 0x0e8d ||
            descriptor.idProduct != 0x7612) {
            continue;
        }

        found = 1;
        result = open_device(devices[i], &handle);
        printf("open=%d\n", result);
        if (result != 0) {
            continue;
        }

        result = reset_device(handle);
        printf("reset_device=%d\n", result);
        Sleep(500);

        result = claim_interface(handle, 0);
        printf("claim_interface_0=%d\n", result);
        result = control_transfer(handle, 0xc0, 0x07, 0x0000, 0x09a8,
                                  data, sizeof(data), 5000);
        printf("read_09a8=%d data=%02x%02x%02x%02x\n",
               result, data[0], data[1], data[2], data[3]);

        if (handle != NULL) {
            (void)release_interface(handle, 0);
            close_device(handle);
            handle = NULL;
        }
    }

    free_device_list(devices, 1);
    if (!found) {
        fprintf(stderr, "0e8d:7612 not found\n");
        return 5;
    }
    return 0;
}
