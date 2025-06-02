from pymem import exception as pymem_exception
from pymem.process import module_from_name
from win32gui import FindWindow, GetForegroundWindow
from time import time
import config
from user_config import user_cfg

# Attempts to find the final memory address of the player's HP using base address and offsets.
def get_hp_address(pm):
    if not hasattr(get_hp_address, "last_error"):
        get_hp_address.last_error = None
    if not hasattr(get_hp_address, "last_error_time"):
        get_hp_address.last_error_time = 0
    if not hasattr(get_hp_address, "last_successful_chain"):
        get_hp_address.last_successful_chain = None
    COOLDOWN = 15  # 15 seconds

    def print_error_throttled(error_msg):
        now = time()
        if (get_hp_address.last_error != error_msg or 
            (now - get_hp_address.last_error_time) > COOLDOWN):
            print(error_msg)
            get_hp_address.last_error = error_msg
            get_hp_address.last_error_time = now

    if not hasattr(get_hp_address, "last_debug_error"):
        get_hp_address.last_debug_error = None
    if not hasattr(get_hp_address, "last_debug_error_time"):
        get_hp_address.last_debug_error_time = 0

    def debug_print_throttled(error_msg):
        now = time()
        if (get_hp_address.last_debug_error != error_msg or
            (now - get_hp_address.last_debug_error_time) > COOLDOWN):
            debug_print(error_msg)
            get_hp_address.last_debug_error = error_msg
            get_hp_address.last_debug_error_time = now

    try:
        # Ensure Pymem object is valid.
        if pm is None or pm.process_handle is None:
             return None
 
        # Get module information to calculate base address.
        mod = module_from_name(pm.process_handle, config.MODULE_NAME)
 
        if mod is None:
            error_msg = f"[ERROR] Module not found: {config.MODULE_NAME}"
            print_error_throttled(error_msg)
            return None
 
        # Calculate the initial address using the module base and a base offset.
        base_addr = mod.lpBaseOfDll + config.BASE_OFFSET
        addr = base_addr
        chain_addresses = [addr]
        for i, off in enumerate(config.OFFSETS):
            if addr is None:
                error_msg = f"[ERROR] Address is None at offset index {i}"
                debug_print_throttled(error_msg)
                raise Exception(error_msg)
            try:
                next_addr = pm.read_ulonglong(addr) + off
                if next_addr == off:
                    error_msg = f"[ERROR] Next address equals offset ({off}) at index {i}"
                    debug_print_throttled(error_msg)
                    raise Exception(error_msg)
                if next_addr < 4096 and i < len(config.OFFSETS) -1:
                    error_msg = f"[ERROR] Next address too low ({next_addr}) at index {i}"
                    debug_print_throttled(error_msg)
                    raise Exception(error_msg)
                addr = next_addr
                chain_addresses.append(addr)
            except pymem_exception.PymemError as e:
                error_msg = f"[ERROR] PymemError during pointer chain at index {i}: {e}"
                print_error_throttled(error_msg)
                return None
            except Exception as e:
                error_msg = f"[ERROR] Exception during pointer chain at index {i}: {e}"
                print_error_throttled(error_msg)
                return None
        # Only print the pointer chain if the pointer path (excluding the final HP address) is different
        current_pointer_path = tuple(chain_addresses[:-1])
        if get_hp_address.last_successful_chain != current_pointer_path:
            debug_print("[DEBUG] Pointer chain resolved:")
            for i, (a, off) in enumerate(zip(chain_addresses, [0] + list(config.OFFSETS))):
                debug_print(f"  Step {i}: addr=0x{a:X} offset=0x{off:X}")
            get_hp_address.last_successful_chain = current_pointer_path
        get_hp_address.last_error = None
        return addr
 
    except pymem_exception.PymemError as e:
        error_msg = f"[ERROR] PymemError in get_hp_address: {e}"
        print_error_throttled(error_msg)
        return None
    except Exception as e:
         error_msg = f"[ERROR] Exception in get_hp_address: {e}"
         print_error_throttled(error_msg)
         return None
 
# Checks if the target game window is currently the foreground (active) window.
def is_target_window_foreground():
    # Find the handle of the target window by its title.
    target_hwnd = FindWindow(None, config.WINDOW_TITLE)
    if target_hwnd:
        # Get the handle of the current foreground window.
        foreground_hwnd = GetForegroundWindow()
        # Return True if the target window is the foreground window.
        return target_hwnd == foreground_hwnd
    # Return False if the target window was not found.
    return False


def debug_print(message):
    if user_cfg and user_cfg['DEVELOPER_DEBUG']:
        print('> ' + message)