import subprocess
import sys
import os
import ctypes
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_cmd(cmd):
    return subprocess.run(
        cmd, 
        capture_output=True, 
        text=True, 
        shell=True, 
        creationflags=subprocess.CREATE_NO_WINDOW
    )

def get_current_lid_action():
    res = run_cmd("powercfg /QUERY SCHEME_CURRENT SUB_BUTTONS LIDACTION")
    for line in res.stdout.splitlines():
        if "0x" in line:
            val = line.split(":")[-1].strip()
            try:
                return int(val, 16)
            except ValueError:
                continue
    return 1

is_nosleep = (get_current_lid_action() == 0)

def apply_no_sleep():
    run_cmd("powercfg /SETACVALUEINDEX SCHEME_CURRENT SUB_BUTTONS LIDACTION 0")
    run_cmd("powercfg /SETDCVALUEINDEX SCHEME_CURRENT SUB_BUTTONS LIDACTION 0")
    run_cmd("powercfg /SETACVALUEINDEX SCHEME_CURRENT SUB_SLEEP STANDBYIDLE 0")
    run_cmd("powercfg /SETDCVALUEINDEX SCHEME_CURRENT SUB_SLEEP STANDBYIDLE 0")
    run_cmd("powercfg /SETACVALUEINDEX SCHEME_CURRENT SUB_VIDEO VIDEOIDLE 0")
    run_cmd("powercfg /SETDCVALUEINDEX SCHEME_CURRENT SUB_VIDEO VIDEOIDLE 0")
    run_cmd("powercfg /SETACTIVE SCHEME_CURRENT")

def apply_sleep():
    run_cmd("powercfg /SETACVALUEINDEX SCHEME_CURRENT SUB_BUTTONS LIDACTION 1")
    run_cmd("powercfg /SETDCVALUEINDEX SCHEME_CURRENT SUB_BUTTONS LIDACTION 1")
    run_cmd("powercfg /SETACVALUEINDEX SCHEME_CURRENT SUB_VIDEO VIDEOIDLE 300")
    run_cmd("powercfg /SETACVALUEINDEX SCHEME_CURRENT SUB_SLEEP STANDBYIDLE 300")
    run_cmd("powercfg /SETDCVALUEINDEX SCHEME_CURRENT SUB_VIDEO VIDEOIDLE 180")
    run_cmd("powercfg /SETDCVALUEINDEX SCHEME_CURRENT SUB_SLEEP STANDBYIDLE 180")
    run_cmd("powercfg /SETACTIVE SCHEME_CURRENT")

def set_no_sleep_mode(icon=None, item=None):
    global is_nosleep
    apply_no_sleep()
    is_nosleep = True
    update_ui(icon)

def set_sleep_mode(icon=None, item=None):
    global is_nosleep
    apply_sleep()
    is_nosleep = False
    update_ui(icon)

def toggle_mode(icon=None, item=None):
    if is_nosleep:
        set_sleep_mode(icon)
    else:
        set_no_sleep_mode(icon)

def create_icon(color):
    image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    d.ellipse([8, 8, 56, 56], fill=color)
    return image

def update_ui(icon):
    if not icon:
        return
    
    if is_nosleep:
        icon.icon = create_icon('#ff4d4d')
        icon.title = "НЕ СПАТЬ (Экран/Сон выкл)"
    else:
        icon.icon = create_icon('#4da6ff')
        icon.title = "СОН (Сеть: 5м | Батарея: 3м)"
        
    icon.menu = build_menu()

def build_menu():
    return pystray.Menu(
        item('Не гаснуть', set_no_sleep_mode, checked=lambda item: is_nosleep),
        item('Обычный режим', set_sleep_mode, checked=lambda item: not is_nosleep),
        pystray.Menu.SEPARATOR,
        item('Выход', lambda icon, item: icon.stop())
    )

if __name__ == '__main__':
    if not is_admin():
        pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        executable = pythonw if os.path.exists(pythonw) else sys.executable
        ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, f'"{__file__}"', None, 0)
        sys.exit()

    initial_color = '#ff4d4d' if is_nosleep else '#4da6ff'
    initial_title = "НЕ СПАТЬ" if is_nosleep else "СОН"

    icon = pystray.Icon(
        "MonitorSleeper",
        create_icon(initial_color),
        initial_title,
        menu=build_menu()
    )

    icon.default_action = toggle_mode
    icon.run()