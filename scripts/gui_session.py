#!/usr/bin/env python3
# Copyright 2026 YOSHIDA-V (ROS 2 Jazzy modifications)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Keep a GUI launch's ROS services alive until its owned RViz has exited."""
import ctypes as C
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid

from ament_index_python.packages import get_package_prefix


def rviz_processes(session):
    executables = {
        str((Path(get_package_prefix('rviz2')) / 'lib/rviz2/rviz2').resolve()),
        str((Path(get_package_prefix('megarover_description')) /
             'lib/megarover_description/rviz_no_prompt').resolve()),
    }
    marker = ('MEGAROVER_GUI_SESSION=' + session).encode()
    result = []
    for entry in Path('/proc').iterdir():
        if not entry.name.isdecimal():
            continue
        try:
            if (marker in (entry / 'environ').read_bytes().split(b'\0') and
                    str((entry / 'exe').resolve()) in executables):
                result.append(int(entry.name))
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            pass
    return result


def close_windows(pid, already_closed=()):
    class Data(C.Union):
        _fields_ = [('bytes', C.c_char * 20), ('shorts', C.c_short * 10), ('longs', C.c_long * 5)]

    class Client(C.Structure):
        _fields_ = [('type', C.c_int), ('serial', C.c_ulong), ('send_event', C.c_int),
                    ('display', C.c_void_p), ('window', C.c_ulong), ('message_type', C.c_ulong),
                    ('format', C.c_int), ('data', Data)]

    class Event(C.Union):
        _fields_ = [('client', Client), ('padding', C.c_long * 24)]

    lib = C.CDLL('libX11.so.6')
    lib.XOpenDisplay.argtypes = [C.c_char_p]
    lib.XOpenDisplay.restype = C.c_void_p
    lib.XDefaultRootWindow.argtypes = [C.c_void_p]
    lib.XDefaultRootWindow.restype = C.c_ulong
    lib.XInternAtom.argtypes = [C.c_void_p, C.c_char_p, C.c_int]
    lib.XInternAtom.restype = C.c_ulong
    lib.XGetWindowProperty.argtypes = [
        C.c_void_p, C.c_ulong, C.c_ulong, C.c_long, C.c_long,
        C.c_int, C.c_ulong, C.POINTER(C.c_ulong), C.POINTER(C.c_int), C.POINTER(C.c_ulong),
        C.POINTER(C.c_ulong), C.POINTER(C.POINTER(C.c_ubyte))]
    lib.XFree.argtypes = [C.c_void_p]
    lib.XSendEvent.argtypes = [C.c_void_p, C.c_ulong, C.c_int, C.c_long, C.POINTER(Event)]
    lib.XFlush.argtypes = [C.c_void_p]
    lib.XCloseDisplay.argtypes = [C.c_void_p]
    error_handler = C.CFUNCTYPE(C.c_int, C.c_void_p, C.c_void_p)(lambda *_: 0)
    lib.XSetErrorHandler.argtypes = [C.c_void_p]
    lib.XSetErrorHandler.restype = C.c_void_p
    previous_error_handler = lib.XSetErrorHandler(error_handler)
    display = lib.XOpenDisplay(os.environ['DISPLAY'].encode())
    if not display:
        lib.XSetErrorHandler(previous_error_handler)
        raise RuntimeError('X display unavailable for owned RViz')
    try:
        def atom(name):
            return lib.XInternAtom(display, name.encode(), 0)

        def values(window, name):
            actual, count, remaining = C.c_ulong(), C.c_ulong(), C.c_ulong()
            fmt, data = C.c_int(), C.POINTER(C.c_ubyte)()
            status = lib.XGetWindowProperty(
                display, window, atom(name), 0, 1024, 0, 0,
                C.byref(actual), C.byref(fmt), C.byref(count), C.byref(remaining), C.byref(data))
            try:
                return (list(C.cast(data, C.POINTER(C.c_ulong))[:count.value])
                        if status == 0 and fmt.value == 32 and data else [])
            finally:
                if data:
                    lib.XFree(data)

        sent = []
        for window in values(lib.XDefaultRootWindow(display), '_NET_CLIENT_LIST'):
            if hex(window) in already_closed:
                continue
            if (values(window, '_NET_WM_PID') != [pid]
                    or atom('_NET_WM_WINDOW_TYPE_NORMAL') not in values(
                        window, '_NET_WM_WINDOW_TYPE')
                    or atom('WM_DELETE_WINDOW') not in values(window, 'WM_PROTOCOLS')):
                continue
            event = Event()
            event.client.type = 33
            event.client.send_event = 1
            event.client.display = display
            event.client.window = window
            event.client.message_type = atom('WM_PROTOCOLS')
            event.client.format = 32
            event.client.data.longs[0] = atom('WM_DELETE_WINDOW')
            if not lib.XSendEvent(display, window, 0, 0, C.byref(event)):
                raise RuntimeError('Could not close owned RViz client')
            sent.append(hex(window))
        lib.XFlush(display)
        return sent
    finally:
        lib.XCloseDisplay(display)
        lib.XSetErrorHandler(previous_error_handler)


def main(before_backend_stop=None):
    requested = []

    def stop(signum, _frame):
        if not requested:
            requested.append(signum)

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    session = str(uuid.uuid4())
    reader, writer = os.pipe()
    os.set_blocking(reader, False)
    env = dict(os.environ, MEGAROVER_GUI_SESSION=session, MEGAROVER_GUI_STATUS_FD=str(writer))
    command = sys.argv[1:]
    child = subprocess.Popen(command, env=env, pass_fds=(writer,), start_new_session=True)
    os.close(writer)
    print(json.dumps({
        'gui_session': session, 'backend_pid': child.pid,
        'argv': command, 'cwd': os.getcwd()}), flush=True)
    closed, signalled, gui_code = set(), False, None
    stop_failed = False
    pending = b''
    try:
        while child.poll() is None:
            try:
                pending += os.read(reader, 4096)
            except BlockingIOError:
                pass
            if b'\n' in pending:
                line, pending = pending.split(b'\n', 1)
                status = json.loads(line)
                gui_code = status['returncode']
                print(json.dumps({'gui_exit': status}), flush=True)
                if not requested:
                    requested.append(0)
            if requested and not signalled:
                pids = rviz_processes(session)
                if not pids:
                    if before_backend_stop:
                        try:
                            before_backend_stop()
                        except Exception as error:
                            stop_failed = True
                            print(json.dumps({'backend_stop_error': str(error)}), flush=True)
                    os.killpg(child.pid, signal.SIGINT)
                    signalled = True
                    print(json.dumps({'backend_sigint_after_gui_exit': child.pid}), flush=True)
                else:
                    for pid in pids:
                        windows = close_windows(pid, closed)
                        if windows:
                            closed.update(windows)
                            print(json.dumps({
                                'owned_rviz_close': pid, 'windows': windows}), flush=True)
            time.sleep(0.05)
        code = 1 if stop_failed else (gui_code if gui_code not in (None, 0) else child.returncode)
        return code if code >= 0 else 128 - code
    finally:
        os.close(reader)
        if child.poll() is None:
            os.killpg(child.pid, signal.SIGINT)
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGTERM)
                child.wait(timeout=5)


if __name__ == '__main__':
    raise SystemExit(main())
