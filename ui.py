import json
import threading
import time
import tkinter as tk
from tkinter import messagebox, simpledialog
import numpy as np
import serial
import serial.tools.list_ports
from PIL import Image, ImageDraw

# --- Configuration ---
BAUD_RATE = 115200
CANVAS_SIZE = 280
OUTPUT_SIZE = 28

# --- Modern Theme Colors ---
BG_COLOR = "#0F0F1A"          # 深邃夜空背景
CARD_COLOR = "#1A1A2E"        # 卡片背景（深紫灰）
CARD_BORDER = "#2A2A4A"       # 卡片边框
TEXT_COLOR = "#E8E8F0"        # 主文字色
TEXT_MUTED = "#6C6C8A"        # 辅助文字色
ACCENT_COLOR = "#7C5CFC"      # 紫色强调色（主色调）
ACCENT_GLOW = "#9D7CFF"       # 紫色高光
SECOND_ACCENT = "#FF6B9D"     # 粉红辅助色
SUCCESS_COLOR = "#4ADE80"     # 成功绿色
WARNING_COLOR = "#FBBF24"     # 警告黄色
BAR_BG = "#252540"            # 进度条背景
BAR_GRADIENT_1 = "#7C5CFC"    # 进度条渐变起始
BAR_GRADIENT_2 = "#A78BFA"    # 进度条渐变结束
BTN_HOVER = "#6A4CE0"         # 按钮悬停色
BTN_SECONDARY = "#2D2D4A"     # 次要按钮背景
BTN_SECONDARY_HOVER = "#3D3D5A"

def select_port():
    """弹出对话框让用户手动选择串口号"""
    ports = serial.tools.list_ports.comports()
    port_list = [p.device for p in ports]
    if not port_list:
        port_list = ["COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", "COM10"]

    # 创建一个现代风格的选择窗口
    sel = tk.Tk()
    sel.title("Select COM Port")
    sel.geometry("340x200")
    sel.configure(bg=BG_COLOR)
    sel.resizable(False, False)

    # 标题
    tk.Label(sel, text="🔌 Serial Port Selection", font=("Segoe UI", 12, "bold"),
             bg=BG_COLOR, fg=TEXT_COLOR).pack(pady=(20, 5))
    tk.Label(sel, text="Choose a port to connect:", font=("Segoe UI", 9),
             bg=BG_COLOR, fg=TEXT_MUTED).pack(pady=(0, 10))

    selected_port = tk.StringVar(sel)
    selected_port.set(port_list[0] if port_list else "COM8")

    # 自定义下拉菜单样式
    port_menu = tk.OptionMenu(sel, selected_port, *port_list)
    port_menu.config(font=("Consolas", 10), bg=CARD_COLOR, fg=TEXT_COLOR,
                     activebackground=BTN_HOVER, activeforeground="white",
                     relief="flat", highlightthickness=1, highlightbackground=CARD_BORDER,
                     bd=0, padx=10, pady=4)
    port_menu["menu"].config(bg=CARD_COLOR, fg=TEXT_COLOR,
                             activebackground=BTN_HOVER, activeforeground="white",
                             bd=0)
    port_menu.pack(pady=5)

    result = {"port": None}

    def on_ok():
        result["port"] = selected_port.get()
        sel.destroy()

    def on_cancel():
        sel.destroy()

    btn_frame = tk.Frame(sel, bg=BG_COLOR)
    btn_frame.pack(pady=(15, 10))

    tk.Button(btn_frame, text="Connect", command=on_ok,
              bg=ACCENT_COLOR, fg="white", font=("Segoe UI", 10, "bold"),
              relief="flat", padx=25, pady=6, cursor="hand2",
              activebackground=BTN_HOVER).pack(side=tk.LEFT, padx=8)

    tk.Button(btn_frame, text="Cancel", command=on_cancel,
              bg=BTN_SECONDARY, fg=TEXT_COLOR, font=("Segoe UI", 10),
              relief="flat", padx=25, pady=6, cursor="hand2",
              activebackground=BTN_SECONDARY_HOVER).pack(side=tk.LEFT, padx=8)

    sel.protocol("WM_DELETE_WINDOW", on_cancel)
    sel.grab_set()
    sel.wait_window()

    return result["port"]


class MnistDigitApp:
    def __init__(self, root, port):
        self.root = root
        self.root.title("PICO-MNIST EDGE AI")
        self.root.geometry("620x720")
        self.root.configure(bg=BG_COLOR)
        self.root.minsize(580, 680)

        self.ser = None
        self._lock = threading.Lock()
        self._busy = False
        self.port = port

        self.setup_ui()
        self.init_serial()

    def setup_ui(self):
        # ========== 1. Header with decorative line ==========
        header_frame = tk.Frame(self.root, bg=BG_COLOR)
        header_frame.pack(pady=(20, 5), fill=tk.X)

        # 装饰性顶部线条
        deco_line = tk.Frame(header_frame, height=3, bg=ACCENT_COLOR)
        deco_line.pack(fill=tk.X, padx=60, pady=(0, 12))

        header = tk.Label(header_frame, text="NEURAL INFERENCE TERMINAL",
                          font=("Segoe UI", 15, "bold"),
                          bg=BG_COLOR, fg=TEXT_COLOR)
        header.pack()

        subtitle = tk.Label(header_frame, text="Pico 2 · Edge AI · MNIST",
                           font=("Segoe UI", 9), bg=BG_COLOR, fg=TEXT_MUTED)
        subtitle.pack(pady=(2, 0))

        # ========== 2. Drawing Canvas with card-style container ==========
        canvas_card = tk.Frame(self.root, bg=CARD_COLOR, bd=0,
                               highlightbackground=CARD_BORDER, highlightthickness=1,
                               padx=12, pady=12)
        canvas_card.pack(pady=(15, 5))

        canvas_label = tk.Label(canvas_card, text="✏️ Draw a digit",
                                font=("Segoe UI", 9), bg=CARD_COLOR, fg=TEXT_MUTED)
        canvas_label.pack(anchor="w", pady=(0, 6))

        self.canvas = tk.Canvas(canvas_card, width=CANVAS_SIZE, height=CANVAS_SIZE,
                                bg="#0A0A14", highlightthickness=0, cursor="pencil")
        self.canvas.pack()
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<Button-1>", self.paint)

        self.image = Image.new("L", (CANVAS_SIZE, CANVAS_SIZE), 0)
        self.draw = ImageDraw.Draw(self.image)

        # ========== 3. Control Buttons ==========
        btn_frame = tk.Frame(self.root, bg=BG_COLOR)
        btn_frame.pack(pady=(18, 10))

        # Recognize button - primary
        self.rec_btn = tk.Button(btn_frame, text="▶ RECOGNIZE", bg=ACCENT_COLOR,
                                 fg="white", font=("Segoe UI", 10, "bold"),
                                 relief="flat", padx=28, pady=10, cursor="hand2",
                                 activebackground=BTN_HOVER,
                                 command=self.send_data)
        self.rec_btn.pack(side=tk.LEFT, padx=8)

        # Clear button - secondary
        self.clear_btn = tk.Button(btn_frame, text="✕ CLEAR", bg=BTN_SECONDARY,
                                   fg=TEXT_COLOR, font=("Segoe UI", 10, "bold"),
                                   relief="flat", padx=28, pady=10, cursor="hand2",
                                   activebackground=BTN_SECONDARY_HOVER,
                                   command=self.clear_canvas)
        self.clear_btn.pack(side=tk.LEFT, padx=8)

        # ========== 4. Result & Visualization Card ==========
        viz_container = tk.Frame(self.root, bg=CARD_COLOR, bd=0,
                                 highlightbackground=CARD_BORDER, highlightthickness=1,
                                 padx=24, pady=20)
        viz_container.pack(fill=tk.X, padx=40, pady=(10, 5))

        # Result section header
        result_header = tk.Frame(viz_container, bg=CARD_COLOR)
        result_header.pack(fill=tk.X, pady=(0, 12))

        tk.Label(result_header, text="📊 Inference Result",
                 font=("Segoe UI", 10, "bold"), bg=CARD_COLOR, fg=TEXT_COLOR).pack(side=tk.LEFT)

        # Left Side: Large digit display
        res_text_frame = tk.Frame(viz_container, bg=CARD_COLOR)
        res_text_frame.pack(side=tk.LEFT, expand=True, fill=tk.Y)

        tk.Label(res_text_frame, text="PREDICTION", font=("Segoe UI", 8, "bold"),
                 bg=CARD_COLOR, fg=TEXT_MUTED).pack()

        # 数字显示带发光效果（通过边框模拟）
        digit_display_frame = tk.Frame(res_text_frame, bg=CARD_COLOR,
                                       highlightbackground=ACCENT_COLOR, highlightthickness=2,
                                       padx=15, pady=5)
        digit_display_frame.pack(pady=(5, 0))

        self.digit_label = tk.Label(digit_display_frame, text="-",
                                    font=("Segoe UI", 52, "bold"),
                                    bg=CARD_COLOR, fg=ACCENT_COLOR)
        self.digit_label.pack()

        # Right Side: Confidence Bars
        bars_frame = tk.Frame(viz_container, bg=CARD_COLOR)
        bars_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(20, 0))

        # Bar 1 (Top 1)
        bar1_header = tk.Frame(bars_frame, bg=CARD_COLOR)
        bar1_header.pack(fill=tk.X)
        self.bar1_label = tk.Label(bar1_header, text="[?]  --%",
                                   font=("Consolas", 9, "bold"), bg=CARD_COLOR, fg=TEXT_COLOR)
        self.bar1_label.pack(side=tk.LEFT)
        tk.Label(bar1_header, text="TOP-1", font=("Segoe UI", 7, "bold"),
                 bg=CARD_COLOR, fg=TEXT_MUTED).pack(side=tk.RIGHT)

        self.bar1_canvas = tk.Canvas(bars_frame, width=160, height=14,
                                     bg=BAR_BG, highlightthickness=0)
        self.bar1_canvas.pack(pady=(4, 14))
        # 圆角效果通过两层实现
        self.bar1_bg = self.bar1_canvas.create_rectangle(0, 0, 160, 14,
                                                          fill=BAR_BG, outline="")
        self.bar1_fill = self.bar1_canvas.create_rectangle(0, 0, 0, 14,
                                                           fill=ACCENT_COLOR, outline="")

        # Bar 2 (Top 2)
        bar2_header = tk.Frame(bars_frame, bg=CARD_COLOR)
        bar2_header.pack(fill=tk.X)
        self.bar2_label = tk.Label(bar2_header, text="[?]  --%",
                                   font=("Consolas", 9, "bold"), bg=CARD_COLOR, fg=TEXT_COLOR)
        self.bar2_label.pack(side=tk.LEFT)
        tk.Label(bar2_header, text="TOP-2", font=("Segoe UI", 7, "bold"),
                 bg=CARD_COLOR, fg=TEXT_MUTED).pack(side=tk.RIGHT)

        self.bar2_canvas = tk.Canvas(bars_frame, width=160, height=14,
                                     bg=BAR_BG, highlightthickness=0)
        self.bar2_canvas.pack(pady=(4, 0))
        self.bar2_bg = self.bar2_canvas.create_rectangle(0, 0, 160, 14,
                                                          fill=BAR_BG, outline="")
        self.bar2_fill = self.bar2_canvas.create_rectangle(0, 0, 0, 14,
                                                           fill=SECOND_ACCENT, outline="")

        # ========== 5. Status Bar ==========
        status_frame = tk.Frame(self.root, bg=CARD_COLOR, bd=0,
                                highlightbackground=CARD_BORDER, highlightthickness=1)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # 状态指示灯
        self.status_indicator = tk.Canvas(status_frame, width=10, height=10,
                                          bg="#555555", highlightthickness=0,
                                          bd=0)
        self.status_indicator.pack(side=tk.LEFT, padx=(12, 6), pady=8)

        self.status_label = tk.Label(status_frame, text="System Offline",
                                     font=("Segoe UI", 9), bg=CARD_COLOR, fg=TEXT_MUTED)
        self.status_label.pack(side=tk.LEFT, pady=8)

    def init_serial(self):
        try:
            self.ser = serial.Serial(self.port, BAUD_RATE, timeout=1)
            time.sleep(1)
            self.status_label.config(text=f"Connected to Pico on {self.port}", fg=SUCCESS_COLOR)
            self.status_indicator.config(bg=SUCCESS_COLOR)
        except Exception:
            self.status_label.config(text="Serial Connection Failed", fg=SECOND_ACCENT)
            self.status_indicator.config(bg=SECOND_ACCENT)

    def paint(self, event):
        r = 12
        x1, y1 = event.x - r, event.y - r
        x2, y2 = event.x + r, event.y + r
        self.canvas.create_oval(x1, y1, x2, y2, fill="white", outline="white")
        self.draw.ellipse([x1, y1, x2, y2], fill=255)

    def clear_canvas(self):
        self.canvas.delete("all")
        self.image = Image.new("L", (CANVAS_SIZE, CANVAS_SIZE), 0)
        self.draw = ImageDraw.Draw(self.image)
        self.digit_label.config(text="-")
        self.update_bars(0, 0, 0, 0)
        self.status_label.config(text="Canvas Cleared", fg=TEXT_MUTED)

    def update_bars(self, digit1, conf1, digit2, conf2):
        # Update text with digit numbers
        self.bar1_label.config(text=f"[{digit1}]  {conf1:.1f}%")
        self.bar2_label.config(text=f"[{digit2}]  {conf2:.1f}%")
        # Update visuals (width=160)
        w1 = int(160 * conf1 / 100)
        w2 = int(160 * conf2 / 100)
        self.bar1_canvas.coords(self.bar1_fill, 0, 0, w1, 14)
        self.bar2_canvas.coords(self.bar2_fill, 0, 0, w2, 14)

    def build_features(self):
        bbox = self.image.getbbox()
        if not bbox: return None
        # 居中剪裁缩放逻辑（同前，保持鲁棒性）
        left, top, right, bottom = bbox
        pad = 30
        crop = self.image.crop((max(0, left-pad), max(0, top-pad), min(280, right+pad), min(280, bottom+pad)))
        resized = crop.resize((20, 20), Image.Resampling.LANCZOS)
        canvas = Image.new("L", (OUTPUT_SIZE, OUTPUT_SIZE), 0)
        canvas.paste(resized, (4, 4))
        return [round(x/255.0, 3) for x in np.asarray(canvas).ravel()]

    def send_data(self):
        if not self.ser: return
        with self._lock:
            if self._busy: return
            self._busy = True

        features = self.build_features()
        if features is None:
            self._busy = False
            return

        self.rec_btn.config(state=tk.DISABLED, text="⏳ INFERRING...")
        self.status_label.config(text="Transmitting Data...", fg=ACCENT_COLOR)
        self.status_indicator.config(bg=WARNING_COLOR)

        try:
            self.ser.write((json.dumps(features) + "\n").encode())
            threading.Thread(target=self.receive_result, daemon=True).start()
        except Exception as e:
            self.status_label.config(text=f"Error: {e}", fg=SECOND_ACCENT)
            self.status_indicator.config(bg=SECOND_ACCENT)
            self._busy = False
            self.rec_btn.config(state=tk.NORMAL, text="▶ RECOGNIZE")

    def receive_result(self):
        start_time = time.time()
        try:
            while time.time() - start_time < 3:
                line = self.ser.readline().decode().strip()
                if line.startswith("{"):
                    data = json.loads(line)
                    if "digit1" in data:
                        self.root.after(0, self.show_result, data)
                        return
            self.root.after(0, lambda: self.status_label.config(text="Timeout", fg=SECOND_ACCENT))
            self.root.after(0, lambda: self.status_indicator.config(bg=SECOND_ACCENT))
        finally:
            self.root.after(0, self.reset_btn)

    def show_result(self, data):
        self.digit_label.config(text=str(data["digit1"]))
        self.update_bars(data["digit1"], data["conf1"], data["digit2"], data["conf2"])
        self.status_label.config(text="Inference Complete", fg=SUCCESS_COLOR)
        self.status_indicator.config(bg=SUCCESS_COLOR)

    def reset_btn(self):
        self.rec_btn.config(state=tk.NORMAL, text="▶ RECOGNIZE")
        with self._lock: self._busy = False

if __name__ == "__main__":
    port = select_port()
    if port is None:
        exit(0)
    root = tk.Tk()
    app = MnistDigitApp(root, port)
    root.mainloop()
