import os
import tkinter as tk
from datetime import timedelta
from tkinter import filedialog, messagebox, ttk, PhotoImage, Label
from tkinter.constants import DISABLED
import cv2
import vlc
from PIL import Image, ImageTk
import subprocess

ffprobe_path = os.path.join(os.getcwd(), 'ffprobe.exe')

class VideoPlayerApp:
    def __init__(self, root):
        # 主窗口
        self.root = root
        self.root.title("视频播放器")
        self.root.geometry("1280x720")
        self.root.grid_rowconfigure(1, weight=1) #大小自适应
        self.root.grid_columnconfigure(0, weight=1)

        # 组件ICON
        new_size1 = (34, 34)
        self.photo_play = ImageTk.PhotoImage(Image.open("icon/play.png").resize(new_size1))
        self.photo_pause = ImageTk.PhotoImage(Image.open("icon/pause.png").resize(new_size1))
        self.photo_voice = ImageTk.PhotoImage(Image.open("icon/voice.png").resize(new_size1))
        self.photo_no_voice = ImageTk.PhotoImage(Image.open("icon/no_voice.png").resize(new_size1))
        self.photo_stop = ImageTk.PhotoImage(Image.open("icon/stop.png").resize(new_size1))
        self.photo_file_add = ImageTk.PhotoImage(Image.open("icon/file_add.png").resize(new_size1))
        self.photo_snapshot = ImageTk.PhotoImage(Image.open("icon/snapshot.png").resize(new_size1))
        self.photo_full = ImageTk.PhotoImage(Image.open("icon/full.png").resize(new_size1))
        self.photo_play_cycle = ImageTk.PhotoImage(Image.open("icon/play_cycle.png").resize(new_size1))
        self.photo_one_cycle = ImageTk.PhotoImage(Image.open("icon/play_one_cycle.png").resize(new_size1))
        self.photo_play_sequel = ImageTk.PhotoImage(Image.open("icon/play_sequel.png").resize(new_size1))
        self.photo_play_stop = ImageTk.PhotoImage(Image.open("icon/play_stop.png").resize(new_size1))

        # 背景图片
        self.pil_image = Image.open("background.png")
        self.background_image = ImageTk.PhotoImage(self.pil_image)
        self.canvas = tk.Canvas(self.root) #创建Canvas用于放置背景图片
        self.canvas.grid(row=0, column=0, rowspan=4, columnspan=3, sticky='nsew')  #确保canvas填充整个窗口
        self.background = self.canvas.create_image(0, 0, anchor='nw', image=self.background_image) #设置背景图片
        self.canvas.bind('<Configure>', self.resize_image) #背景自适应

        #组件
        self.open_button = ttk.Button(root, image=self.photo_file_add, command=self.load_videos) #创建选择文件按钮
        self.open_button.image = self.photo_file_add
        self.panel = tk.Frame(self.root, bg="black") #创建用于嵌入VLC播放器的容器，并将其放置在中间
        self.panel.grid_rowconfigure(0, weight=1)
        self.panel.grid_columnconfigure(0, weight=1)
        self.instance = vlc.Instance() #VLC实例和媒体播放器
        self.player = self.instance.media_player_new()
        self.player.video_set_mouse_input(False) #禁用 VLC 的鼠标输入处理
        self.player.video_set_key_input(False)

        # 创建播放/暂停按钮，初始状态为禁用
        self.play_pause_button = ttk.Button(root, image=self.photo_play, command=self.toggle_play_pause, state=DISABLED)
        # 创建停止按钮，初始状态为禁用
        self.stop_button = ttk.Button(root, image=self.photo_stop, command=self.stop_video, state=DISABLED)
        # 创建截图按钮，初始状态为禁用
        self.snapshot_button = ttk.Button(root, image=self.photo_snapshot, command=self.capture_frame, state=DISABLED)
        # 创建全屏按钮
        self.full_button = ttk.Button(root, image=self.photo_full,command=self.toggle_fullscreen)
        # 创建模式切换按钮
        self.modes_button = ttk.Button(root, image=self.photo_play_sequel, command=self.play_modes_switch)
        # 创建音量标签和音量控制滑块并放置在右下角
        self.volume_button = ttk.Button(root, image=self.photo_voice, command=self.switch_volume)
        self.volume_slider = tk.Scale(root, from_=0, to=100, orient="horizontal", length=87,command=self.set_volume)
        # 默认音量设为50%
        self.volume_slider.set(50)
        # 创建进度条并放置在底部
        self.progress_bar = ttk.Progressbar(root, orient="horizontal", mode="determinate")
        # 创建时间显示标签并放置在下方正中间
        self.time_label = tk.Label(root, text="0:00:00/0:00:00")
        # 创建视频名字标签并放置在上方正中间
        self.name_label = tk.Label(root, text="视频播放器")

        # 创建播放列表
        self.playlist_frame = tk.Frame(self.root)
        self.playlist_label = tk.Label(self.playlist_frame, text="播放列表")
        self.playlist_label.pack(side=tk.TOP, anchor='n')
        self.playlist_box = tk.Listbox(self.playlist_frame, selectmode=tk.SINGLE)
        self.playlist_box.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.playlist_box.bind("<<ListboxSelect>>", self.on_playlist_select)  # 绑定播放列表点击事件
        self.playlist_box.bind("<Double-Button-1>", self.show_popup_menu_del)

        self.rat = 1.0  # 当前播放速率
        # 创建播放速率按钮
        self.rates_button = tk.Button(root, text=self.rat, command=self.toggle_play_pause)
        self.rate_menu = tk.Menu(self.root, tearoff=0)
        self.rate_menu.add_command(label="0.5", command=lambda: self.set_playback_rate(0.5))
        self.rate_menu.add_command(label="1.0", command=lambda: self.set_playback_rate(1.0))
        self.rate_menu.add_command(label="1.5", command=lambda: self.set_playback_rate(1.5))
        self.rate_menu.add_command(label="2.0", command=lambda: self.set_playback_rate(2.0))
        self.rate_menu.add_command(label="3.0", command=lambda: self.set_playback_rate(3.0))
        self.rates_button.bind("<Button-1>", self.show_rate_menu)

        # 右键菜单
        self.popup_menu1 = tk.Menu(self.root, tearoff=0)
        self.popup_menu2 = tk.Menu(self.popup_menu1, tearoff=0)
        self.popup_menu3 = tk.Menu(self.popup_menu1, tearoff=0)
        self.popup_menu4 = tk.Menu(self.popup_menu1, tearoff=0)
        self.popup_menu5 = tk.Menu(self.popup_menu1, tearoff=0)
        self.popup_menu2.add_command(label="0.5", command=lambda: self.set_playback_rate(0.5))
        self.popup_menu2.add_command(label="1.0", command=lambda: self.set_playback_rate(1.0))
        self.popup_menu2.add_command(label="1.5", command=lambda: self.set_playback_rate(1.5))
        self.popup_menu2.add_command(label="2.0", command=lambda: self.set_playback_rate(2.0))
        self.popup_menu2.add_command(label="3.0", command=lambda: self.set_playback_rate(3.0))
        self.popup_menu4.add_command(label="顺序播放", command=lambda: self.play_modes_set(1))
        self.popup_menu4.add_command(label="列表循环", command=lambda: self.play_modes_set(2))
        self.popup_menu4.add_command(label="单集循环", command=lambda: self.play_modes_set(3))
        self.popup_menu4.add_command(label="播完停止", command=lambda: self.play_modes_set(4))
        self.popup_menu1.add_command(label="选择文件", command=self.load_videos, state=tk.NORMAL)
        self.popup_menu1.add_cascade(label="播放列表", menu=self.popup_menu3, state=tk.DISABLED)
        self.popup_menu1.add_cascade(label="播放速率", menu=self.popup_menu2)
        self.popup_menu1.add_cascade(label="播放模式", menu=self.popup_menu4)
        self.popup_menu5.add_command(label="全屏/窗口", command=self.toggle_fullscreen, state=tk.NORMAL)
        self.popup_menu5.add_command(label="切换组件", command=self.toggle_to_switch)
        self.popup_menu1.add_command(label="播放/暂停", command=self.toggle_play_pause, state=tk.DISABLED)
        self.popup_menu5.add_command(label="截图", command=self.capture_frame, state=tk.DISABLED)
        self.popup_menu5.add_command(label="背景", command=self.switch_background)
        self.popup_menu1.add_cascade(label="其他", menu=self.popup_menu5)
        self.popup_menu1.add_command(label="停止", command=self.stop_video, state=tk.DISABLED)
        self.popup_menu1.add_command(label="退出", command=self.exit_app)
        self.popup_menu_del = tk.Menu(self.playlist_box, tearoff=0)
        self.popup_menu_del.add_command(label="播放", command=self.play_selected_video)
        self.popup_menu_del.add_command(label="删除", command=self.delete_selected_video)
        # 绑定点击事件
        self.root.bind("<Button-3>", self.show_popup_menu1)
        self.panel.bind("<Double-Button-1>", self.double_event)

        # 播放状态初始化
        self.play_path = None  #视频路径
        self.is_playing = False #是否播放
        self.is_stopping = True #是否停止
        self.not_fullscreen = True  # 窗口状态
        self.forget = 1  # 组件显示模式
        self.rates = [0.5, 1.0, 1.5, 2.0, 3.0]  # 播放速率
        self.set_playback_rate(1.0)
        self.time_num = 0  # 防止多重调用update_time_display()
        self.total_duration_ms = None #总时长（毫秒）
        self.total_duration = None #总时长（时:分:秒）
        self.after_id_1 = None  # 预览延迟
        self.preview_window = None #预览窗
        self.frames = []
        self.play_mode = 1 #播放模式
        self.play_modes_set(1)
        self.playlist = [] #播放列表
        self.current_index = -1 #当前视频编号
        self.selected_indices = None
        self.volume_level = 50 #音量大小
        self.reset_volume = self.volume_level  #音量记忆
        self.bg = True #背景显示
        self.show_for_items() #组件显示

    def get_duration(self):
        """文件时长获取"""
        result = subprocess.run(
            [ffprobe_path, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
             self.play_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        return float(result.stdout)*1000

    def get_unique_filename(self):
        """生成唯一文件名"""
        base_name = os.path.splitext(os.path.basename(self.play_path))
        directory = os.path.dirname(self.play_path)
        n = 1
        new_filename = self.play_path
        while os.path.isfile(new_filename):
            new_filename = os.path.join(directory, f"{base_name[0]}({n}).jpg")
            n += 1
        return new_filename

    def update_total_time(self):
        """获取视频时长"""
        if self.player.get_media():
            self.total_duration_ms = self.get_duration() #获取时长
            self.total_duration = str(timedelta(milliseconds=self.total_duration_ms)).split('.')[0] #转换为(时:分:秒)

    def capture_frame(self):
        """保存视频截图"""
        if not self.is_stopping:
            result = self.player.video_take_snapshot(0, self.get_unique_filename(), 0, 0)
            if not result == 0:
                messagebox.showinfo("截图","截图失败")

    def switch_background(self):
        """背景图片切换"""
        if self.bg:
            self.canvas.grid_remove()
        else:
            self.canvas.grid()
        self.bg = not self.bg

    def exit_app(self):
        """右键菜单退出"""
        if messagebox.askokcancel("退出", "你确定要退出吗？"):
            # 释放 VLC 资源
            if self.player.is_playing():
                self.stop_video()
            self.player.release()
            self.instance.release()
            # 关闭主窗口并终止应用程序
            self.root.destroy()

    def toggle_fullscreen(self):
        """切换全屏模式"""
        self.not_fullscreen = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not self.not_fullscreen)

    def set_playback_rate(self, rate):
        """设置播放速率"""
        self.player.set_rate(rate)
        self.rat = rate
        # 相关按钮的禁用与恢复
        self.popup_menu2.entryconfig(f"{str(rate)}", state=tk.DISABLED)
        self.rate_menu.entryconfig(f"{str(rate)}", state=tk.DISABLED)
        self.rates_button.config(text=self.rat)
        for Rate in self.rates:
            if Rate != rate:
                self.popup_menu2.entryconfig(f"{str(Rate)}", state=tk.NORMAL)
                self.rate_menu.entryconfig(f"{str(Rate)}", state=tk.NORMAL)

    def play_modes_switch(self):
        """播放模式的按键循环"""
        if self.play_mode != 4:
            self.play_mode += 1
        else:
            self.play_mode=1
        self.play_modes_set(0)

    def play_modes_set(self, mode):
        """播放模式选择"""
        modes=["顺序播放","列表循环","单集循环","播完停止"]
        # 按钮的ICON切换与状态
        photos=[self.photo_play_sequel, self.photo_play_cycle, self.photo_one_cycle, self.photo_play_stop]
        if not mode == 0:
            self.play_mode = mode
        self.popup_menu4.entryconfig(modes[self.play_mode-1], state=tk.DISABLED)
        for mod in modes:
            if mod != modes[self.play_mode-1]:
                self.modes_button.config(image=photos[self.play_mode-1])
                self.popup_menu4.entryconfig(f"{mod}", state=tk.NORMAL)

    def play_modes(self):
        """播放模式切换"""
        match self.play_mode:
            # 顺序播放
            case 1:
                self.player.stop()
                self.play_next_video()
            # 列表循环
            case 2:
                if self.current_index == len(self.playlist) - 1:
                    self.player.stop()
                    self.load_and_play_video(self.playlist[0])
                else:
                    self.play_next_video()
            # 单集循环
            case 3:
                self.player.stop()
                self.load_and_play_video(self.play_path)
            # 播完停止
            case 4:
                self.stop_video()
                messagebox.showinfo("信息", "播放完毕")

    def on_mousewheel(self, event):
        """滚轮音量调整"""
        if event.num == 4 or (event.delta and event.delta > 0):  # 向上滚动
            self.set_volume(self.volume_level+1)
        elif event.num == 5 or (event.delta and event.delta < 0):  # 向下滚动
            if not self.volume_level ==0:
                self.set_volume(self.volume_level-1)

    def update_volume_icon(self):
        """音量图标切换"""
        self.volume_button.config(image=self.photo_no_voice) if self.volume_level == 0 else self.volume_button.config(image=self.photo_voice)

    def switch_volume(self):
        """一键静音与恢复"""
        self.set_volume(0) if self.volume_level != 0 else self.set_volume(self.reset_volume)

    def set_volume(self, volume):
        """音量大小调整"""
        if self.volume_level !=0 :
            self.reset_volume = self.volume_level
        self.volume_level = int(float(volume))
        self.player.audio_set_volume(self.volume_level)
        self.volume_slider.set(self.volume_level)
        self.update_volume_icon()

    def show_popup_menu1(self, event):
        """显示右键菜单"""
        try:
            self.popup_menu1.tk_popup(event.x_root, event.y_root)
        finally:
            # 确保释放tk_popup的抓取
            self.popup_menu1.grab_release()

    def show_popup_menu_del(self, event):
        """显示双击菜单"""
        try:
            if self.selected_indices:
                self.popup_menu_del.tk_popup(event.x_root, event.y_root)
        finally:
            # 确保释放tk_popup的抓取
            self.popup_menu_del.grab_release()

    def show_rate_menu(self, event):
        """显示播放速率菜单"""
        try:
            self.rate_menu.tk_popup(event.x_root, event.y_root)
        finally:
            # 确保释放tk_popup的抓取
            self.rate_menu.grab_release()

    def resize_image(self, event=None):
        """背景大小自适应"""
        resized_image = self.pil_image.resize((event.width, event.height))
        img = ImageTk.PhotoImage(resized_image)
        self.canvas.itemconfig(self.background, image=img)
        self.canvas.image = img  # 更新引用以防止垃圾回收

    def load_videos(self):
        """选择视频加载"""
        video_paths = filedialog.askopenfilenames(
            filetypes=[
                ("V/A files", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.mpg *.mpeg *.wav *.mp3 *.flac *.aac *.wma *.m4a")
            ]
        )
        if not video_paths:
            return
        # 确保播放列表中没有重复的视频
        for video_path in video_paths:
            if video_path not in self.playlist:
                self.playlist.append(video_path)
                self.playlist_box.insert(tk.END, os.path.basename(video_path))
                self.popup_menu3.add_command(label=f"{os.path.basename(video_path)}",
                                             command=lambda: self.load_and_play_video(video_path))

        self.load_and_play_video(video_paths[0]) #加载选择到的第一个视频
        self.popup_menu1.entryconfig("播放列表", state=tk.NORMAL)

    def play_next_video(self):
        """播放下一视频"""
        if self.current_index < len(self.playlist) - 1:
            self.load_and_play_video(self.playlist[self.current_index + 1])
        else:
            self.stop_video()
            messagebox.showinfo("信息", "播放完毕")

    def stop_video(self):
        """视频停止播放"""
        if self.player.get_media():
            self.unbind_progress_bar_events()
            self.player.stop()
            self.is_stopping = True
            self.is_playing = False
            self.current_index = -1
            self.update_item()
            self.update_time_display(self.time_num)
            self.update_name_display()
            self.time_num=0

    def load_and_play_video(self, video_path):
        """播放加载视频"""
        media = self.instance.media_new(video_path)
        self.player.set_media(media)
        if hasattr(self.player, 'set_hwnd'):
            self.player.set_hwnd(self.panel.winfo_id())
        elif hasattr(self.player, 'set_xwindow'):
            self.player.set_xwindow(self.panel.winfo_id())
        else:
            self.player.set_nsobject(int(self.panel.winfo_id()))
        self.is_playing = True
        self.is_stopping = False
        self.play_path=video_path
        self.capture_frames()
        self.get_current_index()
        self.bind_progress_bar_events() #绑定进度条事件
        self.update_total_time()
        self.time_num += 1
        self.update_time_display(self.time_num)
        self.update_name_display()
        self.update_item()
        self.panel.bind("<MouseWheel>", self.on_mousewheel)
        self.player.play()

    def get_current_index(self):
        self.current_index = self.playlist.index(f"{self.play_path}")

    def double_event(self, event):
        """鼠标双击事件"""
        self.toggle_fullscreen()

    def toggle_play_pause(self):
        """暂停播放切换"""
        if self.is_playing:
            self.player.pause()
        else:
            self.player.play()
        self.is_playing = not self.is_playing
        self.update_item()

    def remove_for_background(self):
        """欣赏背景图片"""
        widgets = [self.name_label, self.volume_slider, self.volume_button, self.stop_button, self.play_pause_button
            , self.snapshot_button, self.full_button, self.modes_button, self.open_button, self.playlist_frame
            , self.progress_bar, self.panel, self.time_label, self.rates_button]
        for widget in widgets:
            widget.grid_remove()

    def toggle_to_switch(self):
        """组件显示切换"""
        widgets = [self.name_label, self.volume_slider, self.volume_button, self.stop_button, self.play_pause_button
            , self.snapshot_button, self.full_button, self.modes_button, self.open_button, self.playlist_frame, self.rates_button]
        if self.forget ==1:
            for widget in widgets:
                widget.grid_remove()
                self.panel.grid(padx=0)
            self.forget += 1
        elif self.forget ==2:
            self.remove_for_background()
            self.forget += 1
        else:
            for widget in widgets:
                widget.grid()
                self.panel.grid(padx=2)
                self.progress_bar.grid()
                self.time_label.grid()
            self.forget = 1

    def show_for_items(self):
        """组件显示"""
        self.open_button.grid(row=0, column=0, pady=10, padx=10, sticky='w')
        self.playlist_frame.grid(row=0, rowspan=4, column=3, padx=10, pady=10, sticky='ns')
        self.play_pause_button.grid(row=3, column=0, pady=(0,12), padx=10, sticky='w')
        self.stop_button.grid(row=3, column=0, pady=(0,12), padx=(64, 0), sticky='w')
        self.modes_button.grid(row=3, column=0, pady=(0, 12), padx=(117, 0), sticky='w')
        self.snapshot_button.grid(row=0, column=1, pady=10, padx=(0,64), sticky='e')
        self.full_button.grid(row=0, column=1, pady=10, padx=10, sticky='e')
        self.volume_button.grid(row=3, column=0, pady=(0,12), padx=(0,0), sticky='e')
        self.rates_button.grid(row=3, column=0, pady=(0,12), padx=(0,55), sticky='e',ipadx=7, ipady=7)
        self.volume_slider.grid(row=3, column=1, pady=(0,12), padx=(0,10), sticky='e')
        self.name_label.grid(row=0, column=0, pady=10, padx=(100, 0))
        self.panel.grid(row=1, column=0, columnspan=2, pady=0, padx=2, sticky='nsew')
        self.progress_bar.grid(row=2, column=0, columnspan=1, pady=10, padx=(10,0), sticky='ew')
        self.time_label.grid(row=2, column=1, pady=10, padx=10)

    def update_time_display(self, num):
        """时间显示更新"""
        if self.player.get_media():
            current_time_ms = self.player.get_time() + 1000
            if current_time_ms >= 0 and self.total_duration_ms > 0 and num == self.time_num:
                current_time = str(timedelta(milliseconds=current_time_ms)).split('.')[0]
                self.time_label.config(text=f"{current_time}/{self.total_duration}")
                self.progress_bar['value'] = (current_time_ms / self.total_duration_ms) * 100
                if current_time_ms >= self.total_duration_ms:
                    self.play_modes()
                else:
                    self.root.after(int(1000.0/self.rat), lambda: self.update_time_display(num)) # 每秒更新一次时间显示
        if self.is_stopping:
            self.time_label.config(text="0:00:00/0:00:00")
            self.progress_bar['value'] = 0

    def update_name_display(self):
        """视频标题获取"""
        if self.player.get_media() and not self.is_stopping:
            self.name_label.config(text=os.path.basename(self.play_path))
        else:
            self.name_label.config(text="视频播放器")

    def on_playlist_select(self, event):
        """播放列表选择"""
        self.selected_indices = self.playlist_box.curselection()

    def play_selected_video(self):
        """播放选中视频"""
        index = self.selected_indices[0]
        self.current_index = index
        self.load_and_play_video(self.playlist[index])

    def delete_selected_video(self, *args):
        """删除选中的视频"""
        index = self.selected_indices[0]
        confirm = messagebox.askyesno("删除", f"确定要删除'{os.path.basename(self.playlist[index])}'吗?")
        if confirm:
            self.popup_menu3.delete(index)
            if self.current_index == index:
                self.stop_video()
                self.playlist_box.delete(index)
                del self.playlist[index]
            else:
                self.playlist_box.delete(index)
                del self.playlist[index]
                self.get_current_index()
            if not self.playlist:
                self.popup_menu1.entryconfig("播放列表", state=tk.DISABLED)
            self.selected_indices = None

    def bind_progress_bar_events(self):
        """绑定进度条事件"""
        self.progress_bar.bind("<Button-1>", self.update_progress_bar_position)
        self.progress_bar.bind("<B1-Motion>", self.update_progress_bar_position)
        self.progress_bar.bind("<ButtonRelease-1>", self.update_progress_bar_position)
        self.progress_bar.bind("<Motion>", self.show_preview)
        self.progress_bar.bind("<Leave>", self.on_leave)

    def unbind_progress_bar_events(self):
        """解绑进度条事件"""
        self.hide_preview()
        self.progress_bar.unbind("<Button-1>")
        self.progress_bar.unbind("<B1-Motion>")
        self.progress_bar.unbind("<ButtonRelease-1>")
        self.progress_bar.unbind("<Motion>")
        self.progress_bar.unbind("<Leave>")

    def on_leave(self, event):
        """预览窗隐藏"""
        if self.after_id_1:
            self.root.after_cancel(self.after_id_1)  # 取消定时器
            self.after_id_1 = None
        self.hide_preview()

    def update_progress_bar_position(self, event):
        """更新进度条"""
        x = event.x
        total_width = self.progress_bar.winfo_width()
        if x <= 0:
            x = 0
        elif x >= total_width-1:
            x = total_width-1
        percentage = x / total_width if total_width > 0 else 0
        self.player.set_position(round(percentage, 3)) #跳转
        current_time_ms = self.player.get_time()
        if current_time_ms >= 0 and self.total_duration_ms > 0:
            current_time = str(timedelta(milliseconds=current_time_ms)).split('.')[0]
            self.time_label.config(text=f"{current_time}/{self.total_duration}")
            self.progress_bar['value'] = (current_time_ms / self.total_duration_ms) * 100
            if current_time_ms >= self.total_duration_ms:
                self.play_modes()
            self.show_preview(event)

    def show_preview(self, event):
        """预览窗显示"""
        if not self.preview_window or not self.preview_window.winfo_exists():
            if self.after_id_1:
                self.root.after_cancel(self.after_id_1)  #取消之前的定时器（如果有）
            self.after_id_1 = self.root.after(500, self.create_preview_window(event)) #设置新的定时器
        x = event.x
        total_width = self.progress_bar.winfo_width()
        if x <= 0:
            x = 0
        elif x >= total_width-1:
            x = total_width -1
        percentage = x / total_width if total_width > 0 else 0
        new_time_ms = int(self.total_duration_ms * percentage)
        preview_time = str(timedelta(milliseconds=new_time_ms)).split('.')[0]
        self.preview_label.config(text=f"进度: {percentage*100.0:.2f}%    时间: {preview_time}")
        if self.frames:
            self.preview_image.config(image=self.frames[int(len(self.frames)*percentage-1)])
        # 预览窗的定位
        x = self.root.winfo_pointerx() + 5
        y = self.root.winfo_pointery() - 200
        self.preview_window.geometry(f"+{x}+{y}")

    def hide_preview(self):
        """隐藏预览窗"""
        if self.preview_window and self.preview_window.winfo_exists():
            self.preview_window.destroy()
            self.preview_window = None

    def create_preview_window(self, event):
        """创建预览窗"""
        self.preview_window = tk.Toplevel(self.root)
        self.preview_window.overrideredirect(True)  # 去除窗口边框
        self.preview_window.attributes('-alpha', 0.9)  # 设置透明度
        self.preview_window.geometry("273x180")
        self.preview_label = Label(self.preview_window, bg='white', relief='solid', borderwidth=0)
        self.preview_label.pack(padx=2, pady=2)
        if self.frames:
            self.preview_image = Label(self.preview_window, bg='white', relief='solid', borderwidth=0)
            self.preview_image.pack(fill=tk.BOTH, expand=1)

    def capture_frames(self, interval=24):
        """读取预览画面"""
        self.frames = []
        video_cap = cv2.VideoCapture(self.play_path)
        total_frames = int(video_cap.get(cv2.CAP_PROP_FRAME_COUNT))  # 总帧
        if not video_cap.isOpened() or total_frames == -1:
            return
        frame_interval = int(total_frames / interval)  # 每隔多少帧读取一次
        for frame_number in range(0, total_frames, frame_interval):
            video_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)  # 跳转相关帧
            ret, frame = video_cap.read()
            if not ret:
                break
            # 将OpenCV的BGR图像转换为PIL的RGB图像，并调整大小后的帧使用
            frame = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            resized_frame = frame.resize((273, 160))
            pil_frame = ImageTk.PhotoImage(image=resized_frame)
            self.frames.append(pil_frame)  # 将帧添加到列表中
        print(len(self.frames))
        video_cap.release()  # 释放VideoCapture对象

    def update_item(self):
        """更新按钮状态"""
        if self.is_playing:
            self.play_pause_button.config(image=self.photo_pause)
        else:
            self.play_pause_button.config(image=self.photo_play)
        if self.is_stopping:
            self.popup_menu1.entryconfig("停止", state=tk.DISABLED)
            self.popup_menu1.entryconfig("播放/暂停", state=tk.DISABLED)
            self.popup_menu5.entryconfig("截图", state=tk.DISABLED)
            self.play_pause_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.DISABLED)
            self.snapshot_button.config(state=tk.DISABLED)
        else:
            self.play_pause_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.NORMAL)
            self.snapshot_button.config(state=tk.NORMAL)
            self.popup_menu1.entryconfig("停止", state=tk.NORMAL)
            self.popup_menu5.entryconfig("截图", state=tk.NORMAL)
            self.popup_menu1.entryconfig("播放/暂停", state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    icon_image = PhotoImage(file='icon/icon2.png') #主窗口的ICON
    root.wm_iconphoto(False,icon_image)
    app = VideoPlayerApp(root)
    root.mainloop()