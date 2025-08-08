import ctypes
import io
import json
import os
import subprocess
import sys
import threading
import time
import tkinter
from tkinter import ttk
import logging
import traceback
from PIL import Image, ImageTk

logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s',
                    level=logging.INFO,
                    datefmt='%Y/%m/%d %H:%M:%S')
h = logging.FileHandler("LJ360SM.log", "a", "utf-8")
h.setFormatter(logging.Formatter(fmt='[%(asctime)s] %(levelname)s: %(message)s',
                                 datefmt='%Y/%m/%d %H:%M:%S'))
h.setLevel(logging.INFO)
logging.getLogger().addHandler(h)

import psutil
from SysTrayIcon import SysTrayIcon


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


kill_dict = {
    "ADs": (
        "360垃圾广告",
        {
            "sesvcr.exe",
            "multitip.exe",
            "sesvr.exe",
            "sesvc.exe",
            "SeAppService.exe"
        }
    ),
    "WasteTip": (
        "清理垃圾提醒",
        {
            "360CleanHelper.exe"
        }
    ),
    "ClockTip": (
        "360日历的提醒",
        {
            "GameChrome.exe"
        }
    ),
    "StartCount": (
        "360开机计时",
        {
            "360speedld.exe",
            "360SpeedldEx.exe"
        }
    )
}

last_protect = time.time()

def save_setting():
    global last_protect
    setting["protectTime"] += time.time() - last_protect
    last_protect = time.time()
    with open("LJ360SM.config.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(setting))


def show_time(st=None):
    if st is None:
        st = setting["protectTime"]
    x = int(st + time.time() - last_protect)
    sl = []
    for v, n in [(60, "秒"),
                 (60, "分"),
                 (24, "时"),
                 (30, "日"),
                 (12, "月"),
                 (None, "年")]:
        if v:
            sl.append(f'{x % v}{n}')
            x //= v
            if x == 0:
                break
        else:
            sl.append(f'{x}{n}')
    return ''.join(sl[::-1])


if is_admin():
    running = True
    logging.info('=' * 20)
    if os.path.exists("LJ360SM.config.json"):
        with open("LJ360SM.config.json", encoding="utf-8") as f:
            setting = json.loads(f.read())
    else:
        setting = {
            "count": 0,
            "filters": [
                "ADs"
            ],
            "protectTime": 0
        }
    count_at = setting["count"]
    start_at = setting["protectTime"]
    kill_target = set()
    for k in setting["filters"]:
        kill_target |= kill_dict[k][1]


    def LJ360SM():
        logging.info("LJ360SM 已启动")
        while running:
            changed = False
            pids = psutil.pids()
            for pid in pids:
                try:
                    p = psutil.Process(pid)
                    pid_name = p.name()
                    if pid_name in kill_target:
                        logging.info(f"探测到{pid_name},终止进程")
                        p = subprocess.run(f'taskkill /f /im {pid_name}', shell=True, text=True, stdout=subprocess.PIPE,
                                           stderr=subprocess.STDOUT)
                        changed = True
                        l = [(logging.info if p.returncode == 0 else logging.warning)(f"{line}") for line in
                             p.stdout.strip().split('\n')]
                        setting["count"] += (len(l) if p.returncode == 0 else 0)
                except Exception as e:
                    try:
                        traceback.print_last()
                    except:
                        pass
            if changed:
                save_setting()
            time.sleep(1)


    threading.Thread(target=LJ360SM).start()

    root = tkinter.Tk()
    root.withdraw()

    icons = 'LJ360SM.ico'
    hover_text = "垃圾360死🐎 - 360广告屏蔽器"
    # pic = tkinter.BitmapImage(file="LJ360SM.png")
    pic_open = Image.open("LJ360SM.png").resize((600, 170))
    pic = ImageTk.PhotoImage(pic_open)


    def show_about(*_):
        about = tkinter.Toplevel()
        about.title("关于")
        tkinter.Label(about, image=pic).pack()
        tkinter.Label(about, text="""垃圾360死妈 - 360广告屏蔽器
此项目旨在将360净化，让弹窗去死吧！""", font=("LXGW WenKai", 20, "normal")).pack()
        def f1(*_):
            about.destroy()
            show_count()
        tkinter.Button(about, text="转到 统计数据", command=f1, font=("LXGW WenKai", 15, "italic")).pack()
        def f2(*_):
            about.destroy()
            config()
        tkinter.Button(about, text="转到 设置", command=f2, font=("LXGW WenKai", 15, "italic")).pack()


    def show_count(*_):
        count = tkinter.Toplevel()
        count.title("统计数据")
        tkinter.Label(count, image=pic).pack()
        v3 = tkinter.StringVar(value=f"本次启动关闭广告次数(以进程计): {setting['count']-count_at}")
        tkinter.Label(count, textvariable=v3, font=("LXGW WenKai", 15, "normal")).pack()
        v4 = tkinter.StringVar(value=f"本次启动守护时长: {show_time(setting['protectTime']-start_at)}")
        tkinter.Label(count, textvariable=v4, font=("LXGW WenKai", 15, "normal")).pack()
        v1 = tkinter.StringVar(value=f"累计关闭广告次数(以进程计): {setting['count']}")
        tkinter.Label(count, textvariable=v1, font=("LXGW WenKai", 15, "normal")).pack()
        v2 = tkinter.StringVar(value=f"累计守护时长: {show_time(setting['protectTime'])}")
        tkinter.Label(count, textvariable=v2, font=("LXGW WenKai", 15, "normal")).pack()
        def fr():
            count.destroy()
            show_about()
        tkinter.Button(count, text="回到 关于", command=fr, font=("LXGW WenKai", 15, "italic")).pack()

        def update():
            v1.set(f"累计关闭广告次数(以进程计): {setting['count']}")
            v2.set(f"累计守护时长: {show_time(setting['protectTime'])}")
            v3.set(f"本次启动关闭广告次数(以进程计): {setting['count']-count_at}")
            v4.set(f"本次启动守护时长: {show_time(setting['protectTime']-start_at)}")
            count.after(100, update)

        count.after(100, update)

    def config(*_):
        cfw = tkinter.Toplevel()
        cfw.title("设置")
        tkinter.Label(cfw, image=pic).pack()
        def on_command(k, apps, var):
            def inner():
                global kill_target
                if var.get():
                    kill_target |= apps
                    setting["filters"].append(k)
                    logging.info(f"添加过滤 {k}, 过滤列表变为 {kill_target}")
                else:
                    kill_target -= apps
                    setting["filters"].remove(k)
                    logging.info(f"移除过滤 {k}, 过滤列表变为 {kill_target}")
                save_setting()
            return inner
        tkinter.Label(cfw, text="过滤以下弹窗：（技术原因，暂不支持更多）", font=("LXGW WenKai", 15, "normal")).pack()
        for k in kill_dict:
            name, apps = kill_dict[k]
            var = tkinter.BooleanVar(value=(k in setting['filters']))
            tkinter.Checkbutton(cfw, variable=var, text=name, command=on_command(k, apps, var), font=("LXGW WenKai", 12, "normal"), state='disabled').pack()
        def fr():
            cfw.destroy()
            show_about()
        tkinter.Button(cfw, text="回到 关于", command=fr, font=("LXGW WenKai", 15, "italic")).pack()


    menu_options = (('关于……', None, show_about),
                    ('统计数据', None, show_count),
                    ('设置', None, config))


    def bye(sysTrayIcon):
        global running
        running = False
        logging.info('LJ360SM 关闭了')
        save_setting()


    threading.Thread(
        target=lambda: SysTrayIcon(icons, hover_text, menu_options, on_quit=bye, default_menu_index=1, on_l=show_about)
    ).start()


    def check_running():
        if not running:
            root.destroy()
        else:
            root.after(1000, check_running)


    root.after(1000, check_running)

    root.mainloop()
else:
    # re-run the script with admin rights
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
