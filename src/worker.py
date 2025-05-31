from threading import Thread, Lock
from time import time, sleep
 
from keyboard import send
from pymem import Pymem
from pymem.exception import PymemError
from pymem.process import module_from_name
 
import game_memory
import config
from user_config import user_cfg
 
# Worker thread for automated potion triggering based on in-game HP.
class AutoPotionWorker(Thread):
    _ADDRESS_CHECK_INTERVAL = 2.0
    _DISABLED_STATE_PAUSE = 0.1
    _ERROR_RECOVERY_PAUSE = 0.5
 
    # Initializes worker state and GUI connections.
    def __init__(self, status_text_var, status_color_var, enabled_flag, add_potion_log_callback=None, gui=None, user_cfg=None):
        super().__init__()
 
        # Thread control flags.
        self._running = True
        self._shutting_down = False
 
        # Active logic state flag.
        self._is_active_logic_running = False
 
        # Pymem object and game memory details.
        self._pm = None
        self._hp_final_addr = None
        self._max_hp = None
        self._threshold = None
        self._alerted = False
        self._is_paused_by_window = False
 
        # Variables for stable HP detection (used for Max HP).
        self._last_read_hp = None
        self._stable_hp_timestamp = None
 
        # Configurable stable HP durations.
        self._quick_stable_hp_duration = getattr(config, 'QUICK_STABLE_HP_DURATION', 1.0)
        self._stable_hp_required_duration = getattr(config, 'STABLE_HP_DURATION', 5.0)
 
        # Reset mechanism.
        self._reset_requested = False
        self._lock = Lock()
 
        # GUI update variables.
        self.status_text_var = status_text_var
        self.status_color_var = status_color_var
        self.enabled_flag = enabled_flag
        self.gui = gui
 
        # Log callback.
        self.add_potion_log_callback = add_potion_log_callback
 
        # Initial status update.
        self._update_status("Auto Potion: OFF", config.COLOR_OFF)
 
        self.user_cfg = user_cfg
        self._last_potion_time = config.LAST_POTION_TIME_INIT

        self._potion_cooldown = self.user_cfg['POTION_COOLDOWN'] if self.user_cfg else config.POTION_COOLDOWN
        self._process_found_printed = False  # to print only once
 
    # Requests a state reset. Thread-safe.
    def request_reset(self):
        with self._lock:
            self._reset_requested = True
 
    # Checks for and performs a state reset.
    def _check_and_perform_reset(self):
        reset_done = False
        with self._lock:
            if self._reset_requested:
                self._reset_core_state_variables()
                self._is_active_logic_running = False
                self._reset_requested = False
                reset_done = True
        return reset_done
 
    # Updates GUI status text and color.
    def _update_status(self, text, color_key):
        if self._shutting_down:
            return
        try:
            if self.gui is not None:
                self.gui.status_signal.emit(text, color_key)
            else:
                self.status_text_var.set(text)
                self.status_color_var.set(color_key)
        except Exception:
            self._signal_gui_error_shutdown()
 
    # Updates status only when worker is active.
    def _update_active_status(self, text, color_key):
        if self._get_is_enabled() and self._running and not self._shutting_down:
            self._update_status(text, color_key)
 
    # Thread-safe check if the worker is enabled.
    def _get_is_enabled(self):
        if self._shutting_down:
            return False
        try:
            return self.enabled_flag.get()
        except Exception:
            self._signal_gui_error_shutdown()
            return False
 
    # Signals immediate shutdown due to GUI error.
    def _signal_gui_error_shutdown(self):
        self._shutting_down = True
        self._running = False
 
    # Waits for a duration, checking for stop signals, resets, or disabled state.
    def _wait_with_checks(self, duration_seconds):
        start_time_wait = time()
        while time() - start_time_wait < duration_seconds:
            if not self._running or self._shutting_down: return False
            if self._check_and_perform_reset(): return False
            if not self._get_is_enabled(): return False
            sleep(0.01)
        return True
 
    # Resets core state variables for re-initialization or error recovery.
    def _reset_core_state_variables(self):
        self._pm = None
        self._hp_final_addr = None
        self._max_hp = None
        self._threshold = None
        self._alerted = False
        self._is_paused_by_window = False
        self._last_read_hp = None
        self._stable_hp_timestamp = None
 
    # Handles the state when the worker is disabled.
    def _handle_disabled_state(self):
        if self._is_active_logic_running:
            if not self._shutting_down:
                if self.gui is not None:
                    self.gui.set_status("OFF", config.COLOR_OFF)
                    self.gui.set_hp(None, None)
                    self.gui.set_threshold(None)
                else:
                    self._update_status("Auto Potion: OFF", config.COLOR_OFF)
            self._is_active_logic_running = False
            self._reset_core_state_variables()
        sleep(self._DISABLED_STATE_PAUSE)
 
    # Initializes state for active logic (process attachment, memory scanning).
    def _initialize_for_active_logic(self):
        if not self._is_active_logic_running:
            if not self._shutting_down:
                self._update_active_status("Searching for process...", config.COLOR_WAITING)
            self._is_active_logic_running = True
            self._reset_core_state_variables()
 
    # Attempts to attach to the target game process using Pymem.
    def _try_attach_process(self):
        if self._pm is not None: return True
 
        while self._should_continue_attempting_connection():
            try:
                self._pm = Pymem(config.PROCESS_NAME)
                if not self._shutting_down:
                    if not self._process_found_printed:
                        print(f"[DEBUG] Game process '{config.PROCESS_NAME}' found!")
                        self._process_found_printed = True
                    self._update_active_status(f"Process found.", config.COLOR_WAITING)
                return True
            except PymemError:
                if not self._shutting_down:
                    self._update_active_status(f"Waiting for process...", config.COLOR_WAITING)
            except Exception as e:
                if not self._shutting_down:
                    print(f"[ERROR] Error during process search: {str(e)[:100]}")
                self._pm = None
 
            if not self._wait_with_checks(config.WAIT_INTERVAL_PROCESS): return False
        return False
 
    # Attempts to find the HP memory address.
    def _try_find_hp_address(self):
        if self._hp_final_addr is not None and self._max_hp is not None: return True
 
        while self._should_continue_attempting_connection() and self._pm is not None:
            print("[DEBUG] Searching for HP address...")
 
            try:
                current_hp_addr = game_memory.get_hp_address(self._pm)
                if current_hp_addr is None:
                    if not self._handle_address_not_found_during_search(): return False
                    continue
 
                self._hp_final_addr = current_hp_addr
                print(f"[DEBUG] HP address found: 0x{self._hp_final_addr:X}")
                # Performs initial HP read to set max HP and threshold.
                self._perform_initial_hp_read_and_setup()
                return True
            except Exception as e:
                # Handles errors during address search.
                print(f"[ERROR] Error during address search: {str(e)[:100]}")
                self._reset_core_state_variables()
                self._is_active_logic_running = False
                return False
        return False
 
    # Handles scenario when HP address is not found during search.
    def _handle_address_not_found_during_search(self):
        try:
            module_from_name(self._pm.process_handle, config.MODULE_NAME)
        except PymemError:
            print("[DEBUG] Process lost during address search.")
            self._pm = None
            return False
        except Exception as e_proc_check:
            print(f"[ERROR] Error during process check: {str(e_proc_check)[:100]}")
            self._pm = None
            return False
 
        return self._wait_with_checks(config.WAIT_INTERVAL_MEMORY)
 
    # Performs initial HP read to set max HP and threshold.
    def _perform_initial_hp_read_and_setup(self):
        try:
            initial_hp = self._pm.read_float(self._hp_final_addr)
            if initial_hp > 0:
                self._max_hp = initial_hp
                self._threshold = self._max_hp * (self.user_cfg['THRESHOLD_PCT'] if self.user_cfg else config.THRESHOLD_PCT)
                self._last_read_hp = None
                self._stable_hp_timestamp = None
                self._alerted = False
                status_text = f"HP: {self._max_hp:.0f} / {self._max_hp:.0f} (100.0%) | Thresh: {self._threshold:.0f}"
                self._update_active_status(status_text, config.COLOR_ON)
            else:
                print("[DEBUG] HP address found. Waiting for positive HP value...")
        except Exception as read_err:
            print(f"[ERROR] HP address found. Error reading initial HP: {str(read_err)[:100]}")
 
    # Handles exceptions during address search.
    def _handle_address_search_exception(self, e):
        print(f"[ERROR] Error during address search: {str(e)[:100]}")
        self._reset_core_state_variables()
        self._is_active_logic_running = False
 
    # Main loop for monitoring HP and triggering potions.
    def _perform_hp_monitoring_cycle(self):
        last_addr_check_time = 0.0
 
        while self._should_continue_monitoring():
            if not self._get_is_enabled(): return False
            if self._check_and_perform_reset(): return False
 
            try:
                # Periodically re-checks HP pointer address.
                last_addr_check_time = self._reresolve_hp_pointer_if_needed(last_addr_check_time)
                # Checks if game is focused and pauses logic if not.
                if not self._is_game_focused_and_handle_pause():
                    continue
 
                # Reads current HP from memory.
                current_hp = self._read_current_hp_value()
                # Updates max HP logic based on stable HP.
                self._update_max_hp_logic(current_hp)
                # Updates GUI status.
                self._update_hp_status_display(current_hp)
                # Checks threshold and triggers potion if needed.
                self._apply_auto_potion_logic(current_hp)
 
            except Exception as e:
                # Handles errors during monitoring.
                self._handle_monitoring_error(e)
                return False
 
            if not self._wait_with_checks(config.INTERVAL): return False
        return False
 
    # Check conditions to continue HP monitoring loop.
    def _should_continue_monitoring(self):
        return (self._running and not self._shutting_down and
                self._pm is not None and self._hp_final_addr is not None)
 
    # Check conditions to continue attempting process/address connection.
    def _should_continue_attempting_connection(self):
        if self._check_and_perform_reset(): return False
        return self._running and not self._shutting_down and self._get_is_enabled()
 
    # Periodically re-resolves the HP pointer address.
    def _reresolve_hp_pointer_if_needed(self, last_check_time):
        current_time_val = time()
        if current_time_val - last_check_time > self._ADDRESS_CHECK_INTERVAL:
            new_addr = game_memory.get_hp_address(self._pm)
            if new_addr is None: self.debug_print("Periodic pointer re-resolution: new_addr is None.")
            if new_addr != self._hp_final_addr:
                print(f"[DEBUG] HP address changed: 0x{self._hp_final_addr:X} -> 0x{new_addr:X}")
                self._hp_final_addr = new_addr
            return current_time_val
        return last_check_time
 
    # Checks game window focus and pauses logic if not focused.
    def _is_game_focused_and_handle_pause(self):
        if not game_memory.is_target_window_foreground():
            if not self._is_paused_by_window:
                self._is_paused_by_window = True
                self._last_read_hp = None
                self._stable_hp_timestamp = None
                if not self._shutting_down:
                    if self.gui is not None:
                        self.gui.set_status("PAUSED", config.COLOR_PAUSED)
                    else:
                        self._update_active_status("PAUSED (Game not focused)", config.COLOR_PAUSED)
            self._wait_with_checks(config.INTERVAL)
            return False
        if self._is_paused_by_window: self._is_paused_by_window = False
        return True
 
    # Reads current HP value from memory.
    def _read_current_hp_value(self):
        current_hp = self._pm.read_float(self._hp_final_addr)
        if not isinstance(current_hp, float): raise ValueError("Invalid HP read type.")
        return current_hp
 
    # Logic to determine and update max HP based on stable HP.
    def _update_max_hp_logic(self, current_hp):
        if current_hp <= 0:
            self._last_read_hp = None
            self._stable_hp_timestamp = None
            return
 
        if self._last_read_hp is None or abs(current_hp - self._last_read_hp) > 0.01:
            self._last_read_hp = current_hp
            self._stable_hp_timestamp = time()
        elif self._stable_hp_timestamp is not None:
            elapsed_time = time() - self._stable_hp_timestamp
            # Update max HP if stable for required duration.
            if elapsed_time >= self._quick_stable_hp_duration and \
                    (self._max_hp is None or current_hp > self._max_hp):
                self._set_new_max_hp(current_hp)
            elif elapsed_time >= self._stable_hp_required_duration:
                if self._max_hp is None or abs(current_hp - self._max_hp) > 0.01:
                    self._set_new_max_hp(current_hp)
 
    # Sets new max HP and recalculates threshold.
    def _set_new_max_hp(self, new_max_hp):
        self._max_hp = new_max_hp
        self._threshold = self._max_hp * (self.user_cfg['THRESHOLD_PCT'] if self.user_cfg else config.THRESHOLD_PCT)
        self._alerted = False
        self._last_read_hp = None
        self._stable_hp_timestamp = None
 
    # Updates GUI status display with HP information.
    def _update_hp_status_display(self, current_hp):
        if self._shutting_down: return
        if self.gui is not None:
            if self._max_hp is not None and self._max_hp > 0:
                self.gui.hp_signal.emit(current_hp, self._max_hp)
                self.gui.threshold_signal.emit(self._threshold)
                self.gui.status_signal.emit("ON", config.COLOR_ON)
            elif self._max_hp is not None:
                self.gui.hp_signal.emit(current_hp, self._max_hp)
                self.gui.threshold_signal.emit(self._threshold)
                self.gui.status_signal.emit("ON", config.COLOR_ON)
            else:
                self.gui.hp_signal.emit(current_hp, None)
                self.gui.threshold_signal.emit(None)
                self.gui.status_signal.emit("WAITING", config.COLOR_WAITING)
        else:
            if self._max_hp is not None and self._max_hp > 0:
                self._update_active_status(f"HP: {current_hp:.0f}/{self._max_hp:.0f} ({(current_hp / self._max_hp) * 100:5.1f}%) | Threshold: {self._threshold:.0f}", config.COLOR_ON)
            elif self._max_hp is not None:
                self._update_active_status(f"HP: {current_hp:.0f}/{self._max_hp:.0f} | Threshold: {self._threshold:.0f}", config.COLOR_ON)
            else:
                self.debug_print(f"[DEBUG] HP: Determining Max HP... (Current: {current_hp:.0f})")
 
    # Checks if HP is below threshold and triggers potion key press.
    def _apply_auto_potion_logic(self, current_hp):
        if self._max_hp is not None and self._threshold is not None:
            from time import time
            now = time()
            if current_hp < self._threshold and (now - self._last_potion_time) >= self._potion_cooldown:
                send(str(self.user_cfg['POTION_KEY']) if self.user_cfg else str(config.POTION_KEY))
                self._last_potion_time = now
                if self.add_potion_log_callback:
                    try:
                        self.debug_print(f"[DEBUG] Logging potion use: HP={current_hp}, MaxHP={self._max_hp}")
                        if self.gui is not None:
                            self.gui.log_signal.emit(current_hp, self._max_hp)
                        else:
                            self.add_potion_log_callback(current_hp, self._max_hp)
                    except Exception as e:
                        self.debug_print(f"[ERROR] Error logging potion: {e}")
 
    # Handles errors during HP monitoring phase.
    def _handle_monitoring_error(self, e):
        if not self._shutting_down:
            error_prefix = "Process/Memory Error" if isinstance(e, PymemError) else "Error"
            self.debug_print(f"[ERROR] {error_prefix}: {str(e)[:100]}. Restarting search...")
        self._reset_core_state_variables()
        self._is_active_logic_running = False
        sleep(self._ERROR_RECOVERY_PAUSE)
 
    # Main execution method for the thread.
    def run(self):
        print("Worker Thread started.")
        while self._running and not self._shutting_down:
            if self._check_and_perform_reset():
                continue
 
            if not self._get_is_enabled():
                self._handle_disabled_state()
                continue
 
            # Initializes active logic state.
            self._initialize_for_active_logic()
 
            # Phase 1: Attempt to attach to process.
            if self._pm is None:
                if not self._try_attach_process(): continue
 
            # Phase 2: Attempt to find HP address.
            if self._pm is not None and self._hp_final_addr is None:
                if not self._try_find_hp_address(): continue
 
            # Phase 3: Monitor HP and apply logic.
            if self._pm is not None and self._hp_final_addr is not None:
                if not self._perform_hp_monitoring_cycle(): continue
 
        print("Worker Thread stopped.")
    
    
    def debug_print(self, message):
        if self.user_cfg['DEVELOPER_DEBUG']:
            print('> ' + message)
 
    # Signals the thread to stop gracefully.
    def stop(self):
        self._running = False
 
    # Signals the thread for immediate shutdown.
    def signal_shutdown(self):
        self._shutting_down = True
        self._running = False