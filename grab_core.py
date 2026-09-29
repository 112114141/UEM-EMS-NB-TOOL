import requests
import time
import random
import re
import json
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


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
        self.target_course = None
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

    def detect_apis(self):
        paths = [
            '/xsxk/xsxk_index.aspx',
            '/xsxk/xsxk.aspx',
            '/xsxk/xsxk.aspx?from=menu',
        ]
        for path in paths:
            try:
                resp = self.session.get(
                    self.base_url + path, timeout=5, allow_redirects=True
                )
                if resp.status_code == 200 and 'Login.aspx' not in resp.url:
                    self._parse_page(resp.text)
                    if self.select_url or self.query_url:
                        return True
            except Exception:
                pass
        return False

    def _parse_page(self, html):
        query_patterns = [
            r"['\"]([^'\"]*\.ashx[^'\"]*(?:method=|type=)?"
            r"(?:Query|GetCourse|GetList|Search|LoadData|BindData)[^'\"]*)['\"]",
            r"url\s*[:=]\s*['\"]([^'\"]*xsxk[^'\"]*\.ashx[^'\"]*)['\"]",
            r"['\"]([^'\"]*xsxk[^'\"]*\.ashx[^'\"]*method=query[^'\"]*)['\"]",
        ]
        for p in query_patterns:
            m = re.search(p, html, re.I)
            if m:
                self.query_url = self._fix_url(m.group(1))
                break

        select_patterns = [
            r"['\"]([^'\"]*\.ashx[^'\"]*(?:method=|type=)?"
            r"(?:Select|Save|Submit|Xk|Choose|Add|XuanKe)[^'\"]*)['\"]",
            r"['\"]([^'\"]*xsxk[^'\"]*\.ashx[^'\"]*method=select[^'\"]*)['\"]",
        ]
        for p in select_patterns:
            m = re.search(p, html, re.I)
            if m:
                self.select_url = self._fix_url(m.group(1))
                break

    def _fix_url(self, url):
        if url.startswith('http'):
            return url
        if url.startswith('/'):
            return self.base_url + url
        return self.base_url + '/' + url

    def find_course(self, keyword):
        if not self.query_url:
            return None
        try:
            resp = self.session.post(self.query_url, timeout=5)
            courses = self._extract_courses(resp)
            for c in courses:
                if keyword in c.get('name', ''):
                    return c
        except Exception:
            pass
        return None

    def _extract_courses(self, resp):
        courses = []
        data = None
        try:
            data = resp.json()
        except Exception:
            text = resp.text
            m = re.search(r'\{.*\}', text, re.S)
            if m:
                try:
                    data = json.loads(m.group())
                except Exception:
                    return []

        if data is None:
            return []

        items = None
        if isinstance(data, dict):
            for k in ['data', 'Data', 'rows', 'list', 'result', 'Rows', 'datas']:
                if k in data and isinstance(data[k], list):
                    items = data[k]
                    break
        elif isinstance(data, list):
            items = data

        if items:
            for item in items:
                if isinstance(item, dict):
                    courses.append(self._parse_course(item))
        return courses

    def _parse_course(self, item):
        name = ''
        for k in ['kcmc', 'courseName', 'KCMC', 'name', 'Name', 'kcmc']:
            if k in item and item[k]:
                name = str(item[k])
                break

        remaining = 0
        for k in ['kxrs', 'remaining', 'yxrs', 'KxRs', 'YxRs',
                   'remain', 'Remain', 'surplus', 'kyrs']:
            if k in item:
                try:
                    remaining = int(item[k])
                except (ValueError, TypeError):
                    pass
                break

        return {'name': name, 'remaining': remaining, 'raw': item}

    def submit_select(self, course):
        if not self.select_url:
            return False, '未找到选课接口'
        try:
            params = {}
            raw = course.get('raw', {}) if course else {}
            for k in ['id', 'kcid', 'courseId', 'kcbh',
                       'Id', 'ID', 'KCID', 'xkxxid', 'do_jh_id']:
                if k in raw:
                    params[k] = raw[k]
            resp = self.session.post(self.select_url, data=params, timeout=3)
            return self._check_result(resp)
        except Exception as e:
            return False, str(e)

    def _check_result(self, resp):
        text = resp.text
        low = text.lower()
        if any(kw in text for kw in
               ['成功', '"code":1', '"code": 1', '"status":"ok"', '"status": "ok"']):
            return True, '选课成功'
        if any(kw in low for kw in
               ['"success":true', '"result":true', '"code":1', '"status":"ok"']):
            return True, '选课成功'
        if any(kw in text for kw in
               ['已满', '容量', '人数已满', '已选满']):
            return False, '课程已满'
        if any(kw in low for kw in ['full', '已满']):
            return False, '课程已满'
        if any(kw in low for kw in ['失败', 'fail', 'error']):
            return False, '选课失败'
        if 'login' in low or 'login.aspx' in low:
            return False, 'Cookie过期'
        return False, text[:100]

    def run(self, open_time, advance_seconds, keyword, stop_check):
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
        if self.detect_apis():
            self.log('✓ 接口探测成功')
            if self.query_url:
                self.log(f'  查询接口: {self.query_url}')
            if self.select_url:
                self.log(f'  选课接口: {self.select_url}')
        else:
            self.log('✗ 接口自动探测失败')
            self.log('  教务系统可能尚未开放选课，或接口路径非标准正方格式')
            self.log('  请等教务系统更新后用 Cookie 测试验证')
            return False

        self.log(f'目标课程关键词: {keyword}')
        course = self.find_course(keyword)
        if course:
            self.log(f'✓ 已定位课程: {course["name"]}，当前余量: {course["remaining"]}')
            self.target_course = course
        else:
            self.log(f'⚠ 暂未找到包含"{keyword}"的课程，将在抢课时持续尝试')

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

        self.log('>>> 开始秒抢！')
        success = self._rush(keyword, stop_check)

        if success:
            self.log('✅✅✅ 抢课成功！')
            return True

        if stop_check():
            self.log('已停止')
            return False

        self.log('>>> 转入捡漏模式...')
        success = self._scavenge(keyword, stop_check)

        if success:
            self.log('✅✅✅ 捡漏成功！')
            return True

        self.log('已停止')
        return False

    def _rush(self, keyword, stop_check):
        fail_count = 0
        last_check_time = time.time()

        with ThreadPoolExecutor(max_workers=5) as executor:
            while not stop_check():
                course = self.target_course
                if not course:
                    course = self.find_course(keyword)
                    if course:
                        self.target_course = course
                        self.log(f'定位到课程: {course["name"]}，余量: {course["remaining"]}')

                if not course:
                    time.sleep(0.5)
                    continue

                futures = [executor.submit(self.submit_select, course)
                           for _ in range(5)]
                try:
                    for f in as_completed(futures, timeout=5):
                        success, msg = f.result()
                        if success:
                            self.log(f'秒抢命中: {msg}')
                            return True
                except Exception:
                    for f in futures:
                        f.cancel()
                    self.log('⚠ 本轮提交超时，已跳过')

                fail_count += 5
                if fail_count % 50 == 0:
                    self.log(f'秒抢已提交 {fail_count} 次，尚未成功')

                now = time.time()
                if now - last_check_time >= 2:
                    last_check_time = now
                    c = self.find_course(keyword)
                    if c:
                        self.target_course = c
                        if c['remaining'] == 0:
                            self.log('课余量为 0，秒抢窗口已过，转入捡漏')
                            return False
                        elif fail_count % 50 == 0:
                            self.log(f'余量 {c["remaining"]}，继续秒抢')

                time.sleep(0.05)

        return False

    def _scavenge(self, keyword, stop_check):
        attempt = 0
        while not stop_check():
            attempt += 1
            course = self.find_course(keyword)
            if course:
                remaining = course['remaining']
                if remaining > 0:
                    self.log(f'[捡漏 #{attempt}] {course["name"]} 余量 {remaining}，立即提交！')
                    success, msg = self.submit_select(course)
                    if success:
                        self.log(f'捡漏成功: {msg}')
                        return True
                    else:
                        self.log(f'提交失败: {msg}')
                        if 'Cookie过期' in msg:
                            self.log('✗ Cookie 已过期，请重新登录更新 Cookie')
                            return False
                else:
                    if attempt % 20 == 0:
                        self.log(f'[捡漏 #{attempt}] {course["name"]} 已满，继续等待...')
            else:
                if attempt % 20 == 0:
                    self.log(f'[捡漏 #{attempt}] 未找到课程，继续等待...')

            time.sleep(1.5 + random.uniform(0, 0.5))

        return False