import requests
import time
import random
import re
import json
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from courses_data import BUILTIN_COURSES


class GrabCore:
    def __init__(self, cookie, base_url='https://jw.cidp.edu.cn', log_func=None):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers['Cookie'] = cookie
        self.session.headers['User-Agent'] = (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        )
        self.time_offset = 0.0
        self.select_url = None
        self.query_url = None
        self.target_courses = []
        self.lubn = None
        self.select_type = None
        self.cstask_id = None
        self.page_html = None
        self.select_page_path = None
        self._log = log_func or print

    def log(self, msg):
        ts = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        self._log(f'[{ts}] {msg}')

    def server_now(self):
        return datetime.now() + timedelta(seconds=self.time_offset)

    def calibrate_time(self):
        try:
            resp = self.session.get(self.base_url + '/', timeout=5)
            date_str = resp.headers.get('Date')
            if date_str:
                server_time = parsedate_to_datetime(date_str)
                local_time = datetime.now(timezone.utc)
                self.time_offset = (server_time - local_time).total_seconds()
                return True
        except Exception:
            pass
        return False

    def check_cookie(self):
        try:
            resp = self.session.get(
                self.base_url + '/Navigation/Default.htm?v=5',
                timeout=5, allow_redirects=True
            )
            if 'Login.aspx' in resp.url or resp.status_code in (302, 301):
                return False
            return True
        except Exception:
            return False

    def _start_select(self):
        url = self.base_url + '/Student/CourseSelection/CourseSelectionHandler.ashx?action=startSelect'
        try:
            resp = self.session.post(url, timeout=5)
        except Exception:
            return {'status': 'error', 'message': '请求失败'}
        data = resp.text.strip()
        result = {'status': 'unknown', 'message': data, 'lubn': None, 'type': None}
        if data in ('logintimeout', 'nopermission'):
            result['status'] = 'auth_error'
            result['message'] = 'Cookie过期或无权限'
        elif data == '-20':
            result['status'] = 'paused'
            result['message'] = '选课已暂停'
        elif data == '-1' or data.startswith('-1,'):
            result['status'] = 'not_started'
            result['message'] = '选课尚未开始'
        elif data == '-2':
            result['status'] = 'ended'
            result['message'] = '选课已结束'
        elif data == '-5':
            result['status'] = 'lottery'
            result['message'] = '抽签阶段'
        elif data == '-9':
            result['status'] = 'no_need'
            result['message'] = '无需选课'
        elif '@' in data:
            parts = data.split('@')
            result['status'] = 'success'
            result['lubn'] = parts[0]
            result['type'] = parts[1] if len(parts) > 1 else ''
            result['message'] = f'选课已开放（lubn={parts[0]}, type={result["type"]}）'
        return result

    def detect_apis(self):
        r = self._start_select()
        if r['status'] == 'auth_error':
            self.log(f'✗ {r["message"]}')
            return False
        if r['status'] == 'success':
            self.lubn = r['lubn']
            self.select_type = r['type']
            self.log(f'✓ {r["message"]}')
            if self._extract_apis_from_page(self.lubn, self.select_type):
                return True
            self.log('⚠ 未能从选课页面提取接口，使用默认路径')
        else:
            self.log(f'⚠ {r["message"]}，将使用默认接口路径，选课开放后自动适配')
        self._set_default_apis()
        return True

    def _set_default_apis(self):
        base = self.base_url + '/Student/CourseSelection/CourseSelectionHandler.ashx'
        self.query_url = base + '?action=SearchCourse'
        self.select_url = base + '?action=Selecting&ron=' + str(random.random())

    def _extract_apis_from_page(self, lubn, type_):
        if type_ == '1':
            page_path = f'/CourseSelectHtml/{lubn}/all.html'
        else:
            page_path = f'/CourseSelectHtml/{lubn}/all_FormalSelecting.html'
        self.select_page_path = page_path
        try:
            resp = self.session.get(self.base_url + page_path, timeout=5)
            if resp.status_code != 200 or 'Login.aspx' in resp.url:
                return False
            resp.encoding = 'utf-8'
            self.page_html = resp.text
            m = re.search(r'id="cstaskId"\s+value="(\d+)"', resp.text)
            if m:
                self.cstask_id = m.group(1)
            js_url = self.base_url + '/Student/CourseSelection/FormalCourseSelect.js'
            js_resp = self.session.get(js_url, timeout=5)
            if js_resp.status_code == 200:
                self._parse_js(js_resp.text)
                if self.select_url:
                    return True
        except Exception:
            pass
        return False

    def _parse_js(self, js_text):
        m = re.search(r"['\"]([^'\"]*action=SearchCourse[^'\"]*)['\"]", js_text)
        if m:
            self.query_url = self._fix_url(m.group(1))
        m = re.search(r"['\"]([^'\"]*action=Selecting[^'\"]*)['\"]", js_text)
        if m:
            url = m.group(1)
            if 'ron=' not in url:
                url += '&ron=' + str(random.random())
            self.select_url = self._fix_url(url)

    def _fix_url(self, url):
        if url.startswith('http'):
            return url
        if url.startswith('/'):
            return self.base_url + url
        return self.base_url + '/' + url

    def find_course(self, keyword):
        courses = self.find_all_courses(keyword)
        return courses[0] if courses else None

    def find_all_courses(self, keyword='', class_name=''):
        if not self.page_html:
            if not self.lubn:
                return []
            self._extract_apis_from_page(self.lubn, self.select_type or '4')
        if not self.page_html:
            return []
        return self._parse_courses_from_html(self.page_html, keyword, class_name)

    def find_courses_for_class(self, class_name):
        return self.find_all_courses(keyword='', class_name=class_name)

    @staticmethod
    def get_builtin_courses(class_name=''):
        courses = []
        for c in BUILTIN_COURSES:
            if class_name and class_name not in c['classes']:
                continue
            courses.append({
                'name': c['name'], 'sn': c['sn'], 'assign': c['assign'],
                'credit': c['credit'], 'capacity': c['capacity'],
                'remaining': -1,
                'dcid': c['dcid'], 'course_id': c['course_id'],
                'classes': c['classes'], 'raw': {}
            })
        return courses

    def _parse_courses_from_html(self, html, keyword='', class_name=''):
        courses = []
        trs = re.findall(r'<tr class="item"[^>]*>.*?</tr>', html, re.S)
        for tr in trs:
            tds = re.findall(r'<td[^>]*>(.*?)</td>', tr, re.S)
            if len(tds) < 7:
                continue
            name = re.sub(r'<[^>]+>', '', tds[1]).strip()
            if keyword and keyword not in name:
                continue
            sn = re.sub(r'<[^>]+>', '', tds[2]).strip()
            assign = re.sub(r'<[^>]+>', '', tds[3]).strip()
            credit = re.sub(r'<[^>]+>', '', tds[4]).strip()
            capacity = re.sub(r'<[^>]+>', '', tds[5]).strip()
            selected = re.sub(r'<[^>]+>', '', tds[6]).strip()
            cap = int(capacity) if capacity.isdigit() else 0
            sel = int(selected) if selected.isdigit() else 0
            dcid_m = re.search(r'Selecting\(this,"(\d+)"', tr)
            luid_m = re.search(r"luid='(\d+)'", tr)
            dcid = dcid_m.group(1) if dcid_m else ''
            luid = luid_m.group(1) if luid_m else ''
            classes = []
            if len(tds) > 7:
                classes_text = re.sub(r'<[^>]+>', ' ', tds[7])
                classes = [c.strip() for c in classes_text.split() if c.strip()]
            if class_name and class_name not in classes:
                continue
            courses.append({
                'name': name, 'sn': sn, 'assign': assign,
                'credit': credit, 'capacity': cap, 'remaining': cap - sel,
                'dcid': dcid, 'course_id': luid, 'classes': classes, 'raw': {}
            })
        return courses

    def submit_select(self, course):
        if not self.select_url:
            return False, '未找到选课接口'
        try:
            raw = course.get('raw', {}) if course else {}
            dcid = course.get('dcid', raw.get('dcId', ''))
            lu_id = course.get('course_id', raw.get('courseId', ''))
            credit = course.get('credit', raw.get('credit', 0))
            params = {'dcid': dcid, 'luID': lu_id, 'credit': credit}
            if self.cstask_id:
                params['cstaskId'] = self.cstask_id
            url = self.select_url
            if 'ron=' not in url:
                url += '&ron=' + str(random.random())
            headers = {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Origin': self.base_url,
            }
            if self.select_page_path:
                headers['Referer'] = f'{self.base_url}{self.select_page_path}?rondom={random.random()}'
            resp = self.session.post(url, data=params, headers=headers, timeout=3)
            return self._check_result(resp)
        except Exception as e:
            return False, str(e)

    def _check_result(self, resp):
        text = resp.text.strip()
        if text in ('logintimeout', 'nopermission'):
            return False, 'Cookie过期'
        if text == '-555':
            return False, '操作过快(-555)'
        if text == '-200':
            return False, '选课已暂停(-200)'
        if text == '-202':
            return False, '选课未到时间(-202)'
        if text == '-5':
            return False, '已选其他班(-5)'
        if text == '-3':
            return False, '时间冲突(-3)'
        if not text or text.lstrip('-').isdigit():
            return False, f'选课失败: {text}'
        try:
            data = json.loads(text)
            state = str(data.get('state', ''))
            if state == '9':
                return True, '选课成功'
            if state == '-8':
                return False, '没有名额了'
            if state == '-999':
                return False, f'条件限制: {data.get("Name", "")}'
            return False, f'选课失败: state={state}'
        except Exception:
            pass
        return False, text[:100]

    def run(self, open_time, advance_seconds, class_name, primary_courses, backup_courses, stop_check):
        self.log('=== 抢课脚本启动 ===')

        self.log('正在校准服务器时间...')
        if self.calibrate_time():
            direction = '快' if self.time_offset > 0 else '慢'
            self.log(f'✓ 时间已校准：服务器比本地{direction} {abs(self.time_offset):.2f} 秒')
        else:
            self.log('⚠ 时间校准失败，使用本地时间')

        self.log('正在检查 Cookie...')
        if not self.check_cookie():
            self.log('✗ Cookie 已过期，请重新登录教务系统并更新 Cookie')
            return False
        self.log('✓ Cookie 有效')

        self.log('正在探测选课接口...')
        self.detect_apis()
        if self.select_url:
            self.log(f'  选课接口: {self.select_url}')
        if self.cstask_id:
            self.log(f'  选课任务ID: {self.cstask_id}')

        self.log(f'目标班级: {class_name}')

        start_time = open_time - timedelta(seconds=advance_seconds)
        self.log(f'计划开始时间: {start_time.strftime("%Y-%m-%d %H:%M:%S")}（提前 {advance_seconds} 秒）')

        self.log('进入倒计时...')
        while not stop_check():
            now = self.server_now()
            remaining = (start_time - now).total_seconds()
            if remaining <= 0:
                break
            if remaining > 10:
                self.log(f'倒计时 {int(remaining)} 秒...')
                self.calibrate_time()
                time.sleep(5)
            elif remaining > 1:
                time.sleep(0.5)
            else:
                time.sleep(0.05)

        if stop_check():
            self.log('已停止')
            return False

        if not self.lubn:
            self.log('>>> 选课即将开放，重新探测接口...')
            self.detect_apis()
            if self.select_url:
                self.log(f'  选课接口: {self.select_url}')

        if primary_courses:
            self.primary_courses = primary_courses
            self.log(f'✓ 主选课程: {len(primary_courses)} 个教学班:')
            for c in primary_courses:
                self.log(f'  [主] {c["name"]} 班号{c["sn"]} dcid={c["dcid"]}')
        else:
            courses = self.get_builtin_courses(class_name)
            if not courses:
                self.log(f'✗ 内置数据中未找到 [{class_name}] 可选课程')
                return False
            self.primary_courses = courses
            self.log(f'✓ 内置数据: [{class_name}] 共 {len(courses)} 个教学班作为主选')

        self.backup_courses = backup_courses
        if backup_courses:
            self.log(f'✓ 备选课程: {len(backup_courses)} 个教学班:')
            for c in backup_courses:
                self.log(f'  [备] {c["name"]} 班号{c["sn"]} dcid={c["dcid"]}')

        self.target_courses = self.primary_courses

        self.log('>>> 开始秒抢！')
        success = self._rush(stop_check)

        if success:
            self.log('✅✅✅ 抢课成功！')
            return True

        if stop_check():
            self.log('已停止')
            return False

        self.log('>>> 转入捡漏模式...')
        success = self._scavenge(stop_check)

        if success:
            self.log('✅✅✅ 捡漏成功！')
            return True

        self.log('已停止')
        return False

    def _rush(self, stop_check):
        fail_count = 0
        delay = 0.1
        round_count = 0
        exhausted_primary = set()

        while not stop_check():
            primary = [c for c in self.primary_courses if c['dcid'] not in exhausted_primary]
            if primary:
                courses = primary
            else:
                courses = self.backup_courses or self.primary_courses

            if not courses:
                time.sleep(0.5)
                continue

            round_count += 1
            got_555 = False
            for c in courses:
                if stop_check():
                    return False
                success, msg = self.submit_select(c)
                fail_count += 1
                if success:
                    self.log(f'✅ 秒抢命中: {c["name"]} 班号{c["sn"]} → {msg}')
                    return True
                if '-555' in msg:
                    got_555 = True
                if '没有名额' in msg or '-8' in msg:
                    exhausted_primary.add(c['dcid'])

            if not primary and self.backup_courses:
                self.log(f'⚠ 主选全部没名额，已切换备选({len(self.backup_courses)}个)')

            if got_555:
                delay = min(delay * 1.5, 2.0)
                if delay < 0.3:
                    delay = 0.3
                self.log(f'⚠ 操作过快(-555)，减速至 {delay:.2f}秒/轮')
            elif round_count % 10 == 0 and delay > 0.1:
                delay = max(delay * 0.8, 0.1)
                self.log(f'✓ 连续10轮无-555，恢复至 {delay:.2f}秒/轮')

            if round_count % 20 == 0:
                self.log(f'秒抢第{round_count}轮，已提交{fail_count}次，间隔{delay:.2f}秒')

            time.sleep(delay)

        return False

    def _scavenge(self, stop_check):
        attempt = 0
        delay = 1.5
        all_courses = self.primary_courses + self.backup_courses
        while not stop_check():
            attempt += 1
            got_555 = False

            if attempt % 5 == 0 and self.lubn:
                fresh = self.find_all_courses()
                fresh_map = {c['dcid']: c for c in fresh}
                for c in all_courses:
                    if c['dcid'] in fresh_map:
                        c['remaining'] = fresh_map[c['dcid']]['remaining']

            for c in self.primary_courses:
                if stop_check():
                    return False
                if c['remaining'] > 0:
                    self.log(f'[捡漏 #{attempt}] [主] {c["name"]} 班号{c["sn"]} 余量{c["remaining"]}，立即提交！')
                    success, msg = self.submit_select(c)
                    if success:
                        self.log(f'捡漏成功: {msg}')
                        return True
                    else:
                        self.log(f'提交失败: {msg}')
                        if 'Cookie过期' in msg:
                            return False
                        if '-555' in msg:
                            got_555 = True
                        if '没有名额' in msg or '-8' in msg:
                            c['remaining'] = 0

            for c in self.backup_courses:
                if stop_check():
                    return False
                if c['remaining'] > 0:
                    self.log(f'[捡漏 #{attempt}] [备] {c["name"]} 班号{c["sn"]} 余量{c["remaining"]}，立即提交！')
                    success, msg = self.submit_select(c)
                    if success:
                        self.log(f'捡漏成功: {msg}')
                        return True
                    else:
                        self.log(f'提交失败: {msg}')
                        if 'Cookie过期' in msg:
                            return False
                        if '-555' in msg:
                            got_555 = True
                        if '没有名额' in msg or '-8' in msg:
                            c['remaining'] = 0

            if got_555:
                delay = min(delay * 1.5, 5.0)
                self.log(f'⚠ 操作过快，捡漏间隔增至 {delay:.1f}秒')
            elif delay > 1.5:
                delay = max(delay * 0.8, 1.5)
            if attempt % 20 == 0:
                self.log(f'[捡漏 #{attempt}] 暂无有余量的教学班，间隔 {delay:.1f}秒，继续等待...')
            time.sleep(delay + random.uniform(0, 0.5))

        return False