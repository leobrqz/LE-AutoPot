import pymem
import pymem.process
import win32gui
 
import config
 
# Attempts to find the final memory address of the player's HP using base address and offsets.
def get_hp_address(pm):
    try:
        # Ensure Pymem object is valid.
        if pm is None or pm.process_handle is None:
             return None
 
        # Get module information to calculate base address.
        mod = pymem.process.module_from_name(pm.process_handle, config.MODULE_NAME)
 
        if mod is None:
            return None
 
        # Calculate the initial address using the module base and a base offset.
        base_addr = mod.lpBaseOfDll + config.BASE_OFFSET
 
        # Start dereferencing the pointer chain.
        addr = base_addr
        for i, off in enumerate(config.OFFSETS):
             if addr is None:
                 return None
             try:
                # Read the value at the current address, add the next offset to get the next address in the chain.
                next_addr = pm.read_ulonglong(addr) + off
 
                # Basic validation checks for the next address.
                if next_addr == off:
                    return None
                # Ensure next address is not too low (invalid pointer) unless it's the final offset.
                if next_addr < 4096 and i < len(config.OFFSETS) -1:
                    return None
 
                # Move to the next address in the chain.
                addr = next_addr
             except pymem.exception.PymemError as e:
                  # Handle Pymem errors during read.
                  return None
             except Exception as e:
                  # Handle other exceptions during read.
                  return None
 
        # Return the final calculated address after all offsets.
        return addr
 
    except pymem.exception.PymemError as e:
        # Handle Pymem errors during initial steps.
        return None
    except Exception as e:
         # Handle other exceptions during initial steps.
         return None
 
# Checks if the target game window is currently the foreground (active) window.
def is_target_window_foreground():
    # Find the handle of the target window by its title.
    target_hwnd = win32gui.FindWindow(None, config.WINDOW_TITLE)
    if target_hwnd:
        # Get the handle of the current foreground window.
        foreground_hwnd = win32gui.GetForegroundWindow()
        # Return True if the target window is the foreground window.
        return target_hwnd == foreground_hwnd
    # Return False if the target window was not found.
    return False