import ctypes

class dbus(ctypes.Structure):
    _fields_ = []

class dbus_atomic(ctypes.Structure):
    _fields_ = [('value', ctypes.c_int32)]

class dbus_r_mutex(ctypes.Structure):
    _fields_ = []

class dbus_error(ctypes.Structure):
    _fields_ = [
        ('name',    ctypes.c_wchar_p),
        ('message', ctypes.c_wchar_p),
        ('dummy1',  ctypes.c_int, 1),
        ('dummy2',  ctypes.c_int, 1),
        ('dummy3',  ctypes.c_int, 1),
        ('dummy4',  ctypes.c_int, 1),
        ('dummy5',  ctypes.c_int, 1),
        ('padding', ctypes.c_void_p),
    ]

class dbus_connection(ctypes.Structure):
    _fields_ = [
        ('refcount',                      dbus_atomic), # DBusAtomic 
        ('mutex',                         ctypes.), # DBusRMutex *
        ('dispatch_mutex',                ctypes.), # DBusCMutex *
        ('dispatch_cond',                 ctypes.), # DBusCondVar *
        ('io_path_mutex',                 ctypes.), # DBusCMutex *
        ('io_path_cond',                  ctypes.), # DBusCondVar *
        ('outgoing_messages',             ctypes.), # DBusList *
        ('incoming_messages',             ctypes.), # DBusList *
        ('expired_messages',              ctypes.), # DBusList *
        ('message_borrowed',              ctypes.), # DBusMessage *
        ('n_outgoing',                    ctypes.c_int), # int 
        ('n_incoming',                    ctypes.c_int), # int 
        ('outgoing_counter',              ctypes.), # DBusCounter *
        ('transport',                     ctypes.), # DBusTransport *
        ('watches',                       ctypes.), # DBusWatchList *
        ('timeouts',                      ctypes.), # DBusTimeoutList *
        ('filter_list',                   ctypes.), # DBusList *
        ('slot_mutex',                    ctypes.), # DBusRMutex *
        ('slot_list',                     ctypes.), # DBusDataSlotList 
        ('pending_replies',               ctypes.), # DBusHashTable *
        ('client_serial',                 ctypes.), # dbus_uint32_t 
        ('disconnect_message_link',       ctypes.), # DBusList *
        ('wakeup_main_function',          ctypes.), # DBusWakeupMainFunction 
        ('wakeup_main_data',              ctypes.), # void *
        ('free_wakeup_main_data',         ctypes.), # DBusFreeFunction 
        ('dispatch_status_function',      ctypes.), # DBusDispatchStatusFunction 
        ('dispatch_status_data',          ctypes.c_void_p), # void *
        ('free_dispatch_status_data',     ctypes.), # DBusFreeFunction 
        ('last_dispatch_status',          ctypes.), # DBusDispatchStatus 
        ('objects',                       ctypes.), # DBusObjectTree *
        ('server_guid',                   ctypes.c_wchar_p), # char *
        ('dispatch_acquired',             ctypes.), # dbus_bool_t 
        ('io_path_acquired',              ctypes.), # dbus_bool_t 
        ('shareable',                     ctypes..c_uint, 1), # unsigned int  : 1
        ('exit_on_disconnect',            ctypes..c_uint, 1), # unsigned int  : 1
        ('route_peer_messages',           ctypes..c_uint, 1), # unsigned int  : 1
        ('disconnected_message_arrived',  ctypes..c_uint, 1), # unsigned int  : 1
        ('disconnected_message_processed',ctypes..c_uint, 1), # unsigned int  : 1
    ]