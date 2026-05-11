import platform
import subprocess
import threading
import tkinter as tk
from datetime import datetime, timedelta
from pathlib import Path

# Audio files are stored inside the repository's audio/ folder.
BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio"

AUDIO_FILES = {
    "glass": AUDIO_DIR / "Glass.aiff",
    "ear_temperature": AUDIO_DIR / "测耳温.mp3",
    "body_weight": AUDIO_DIR / "称体重.mp3",
    "camera_and_treadmill": AUDIO_DIR / "请设置好红外摄像机和走步机控制器.mp3",
    "k5_mask_strap": AUDIO_DIR / "请准备好K5、面罩和绑带,并设置程序.mp3",
}


def play_audio(file_path: Path):
    """Play an audio file in a background thread.

    This application was originally written for macOS and uses afplay.
    On non-macOS systems, the function prints a warning instead of crashing.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        print(f"音频文件不存在: {file_path}")
        return

    if platform.system() != "Darwin":
        print(f"当前系统不是 macOS，请手动播放音频: {file_path}")
        return

    def _play():
        try:
            subprocess.run(["afplay", str(file_path)], check=False)
        except Exception as exc:
            print(f"播放音频失败: {file_path}，错误: {exc}")

    threading.Thread(target=_play, daemon=True).start()


def play_sound():
    """播放普通提示音"""
    play_audio(AUDIO_FILES["glass"])


def play_voice_alert(audio_key):
    """播放指定语音提醒"""
    play_audio(AUDIO_FILES[audio_key])


def build_alert_times(total_minutes):
    """Build all minutes that should trigger an alert sound."""
    base_alerts = {0, 20, 29, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 76, 80, 90}
    extended_alerts = set(range(80, total_minutes + 1, 5))
    return {minute for minute in (base_alerts | extended_alerts) if minute <= total_minutes}


def start_experiment(start_offset=0):
    """开始实验并更新进度"""
    global start_time, alert_times, experiment_started
    experiment_started = True
    start_time = datetime.now() - timedelta(seconds=start_offset)
    alert_times = build_alert_times(total_minutes)
    start_button.config(text="实验进行中", bg="red", fg="black")
    update_progress()


def update_progress():
    """更新实验进度和计时器显示"""
    now = datetime.now()
    elapsed_time = (now - start_time).total_seconds() / 60

    if elapsed_time <= total_minutes:
        current_minute = int(elapsed_time)

        if current_minute in alert_times:
            play_sound()
            alert_times.remove(current_minute)

            # 在特定时间点播放中文语音提醒
            if current_minute == 0:
                play_voice_alert("ear_temperature")
            elif current_minute == 29:
                play_voice_alert("camera_and_treadmill")
            elif current_minute == 30:
                play_voice_alert("ear_temperature")
                play_voice_alert("body_weight")
            elif current_minute == 76:
                play_voice_alert("k5_mask_strap")
            elif current_minute == 80:
                play_voice_alert("ear_temperature")
                play_voice_alert("body_weight")

        update_time_axis(current_minute)
        root.after(1000, update_progress)
    else:
        if total_minutes in alert_times:
            play_sound()
            alert_times.remove(total_minutes)

        update_time_axis(total_minutes)
        start_button.config(text="实验完成", bg="SystemButtonFace", fg="red")


def update_time_axis(minute):
    """根据当前分钟数更新时间轴颜色"""
    for current_minute in range(minute + 1):
        if current_minute < 31:
            fill_color = "#E5FEE2"
        elif current_minute < total_minutes - 10 + 1 and current_minute > 30:
            fill_color = "#E4F9FE"
        else:
            fill_color = "#FFD5ED"

        if current_minute < len(segments):
            time_axis_canvas.itemconfig(segments[current_minute], fill=fill_color)


def draw_time_axis(canvas):
    """绘制实验时间轴"""
    global segments
    segments = []
    start_x = 50
    segment_width = (1100 - 100) / (total_minutes + 1)

    canvas.delete("all")

    for i in range(total_minutes + 1):
        rect = canvas.create_rectangle(
            start_x + i * segment_width,
            40,
            start_x + (i + 1) * segment_width,
            60,
            fill="#D0D0D0",
            outline="",
        )
        segments.append(rect)

    tick_positions = [0, 20, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 90] + list(
        range(80, total_minutes + 1, 5)
    )
    adjust_positions = [20, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 90] + list(
        range(80, total_minutes + 1, 5)
    )
    phase_labels = [
        (17, "预暴露"),
        ((total_minutes + 22) // 2, "正式实验"),
        (total_minutes - 10 + 4, "代谢率测试"),
    ]

    for tick in sorted(set(tick_positions)):
        x_position = start_x + (tick if tick not in adjust_positions else tick + 1) * segment_width
        canvas.create_line(x_position, 60, x_position, 75, width=2)
        canvas.create_text(x_position, 85, text=str(tick), font=("Times New Roman", 30))

    for mid_point, label in phase_labels:
        x_label_position = start_x + mid_point * segment_width
        canvas.create_text(x_label_position, 20, text=label, font=("Times New Roman", 30), fill="black")


def update_time():
    """更新当前日期和时间"""
    now = datetime.now()
    date_label.config(text=now.strftime("%Y-%m-%d"))
    time_label.config(text=now.strftime("%H:%M:%S"))
    root.after(1000, update_time)


def focus_next_widget(event):
    """输入两位小时后自动跳到分钟输入框"""
    if len(hour_entry.get()) == 2:
        minute_entry.focus()


def check_time_and_update_button(event=None):
    """检查输入的时间并更新按钮文本"""
    try:
        hour = int(hour_entry.get())
        minute = int(minute_entry.get())

        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("时间超出范围")

        scheduled_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
        now = datetime.now()

        if scheduled_time <= now:
            start_button.config(text="直接开始", bg="green", fg="black")
        else:
            start_button.config(text="定时开始实验", bg="SystemButtonFace", fg="black")
    except ValueError:
        start_button.config(text="定时开始实验", bg="SystemButtonFace", fg="black")


def schedule_start():
    """按照输入的时间定时开始实验；如果时间已过，则按已过去的时长直接开始"""
    try:
        hour = int(hour_entry.get())
        minute = int(minute_entry.get())

        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("时间超出范围")

        scheduled_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
        now = datetime.now()

        delay = (scheduled_time - now).total_seconds()
        if delay < 0:
            start_offset = int(-delay)
            delay = 0
        else:
            start_offset = 0

        root.after(int(delay * 1000), lambda: start_experiment(start_offset))
        start_button.config(text="即将开始", bg="yellow", fg="black")
    except ValueError:
        print("请输入有效的时间，例如 09:30。")
    except Exception as exc:
        print(f"发生错误: {exc}")


def add_five_minutes():
    """增加五分钟到实验时间"""
    global total_minutes, alert_times
    total_minutes += 5
    alert_times = build_alert_times(total_minutes)
    draw_time_axis(time_axis_canvas)

    if experiment_started:
        elapsed_minutes = int((datetime.now() - start_time).total_seconds() / 60)
        update_time_axis(elapsed_minutes)


def setup_gui():
    """初始化图形界面"""
    global root, date_label, time_label, hour_entry, minute_entry
    global start_button, time_axis_canvas, total_minutes, experiment_started

    root = tk.Tk()
    root.title("实验控制")
    root.geometry("1500x1000")

    total_minutes = 90
    experiment_started = False

    date_label = tk.Label(root, font=("Times New Roman", 60))
    time_label = tk.Label(root, font=("Times New Roman", 100))
    date_label.place(relx=0.5, rely=0.1, anchor="center")
    time_label.place(relx=0.5, rely=0.25, anchor="center")

    hour_entry = tk.Entry(root, width=2, font=("Times New Roman", 50))
    minute_entry = tk.Entry(root, width=2, font=("Times New Roman", 50))
    hour_entry.place(relx=0.5, rely=0.7, anchor="e", x=-30)
    minute_entry.place(relx=0.5, rely=0.7, anchor="w", x=30)
    hour_entry.bind("<KeyRelease>", focus_next_widget)
    minute_entry.bind("<KeyRelease>", check_time_and_update_button)

    start_button = tk.Button(root, text="定时开始实验", command=schedule_start, font=("Songti SC", 50))
    start_button.place(relx=0.5, rely=0.8, anchor="center")

    add_time_button = tk.Button(root, text="+5分钟", command=add_five_minutes, font=("Songti SC", 50))
    add_time_button.place(relx=0.75, rely=0.8, anchor="center")

    time_axis_canvas = tk.Canvas(root, width=1100, height=300)
    time_axis_canvas.place(relx=0.5, rely=0.5, anchor="center")
    draw_time_axis(time_axis_canvas)

    update_time()

    return root


if __name__ == "__main__":
    root = setup_gui()
    root.mainloop()
