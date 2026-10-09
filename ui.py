import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
import threading
import webbrowser
import platform
from grab_core import GrabCore


def _font(size, bold=False, underline=False):
    family = 'PingFang SC' if platform.system() == 'Darwin' else '微软雅黑'
    style = []
    if bold:
        style.append('bold')
    if underline:
        style.append('underline')
    return (family, size, ' '.join(style) if style else 'normal')


def _mono_font(size):
    return ('Menlo', size) if platform.system() == 'Darwin' else ('Consolas', size)


class GrabUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('UEM Course Grabbing Tool')
        self.root.geometry('800x780')
        self.root.resizable(False, False)
        self.core = None
        self.stop_flag = False
        self.grab_thread = None
        self.verify_thread = None
        self.main_vars = []
        self.backup_vars = []
        self.course_data = []
        self.main_course_name = None
        self._build_ui()
        self._center_window()

    def _center_window(self):
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f'+{x}+{y}')

    def _build_ui(self):
        tk.Label(
            self.root, text='应急管理大学教务管理系统抢课工具',
            font=_font(16, bold=True)
        ).pack(pady=(10, 6))

        info_frame = ttk.LabelFrame(self.root, text='选课信息', padding=10)
        info_frame.pack(fill='x', padx=12, pady=4)

        ttk.Label(info_frame, text='Cookie:').grid(
            row=0, column=0, sticky='nw', pady=2
        )
        cookie_inner = ttk.Frame(info_frame)
        cookie_inner.grid(row=0, column=1, sticky='we', pady=2)
        self.cookie_text = tk.Text(
            cookie_inner, height=3, width=60, wrap='none',
            font=_mono_font(8), relief='sunken', borderwidth=1
        )
        cookie_scroll = ttk.Scrollbar(
            cookie_inner, orient='horizontal',
            command=self.cookie_text.xview
        )
        self.cookie_text.configure(xscrollcommand=cookie_scroll.set)
        self.cookie_text.pack(side='left', fill='x', expand=True)
        cookie_scroll.pack(side='left', fill='y')

        self.verify_btn = ttk.Button(
            info_frame, text='验证', command=self.verify_cookie
        )
        self.verify_btn.grid(row=0, column=2, sticky='nw', padx=(6, 0), pady=2)
        self.verify_var = tk.StringVar(value='')
        ttk.Label(info_frame, textvariable=self.verify_var,
                  font=_font(9)).grid(row=0, column=3, sticky='nw', padx=(6, 0), pady=2)

        ttk.Label(info_frame, text='我的班级:').grid(
            row=1, column=0, sticky='w', pady=2
        )
        self.class_entry = ttk.Entry(info_frame, width=20)
        self.class_entry.grid(row=1, column=1, sticky='w', pady=2)
        self.class_entry.bind('<KeyRelease>', lambda e: self._refresh_course_list())

        course_frame = ttk.LabelFrame(self.root, text='课程列表（点「主」设主选，只能选同一课程不同班；点「备」设备选，随便选）', padding=10)
        course_frame.pack(fill='both', expand=False, padx=12, pady=4)

        self.fetch_status_var = tk.StringVar(value='请先填写班级')
        ttk.Label(course_frame, textvariable=self.fetch_status_var,
                  font=_font(9)).pack(anchor='w', pady=(0, 4))

        list_inner = ttk.Frame(course_frame)
        list_inner.pack(fill='both', expand=True)

        self.course_tree = ttk.Treeview(
            list_inner,
            columns=('main', 'backup', 'sn', 'assign', 'remain', 'capacity'),
            show='tree headings',
            height=7
        )
        self.course_tree.heading('#0', text='课程名')
        self.course_tree.heading('main', text='主')
        self.course_tree.heading('backup', text='备')
        self.course_tree.heading('sn', text='班号')
        self.course_tree.heading('assign', text='教师/时间')
        self.course_tree.heading('remain', text='余量')
        self.course_tree.heading('capacity', text='容量')
        self.course_tree.column('#0', width=140, anchor='w')
        self.course_tree.column('main', width=40, anchor='center')
        self.course_tree.column('backup', width=40, anchor='center')
        self.course_tree.column('sn', width=50, anchor='center')
        self.course_tree.column('assign', width=180, anchor='w')
        self.course_tree.column('remain', width=50, anchor='center')
        self.course_tree.column('capacity', width=50, anchor='center')
        self.course_tree.tag_configure('main_sel', background='#d4edda')
        self.course_tree.tag_configure('backup_sel', background='#fff3cd')
        self.course_tree.pack(side='left', fill='both', expand=True)
        course_scroll = ttk.Scrollbar(
            list_inner, orient='vertical',
            command=self.course_tree.yview
        )
        self.course_tree.configure(yscrollcommand=course_scroll.set)
        course_scroll.pack(side='right', fill='y')
        self.course_tree.bind('<Button-1>', self._on_tree_click)

        time_frame = ttk.LabelFrame(self.root, text='时间设置', padding=10)
        time_frame.pack(fill='x', padx=12, pady=4)

        ttk.Label(time_frame, text='开放时间:').grid(
            row=0, column=0, sticky='w', pady=2
        )
        sb_frame = ttk.Frame(time_frame)
        sb_frame.grid(row=0, column=1, sticky='w', pady=2)

        self.year_sb = ttk.Spinbox(sb_frame, from_=2024, to=2035, width=5, justify='center', state='readonly')
        self.year_sb.set('2026')
        self.year_sb.pack(side='left')
        ttk.Label(sb_frame, text='-').pack(side='left')

        self.month_sb = ttk.Spinbox(sb_frame, from_=1, to=12, width=3, justify='center', state='readonly')
        self.month_sb.set('10')
        self.month_sb.pack(side='left')
        ttk.Label(sb_frame, text='-').pack(side='left')

        self.day_sb = ttk.Spinbox(sb_frame, from_=1, to=31, width=3, justify='center', state='readonly')
        self.day_sb.set('9')
        self.day_sb.pack(side='left')
        ttk.Label(sb_frame, text=' ').pack(side='left')

        self.hour_sb = ttk.Spinbox(sb_frame, from_=0, to=23, width=3, justify='center', state='readonly')
        self.hour_sb.set('16')
        self.hour_sb.pack(side='left')
        ttk.Label(sb_frame, text=':').pack(side='left')

        self.min_sb = ttk.Spinbox(sb_frame, from_=0, to=59, width=3, justify='center', state='readonly')
        self.min_sb.set('00')
        self.min_sb.pack(side='left')
        ttk.Label(sb_frame, text=':').pack(side='left')

        self.sec_sb = ttk.Spinbox(sb_frame, from_=0, to=59, width=3, justify='center', state='readonly')
        self.sec_sb.set('00')
        self.sec_sb.pack(side='left')

        ttk.Label(time_frame, text='提前量(秒):').grid(
            row=0, column=2, sticky='e', pady=2, padx=(20, 0)
        )
        self.advance_entry = ttk.Entry(time_frame, width=8)
        self.advance_entry.insert(0, '10')
        self.advance_entry.grid(row=0, column=3, sticky='w', pady=2)

        ctrl_frame = ttk.Frame(self.root)
        ctrl_frame.pack(fill='x', padx=12, pady=6)

        self.start_btn = ttk.Button(ctrl_frame, text='开始抢课', command=self.start_grab)
        self.start_btn.pack(side='left', padx=(0, 10))
        self.stop_btn = ttk.Button(ctrl_frame, text='停止', command=self.stop_grab, state='disabled')
        self.stop_btn.pack(side='left', padx=10)

        self.status_var = tk.StringVar(value='待机')
        ttk.Label(ctrl_frame, textvariable=self.status_var,
                  font=_font(10, bold=True)).pack(side='right')

        log_header = ttk.Frame(self.root)
        log_header.pack(fill='x', padx=12)
        ttk.Label(log_header, text='日志', font=_font(9, bold=True)).pack(side='left')
        ttk.Button(log_header, text='清空', command=self.clear_log).pack(side='right')

        self.log_text = scrolledtext.ScrolledText(
            self.root, width=95, height=12, font=_mono_font(9),
            state='disabled'
        )
        self.log_text.pack(fill='both', expand=True, padx=12, pady=(2, 4))

        self.log_text.tag_config('success', foreground='#27AE60')
        self.log_text.tag_config('error', foreground='#E74C3C')
        self.log_text.tag_config('warning', foreground='#E67E22')
        self.log_text.tag_config('info', foreground='#2980B9')

        watermark_frame = tk.Frame(self.root)
        watermark_frame.pack(side='right', padx=12, pady=(0, 4))
        tk.Label(watermark_frame, text='made by ',
                 font=_font(8), fg='gray').pack(side='left')
        link_label = tk.Label(watermark_frame, text='112114141',
                 font=_font(8, underline=True), fg='blue',
                 cursor='hand2')
        link_label.pack(side='left')
        link_label.bind('<Button-1>',
            lambda e: webbrowser.open('https://github.com/112114141'))
        tk.Label(watermark_frame, text='[左晟宇] with ❤️',
                 font=_font(8), fg='gray').pack(side='left')

    def _refresh_course_list(self):
        class_name = self.class_entry.get().strip()
        if not class_name:
            self.course_data = []
            self.main_vars = []
            self.backup_vars = []
            self.main_course_name = None
            self.course_tree.delete(*self.course_tree.get_children())
            self.fetch_status_var.set('请先填写班级')
            return

        courses = GrabCore.get_builtin_courses(class_name)
        self.course_data = courses
        self.main_vars = [False] * len(courses)
        self.backup_vars = [False] * len(courses)
        self.main_course_name = None
        self.course_tree.delete(*self.course_tree.get_children())

        for i, c in enumerate(self.course_data):
            self.course_tree.insert(
                '', 'end',
                text=c['name'],
                values=('☐', '☐', c['sn'], c['assign'], '?', c['capacity']),
                iid=str(i)
            )

        self.fetch_status_var.set(
            f'共 {len(courses)} 个教学班（点「主」选主选，点「备」选备选）'
        )

    def _on_tree_click(self, event):
        region = self.course_tree.identify('region', event.x, event.y)
        if region not in ('tree', 'cell'):
            return
        item = self.course_tree.identify_row(event.y)
        if not item:
            return
        col = self.course_tree.identify_column(event.x)
        if col not in ('#1', '#2'):
            return
        idx = self.course_tree.index(item)
        if idx >= len(self.course_data):
            return

        vals = list(self.course_tree.item(item, 'values'))

        if col == '#1':
            if self.main_vars[idx]:
                self.main_vars[idx] = False
                vals[0] = '☐'
                if not any(self.main_vars):
                    self.main_course_name = None
                self.course_tree.item(item, values=vals, tags=())
            else:
                cname = self.course_data[idx]['name']
                if self.main_course_name and cname != self.main_course_name:
                    messagebox.showwarning('提示',
                        f'主选只能选同一课程的不同班号\n当前主选: {self.main_course_name}\n该课程: {cname}')
                    return
                if self.backup_vars[idx]:
                    self.backup_vars[idx] = False
                    vals[1] = '☐'
                self.main_vars[idx] = True
                self.main_course_name = cname
                vals[0] = '☑'
                self.course_tree.item(item, values=vals, tags=('main_sel',))

        elif col == '#2':
            if self.backup_vars[idx]:
                self.backup_vars[idx] = False
                vals[1] = '☐'
                self.course_tree.item(item, values=vals, tags=())
            else:
                if self.main_vars[idx]:
                    self.main_vars[idx] = False
                    vals[0] = '☐'
                    if not any(self.main_vars):
                        self.main_course_name = None
                self.backup_vars[idx] = True
                vals[1] = '☑'
                self.course_tree.item(item, values=vals, tags=('backup_sel',))

    def _get_log_tag(self, msg):
        if '✅' in msg or '成功' in msg:
            return 'success'
        if '✗' in msg or '失败' in msg or '过期' in msg:
            return 'error'
        if '⚠' in msg:
            return 'warning'
        if '✓' in msg or '>>>' in msg:
            return 'info'
        return 'normal'

    def _update_status(self, msg):
        if '倒计时' in msg:
            self.status_var.set('倒计时中')
        elif '开始秒抢' in msg:
            self.status_var.set('秒抢中')
        elif '转入捡漏' in msg:
            self.status_var.set('捡漏中')
        elif '抢课成功' in msg or '捡漏成功' in msg:
            self.status_var.set('已完成 ✅')
        elif '已停止' in msg:
            self.status_var.set('已停止')

    def append_log(self, msg):
        self.log_text.config(state='normal')
        tag = self._get_log_tag(msg)
        self.log_text.insert('end', msg + '\n', tag)
        self.log_text.see('end')
        lines = int(self.log_text.index('end-1c').split('.')[0])
        if lines > 500:
            self.log_text.delete('1.0', f'{lines - 500}.0')
        self.log_text.config(state='disabled')
        self._update_status(msg)

    def log(self, msg):
        self.root.after(0, lambda: self.append_log(msg))

    def clear_log(self):
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', 'end')
        self.log_text.config(state='disabled')

    def verify_cookie(self):
        cookie = self.cookie_text.get('1.0', 'end-1c').strip().replace('\n', '').replace('\r', '')
        if not cookie:
            messagebox.showwarning('提示', '请填写 Cookie')
            return

        self.verify_btn.config(state='disabled')
        self.verify_var.set('验证中...')

        self.verify_thread = threading.Thread(
            target=self._run_verify,
            args=(cookie,),
            daemon=True
        )
        self.verify_thread.start()

    def _run_verify(self, cookie):
        try:
            core = GrabCore(cookie)
            ok = core.check_cookie()
            if ok:
                self.root.after(0, lambda: self._on_verify_done(True, '✓ 有效'))
            else:
                self.root.after(0, lambda: self._on_verify_done(False, '✗ 已过期'))
        except Exception as e:
            self.root.after(0, lambda: self._on_verify_done(False, f'✗ 错误: {e}'))

    def _on_verify_done(self, ok, msg):
        self.verify_btn.config(state='normal')
        self.verify_var.set(msg)

    def start_grab(self):
        cookie = self.cookie_text.get('1.0', 'end-1c').strip().replace('\n', '').replace('\r', '')
        class_name = self.class_entry.get().strip()
        time_str = f'{self.year_sb.get()}-{self.month_sb.get()}-{self.day_sb.get()} {self.hour_sb.get()}:{self.min_sb.get()}:{self.sec_sb.get()}'
        advance_str = self.advance_entry.get().strip()

        if not cookie:
            messagebox.showwarning('提示', '请填写 Cookie')
            return
        if not class_name:
            messagebox.showwarning('提示', '请填写班级')
            return

        try:
            open_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            messagebox.showwarning('提示', '时间格式错误')
            return

        try:
            advance = float(advance_str)
        except ValueError:
            advance = 10.0

        primary = [self.course_data[i] for i in range(len(self.course_data))
                    if i < len(self.main_vars) and self.main_vars[i]]
        backup = [self.course_data[i] for i in range(len(self.course_data))
                   if i < len(self.backup_vars) and self.backup_vars[i]]

        if not primary and not backup:
            messagebox.showwarning('提示', '请至少选一个主选或备选课程')
            return

        self.stop_flag = False
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.status_var.set('初始化中...')
        self.clear_log()

        self.core = GrabCore(cookie, log_func=self.log)
        self.grab_thread = threading.Thread(
            target=self._run_grab,
            args=(open_time, advance, class_name, primary, backup),
            daemon=True
        )
        self.grab_thread.start()

    def _run_grab(self, open_time, advance, class_name, primary, backup):
        try:
            self.core.run(open_time, advance, class_name, primary, backup,
                          lambda: self.stop_flag)
        except Exception as e:
            self.log(f'✗ 程序异常: {e}')
        finally:
            self.root.after(0, self._on_finish)

    def _on_finish(self):
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        if self.status_var.get() not in ('已完成 ✅', '已停止'):
            self.status_var.set('待机')

    def stop_grab(self):
        self.stop_flag = True
        self.log('用户点击停止，正在停止...')

    def run(self):
        self.root.mainloop()