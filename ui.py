import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
import threading
import webbrowser
from grab_core import GrabCore


class GrabUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('UEM Course Grabbing Tool')
        self.root.geometry('640x580')
        self.root.resizable(False, False)
        self.core = None
        self.stop_flag = False
        self.grab_thread = None
        self._build_ui()

    def _build_ui(self):
        tk.Label(
            self.root, text='应急管理大学教务管理系统抢课工具',
            font=('微软雅黑', 16, 'bold')
        ).pack(pady=8)

        input_frame = ttk.Frame(self.root)
        input_frame.pack(fill='x', padx=12, pady=4)

        ttk.Label(input_frame, text='Cookie:').grid(
            row=0, column=0, sticky='w', pady=4
        )
        self.cookie_entry = ttk.Entry(input_frame, width=82)
        self.cookie_entry.grid(
            row=0, column=1, columnspan=3, sticky='we', pady=4
        )

        ttk.Label(input_frame, text='课程名:').grid(
            row=1, column=0, sticky='w', pady=4
        )
        self.course_entry = ttk.Entry(input_frame, width=82)
        self.course_entry.grid(
            row=1, column=1, columnspan=3, sticky='we', pady=4
        )

        ttk.Label(input_frame, text='开放时间:').grid(
            row=2, column=0, sticky='w', pady=4
        )
        time_frame = ttk.Frame(input_frame)
        time_frame.grid(row=2, column=1, sticky='w', pady=4)

        self.year_sb = ttk.Spinbox(time_frame, from_=2026, to=2030, width=5, justify='center', state='readonly')
        self.year_sb.set('2026')
        self.year_sb.pack(side='left')
        ttk.Label(time_frame, text='-').pack(side='left')

        self.month_sb = ttk.Spinbox(time_frame, from_=1, to=12, width=3, justify='center', state='readonly')
        self.month_sb.set('12')
        self.month_sb.pack(side='left')
        ttk.Label(time_frame, text='-').pack(side='left')

        self.day_sb = ttk.Spinbox(time_frame, from_=1, to=31, width=3, justify='center', state='readonly')
        self.day_sb.set('20')
        self.day_sb.pack(side='left')
        ttk.Label(time_frame, text=' ').pack(side='left')

        self.hour_sb = ttk.Spinbox(time_frame, from_=0, to=23, width=3, justify='center', state='readonly')
        self.hour_sb.set('12')
        self.hour_sb.pack(side='left')
        ttk.Label(time_frame, text=':').pack(side='left')

        self.min_sb = ttk.Spinbox(time_frame, from_=0, to=59, width=3, justify='center', state='readonly')
        self.min_sb.set('00')
        self.min_sb.pack(side='left')
        ttk.Label(time_frame, text=':').pack(side='left')

        self.sec_sb = ttk.Spinbox(time_frame, from_=0, to=59, width=3, justify='center', state='readonly')
        self.sec_sb.set('00')
        self.sec_sb.pack(side='left')

        ttk.Label(input_frame, text='提前量(秒):').grid(
            row=2, column=2, sticky='e', pady=4, padx=(20, 0)
        )
        self.advance_entry = ttk.Entry(input_frame, width=8)
        self.advance_entry.insert(0, '3')
        self.advance_entry.grid(row=2, column=3, sticky='w', pady=4)

        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=8)
        self.start_btn = ttk.Button(
            btn_frame, text='开始抢课', command=self.start_grab
        )
        self.start_btn.pack(side='left', padx=20)
        self.stop_btn = ttk.Button(
            btn_frame, text='停止', command=self.stop_grab,
            state='disabled'
        )
        self.stop_btn.pack(side='left', padx=20)

        ttk.Label(self.root, text='日志:', font=('微软雅黑', 9)).pack(
            anchor='w', padx=12
        )
        self.log_text = scrolledtext.ScrolledText(
            self.root, width=85, height=20, font=('Consolas', 9),
            state='disabled'
        )
        self.log_text.pack(fill='both', expand=True, padx=12, pady=4)

        watermark_frame = tk.Frame(self.root)
        watermark_frame.pack(side='right', padx=12)
        tk.Label(watermark_frame, text='made by ',
                 font=('微软雅黑', 8), fg='gray').pack(side='left')
        link_label = tk.Label(watermark_frame, text='112114141',
                 font=('微软雅黑', 8, 'underline'), fg='blue',
                 cursor='hand2')
        link_label.pack(side='left')
        link_label.bind('<Button-1>',
            lambda e: webbrowser.open('https://github.com/112114141'))

    def append_log(self, msg):
        self.log_text.config(state='normal')
        self.log_text.insert('end', msg + '\n')
        self.log_text.see('end')
        self.log_text.config(state='disabled')

    def log(self, msg):
        self.root.after(0, lambda: self.append_log(msg))

    def start_grab(self):
        cookie = self.cookie_entry.get().strip()
        keyword = self.course_entry.get().strip()
        time_str = f'{self.year_sb.get()}-{self.month_sb.get()}-{self.day_sb.get()} {self.hour_sb.get()}:{self.min_sb.get()}:{self.sec_sb.get()}'
        advance_str = self.advance_entry.get().strip()

        if not cookie:
            messagebox.showwarning('提示', '请填写 Cookie')
            return
        if not keyword:
            messagebox.showwarning('提示', '请填写课程名')
            return
        if not time_str:
            messagebox.showwarning('提示', '请填写开放时间')
            return

        try:
            open_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            messagebox.showwarning(
                '提示', '时间格式错误，应为 2026-12-20 12:00:00'
            )
            return

        try:
            advance = float(advance_str)
        except ValueError:
            advance = 3.0

        self.stop_flag = False
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', 'end')
        self.log_text.config(state='disabled')

        self.core = GrabCore(cookie, log_func=self.log)
        self.grab_thread = threading.Thread(
            target=self._run_grab,
            args=(open_time, advance, keyword),
            daemon=True
        )
        self.grab_thread.start()

    def _run_grab(self, open_time, advance, keyword):
        try:
            self.core.run(open_time, advance, keyword,
                          lambda: self.stop_flag)
        except Exception as e:
            self.log(f'✗ 程序异常: {e}')
        finally:
            self.root.after(0, self._on_finish)

    def _on_finish(self):
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')

    def stop_grab(self):
        self.stop_flag = True
        self.log('用户点击停止，正在停止...')

    def run(self):
        self.root.mainloop()