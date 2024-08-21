import argparse
import sys

import base64
import ctypes
import ctypes.wintypes
import win32process
import win32api
import win32con

from pathlib import Path

from thps_formats.scripting2.qb import QB
from thps_formats.scripting2.enums import TokenType
from thps_formats.shared.enums import GameVersion


# ----------------------------------------------------------------------------------------------------
PROCESS_NAME = 'thugpro.exe'
COMPILER_PARAMS = {'debug': False, 'game': GameVersion.THUGPRO_WIN}
UPDATE_ADDRESS = 0x007CE4A0 # runmenow flag (thugpro.exe)


# -------------------------------------------------------------------------------------------------
def get_process_by_name(process_name):
    for proc in win32process.EnumProcesses():
        try:
            hprocess = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, proc)
            exe = win32process.GetModuleFileNameEx(hprocess, 0)
            if process_name.lower() in exe.lower():
                return hprocess, proc, exe
        except Exception:
            pass
    return None


# -------------------------------------------------------------------------------------------------
def read_process_memory(process, address, size):
    buffer = ctypes.create_string_buffer(size)
    bytes_read = ctypes.c_size_t()
    ctypes.windll.kernel32.ReadProcessMemory(
        process.handle,
        ctypes.c_void_p(address),
        buffer,
        size,
        ctypes.byref(bytes_read)
    )
    return buffer.raw


# -------------------------------------------------------------------------------------------------
def write_process_memory(process, address, data):
    size = len(data)
    buffer = ctypes.create_string_buffer(data)
    bytes_written = ctypes.c_size_t()
    ctypes.windll.kernel32.WriteProcessMemory(
        process.handle,
        ctypes.c_void_p(address),
        buffer,
        size,
        ctypes.byref(bytes_written)
    )
    return bytes_written.value


# -------------------------------------------------------------------------------------------------
def compile(source, output):

    qb = QB.from_string(source, COMPILER_PARAMS)
    if qb is None:
        raise ValueError('Failed to parse q source')

    if not any(token['type'] == TokenType.KEYWORD_SCRIPT for token in qb.tokens):
        print('WARNING: Wrapping inlined code!')
        wrapped = F"script RunMeNow2\n{source}\nendscript"
        return compile(wrapped, output)

    qb.to_file(output, COMPILER_PARAMS)
    return qb is not None


# -------------------------------------------------------------------------------------------------
def notify(process):
    return write_process_memory(process, UPDATE_ADDRESS, b'\x01') > 0


# -------------------------------------------------------------------------------------------------
def main(args):

    decoded = base64.urlsafe_b64decode(args.source.encode()).decode()
    if decoded is None:
        raise ValueError('Failed to decode input...')

    process, pid, exe = get_process_by_name(PROCESS_NAME)
    if process is None:
        raise ProcessLookupError('Could not find a running process...')

    output = Path(exe).parent / 'RunMeNow.qb'
    if compile(decoded, output):
        return notify(process)

    return False


# -------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='runmenow')
    parser.add_argument('source', nargs='?', type=str, help='q source code base64 encoded')
    args = parser.parse_args()
    try:
        success = main(args)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(e)
        sys.exit(1)
