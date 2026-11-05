#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>

typedef struct libusb_context libusb_context;
typedef struct libusb_device_handle libusb_device_handle;
struct libusb_transfer;
typedef int (__cdecl *libusb_init_fn)(libusb_context **ctx);
typedef int (__cdecl *libusb_set_option_fn)(libusb_context *ctx, int option, ...);
typedef int (__cdecl *libusb_submit_transfer_fn)(
    struct libusb_transfer *transfer);
typedef int (__cdecl *libusb_handle_events_timeout_fn)(
    libusb_context *ctx, void *tv);
typedef int (__cdecl *libusb_control_transfer_fn)(
    libusb_device_handle *handle, uint8_t request_type, uint8_t request,
    uint16_t value, uint16_t index, unsigned char *data, uint16_t length,
    unsigned int timeout);
typedef int (__cdecl *libusb_reset_device_fn)(libusb_device_handle *handle);

#define LIBUSB_OPTION_USE_USBDK 1
#define LIBUSB_TRANSFER_TYPE_CONTROL 0
#define LIBUSB_TRANSFER_COMPLETED 0
#define LIBUSB_TRANSFER_ERROR 1
#define LIBUSB_TRANSFER_TIMED_OUT 2
#define LIBUSB_TRANSFER_CANCELLED 3
#define LIBUSB_TRANSFER_STALL 4
#define LIBUSB_TRANSFER_NO_DEVICE 5
#define LIBUSB_TRANSFER_OVERFLOW 6

typedef void (__cdecl *libusb_transfer_cb_fn)(struct libusb_transfer *transfer);

struct libusb_transfer {
    libusb_device_handle *dev_handle;
    uint8_t flags;
    unsigned char endpoint;
    unsigned char type;
    unsigned int timeout;
    int status;
    int length;
    int actual_length;
    libusb_transfer_cb_fn callback;
    void *user_data;
    unsigned char *buffer;
    int num_iso_packets;
};

typedef struct control_work {
    struct control_work *next;
    struct libusb_transfer *transfer;
} control_work;

static INIT_ONCE control_queue_once = INIT_ONCE_STATIC_INIT;
static CRITICAL_SECTION pending_lock;
static CRITICAL_SECTION completed_lock;
static HANDLE control_work_ready;
static control_work *pending_head;
static control_work *pending_tail;
static control_work *completed_head;
static control_work *completed_tail;

/* Logging is opt-in: set USBDK_PROXY_LOG to a writable file path. */
static void proxy_log(const char *format, ...)
{
    char log_path[MAX_PATH];
    char message[512];
    va_list arguments;
    int length;
    HANDLE file;
    DWORD written;
    DWORD path_length;

    path_length = GetEnvironmentVariableA(
        "USBDK_PROXY_LOG", log_path, (DWORD)sizeof(log_path));
    if (path_length == 0 || path_length >= sizeof(log_path)) {
        return;
    }

    va_start(arguments, format);
    length = vsnprintf(message, sizeof(message), format, arguments);
    va_end(arguments);
    if (length <= 0) {
        return;
    }
    if ((size_t)length >= sizeof(message) - 2) {
        length = (int)sizeof(message) - 2;
    }
    message[length++] = '\r';
    message[length++] = '\n';

    file = CreateFileA(log_path, FILE_APPEND_DATA,
                       FILE_SHARE_READ | FILE_SHARE_WRITE, NULL,
                       OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (file == INVALID_HANDLE_VALUE) {
        return;
    }
    (void)WriteFile(file, message, (DWORD)length, &written, NULL);
    CloseHandle(file);
}

static HMODULE load_original(void)
{
    static HMODULE module;
    HMODULE current;

    current = InterlockedCompareExchangePointer(
        (PVOID volatile *)&module, NULL, NULL);
    if (current != NULL) {
        return current;
    }

    current = LoadLibraryA("libusb_original.dll");
    if (current == NULL) {
        return NULL;
    }

    if (InterlockedCompareExchangePointer(
            (PVOID volatile *)&module, current, NULL) != NULL) {
        FreeLibrary(current);
        return module;
    }
    return current;
}

static void *original_symbol(const char *name)
{
    HMODULE module = load_original();

    if (module == NULL) {
        return NULL;
    }
    return (void *)GetProcAddress(module, name);
}

static int transfer_status_from_error(int error)
{
    switch (error) {
    case -4:  /* LIBUSB_ERROR_NO_DEVICE */
        return LIBUSB_TRANSFER_NO_DEVICE;
    case -6:  /* LIBUSB_ERROR_BUSY */
    case -10: /* LIBUSB_ERROR_INTERRUPTED */
        return LIBUSB_TRANSFER_CANCELLED;
    case -7:  /* LIBUSB_ERROR_TIMEOUT */
        return LIBUSB_TRANSFER_TIMED_OUT;
    case -8:  /* LIBUSB_ERROR_OVERFLOW */
        return LIBUSB_TRANSFER_OVERFLOW;
    case -9:  /* LIBUSB_ERROR_PIPE */
        return LIBUSB_TRANSFER_STALL;
    default:
        return LIBUSB_TRANSFER_ERROR;
    }
}

static DWORD WINAPI control_worker(LPVOID unused)
{
    libusb_control_transfer_fn control_transfer;

    (void)unused;
    control_transfer =
        (libusb_control_transfer_fn)original_symbol("libusb_control_transfer");
    if (control_transfer == NULL) {
        return 1;
    }

    for (;;) {
        control_work *work;
        struct libusb_transfer *transfer;
        int result;

        WaitForSingleObject(control_work_ready, INFINITE);

        EnterCriticalSection(&pending_lock);
        work = pending_head;
        if (work != NULL) {
            pending_head = work->next;
            if (pending_head == NULL) {
                pending_tail = NULL;
            }
        }
        LeaveCriticalSection(&pending_lock);

        if (work == NULL) {
            continue;
        }

        transfer = work->transfer;
        if ((transfer->buffer[0] & 0x60) == 0x40) {
            proxy_log("control setup=%02x %02x %02x%02x %02x%02x len=%02x%02x timeout=%u",
                      transfer->buffer[0], transfer->buffer[1],
                      transfer->buffer[3], transfer->buffer[2],
                      transfer->buffer[5], transfer->buffer[4],
                      transfer->buffer[7], transfer->buffer[6],
                      transfer->timeout);
        }
        result = control_transfer(
            transfer->dev_handle,
            transfer->buffer[0],
            transfer->buffer[1],
            (uint16_t)(transfer->buffer[2] |
                       ((uint16_t)transfer->buffer[3] << 8)),
            (uint16_t)(transfer->buffer[4] |
                       ((uint16_t)transfer->buffer[5] << 8)),
            transfer->buffer + 8,
            (uint16_t)(transfer->buffer[6] |
                       ((uint16_t)transfer->buffer[7] << 8)),
            transfer->timeout);
        if ((transfer->buffer[0] & 0x60) == 0x40) {
            proxy_log("control result=%d", result);
        }

        transfer->actual_length = result > 0 ? result : 0;
        transfer->status = result >= 0
            ? LIBUSB_TRANSFER_COMPLETED
            : transfer_status_from_error(result);

        work->next = NULL;
        EnterCriticalSection(&completed_lock);
        if (completed_tail == NULL) {
            completed_head = work;
        } else {
            completed_tail->next = work;
        }
        completed_tail = work;
        LeaveCriticalSection(&completed_lock);
    }
}

static BOOL CALLBACK initialize_control_queue(
    PINIT_ONCE once, PVOID parameter, PVOID *context)
{
    (void)once;
    (void)parameter;
    (void)context;

    InitializeCriticalSection(&pending_lock);
    InitializeCriticalSection(&completed_lock);
    control_work_ready = CreateSemaphoreA(NULL, 0, 0x7fffffff, NULL);
    if (control_work_ready == NULL) {
        return FALSE;
    }
    if (CreateThread(NULL, 0, control_worker, NULL, 0, NULL) == NULL) {
        CloseHandle(control_work_ready);
        control_work_ready = NULL;
        return FALSE;
    }
    return TRUE;
}

__declspec(dllexport)
int __cdecl libusb_init_proxy(libusb_context **ctx)
{
    libusb_init_fn original_init;
    libusb_set_option_fn original_set_option;
    int result;

    original_init = (libusb_init_fn)original_symbol("libusb_init");
    original_set_option =
        (libusb_set_option_fn)original_symbol("libusb_set_option");
    if (original_init == NULL || original_set_option == NULL) {
        return -99; /* LIBUSB_ERROR_OTHER */
    }

    result = original_init(ctx);
    if (result == 0 && ctx != NULL && *ctx != NULL) {
        (void)original_set_option(*ctx, LIBUSB_OPTION_USE_USBDK);
    }
    return result;
}

__declspec(dllexport)
int __cdecl libusb_submit_transfer_proxy(struct libusb_transfer *transfer)
{
    libusb_submit_transfer_fn original_submit;
    control_work *work;

    original_submit =
        (libusb_submit_transfer_fn)original_symbol("libusb_submit_transfer");
    if (original_submit == NULL) {
        return -12; /* LIBUSB_ERROR_NOT_SUPPORTED */
    }
    if (transfer == NULL) {
        return -2; /* LIBUSB_ERROR_INVALID_PARAM */
    }
    if (transfer->type != LIBUSB_TRANSFER_TYPE_CONTROL) {
        return original_submit(transfer);
    }
    if (!InitOnceExecuteOnce(
            &control_queue_once, initialize_control_queue, NULL, NULL)) {
        return -11; /* LIBUSB_ERROR_NO_MEM */
    }

    work = (control_work *)HeapAlloc(
        GetProcessHeap(), HEAP_ZERO_MEMORY, sizeof(*work));
    if (work == NULL) {
        return -11;
    }
    work->transfer = transfer;

    EnterCriticalSection(&pending_lock);
    if (pending_tail == NULL) {
        pending_head = work;
    } else {
        pending_tail->next = work;
    }
    pending_tail = work;
    LeaveCriticalSection(&pending_lock);
    ReleaseSemaphore(control_work_ready, 1, NULL);
    return 0;
}

__declspec(dllexport)
int __cdecl libusb_handle_events_timeout_proxy(
    libusb_context *ctx, void *tv)
{
    libusb_handle_events_timeout_fn original_handle_events;
    control_work *work;

    if (InitOnceExecuteOnce(
            &control_queue_once, initialize_control_queue, NULL, NULL)) {
        EnterCriticalSection(&completed_lock);
        work = completed_head;
        completed_head = NULL;
        completed_tail = NULL;
        LeaveCriticalSection(&completed_lock);

        while (work != NULL) {
            control_work *next = work->next;
            struct libusb_transfer *transfer = work->transfer;

            if (transfer->callback != NULL) {
                transfer->callback(transfer);
            }
            HeapFree(GetProcessHeap(), 0, work);
            work = next;
        }
    }

    original_handle_events = (libusb_handle_events_timeout_fn)
        original_symbol("libusb_handle_events_timeout");
    if (original_handle_events == NULL) {
        return -12;
    }
    return original_handle_events(ctx, tv);
}

__declspec(dllexport)
int __cdecl libusb_reset_device_proxy(libusb_device_handle *handle)
{
    libusb_reset_device_fn original_reset;
    int result;

    original_reset =
        (libusb_reset_device_fn)original_symbol("libusb_reset_device");
    if (original_reset == NULL) {
        return -12; /* LIBUSB_ERROR_NOT_SUPPORTED */
    }
    result = original_reset(handle);
    proxy_log("reset result=%d, settling 750ms", result);
    Sleep(750);
    return result;
}
