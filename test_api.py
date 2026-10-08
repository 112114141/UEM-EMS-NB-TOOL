import requests
import re
import sys

BASE = 'https://jw.cidp.edu.cn'
COOKIE = sys.argv[1] if len(sys.argv) > 1 else input('请输入Cookie: ').strip()

s = requests.Session()
s.headers['Cookie'] = COOKIE
s.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'

print('=== 1. 检查Cookie ===')
resp = s.get(f'{BASE}/Navigation/Default.htm?v=5', timeout=5, allow_redirects=True)
if 'Login.aspx' in resp.url:
    print('✗ Cookie已过期！请重新登录教务系统获取新Cookie。')
    sys.exit(1)
print('✓ Cookie有效')

print('\n=== 2. 调用startSelect ===')
resp = s.post(f'{BASE}/Student/CourseSelection/CourseSelectionHandler.ashx?action=startSelect', timeout=5)
data = resp.text.strip()
print(f'返回值: {data}')

if data == '-20':
    print('选课已暂停，无法测试。请等选课开放后再运行此脚本。')
    sys.exit(0)
elif data == '-1' or data.startswith('-1,'):
    print('选课尚未开始，无法测试。请等选课开放后再运行此脚本。')
    sys.exit(0)
elif data == '-2':
    print('选课已结束。')
    sys.exit(0)
elif '@' not in data:
    print(f'未知返回值: {data}')
    sys.exit(1)

lubn, type_ = data.split('@')
print(f'✓ 选课已开放！lubn={lubn}, type={type_}')

if type_ == '1':
    page = f'/CourseSelectHtml/{lubn}/all.html'
    label = '预选'
else:
    page = f'/CourseSelectHtml/{lubn}/all_FormalSelecting.html'
    label = '正选/抢选'
print(f'\n=== 3. 访问{label}页面: {page} ===')

resp = s.get(f'{BASE}{page}', timeout=5)
if resp.status_code != 200:
    print(f'✗ 页面返回 {resp.status_code}')
    sys.exit(1)
print(f'✓ 页面获取成功，{len(resp.text)} 字节')

print('\n=== 4. 提取所有ashx接口 ===')
urls = re.findall(r"['\"]([^'\"]*\.ashx[^'\"]*action=\w+[^'\"]*)['\"]", resp.text, re.I)
if urls:
    for u in urls:
        action = re.search(r'action=(\w+)', u, re.I)
        act = action.group(1) if action else '?'
        full = u if u.startswith('http') else (BASE + u if u.startswith('/') else BASE + '/' + u)
        print(f'  [{act}] {full}')
else:
    print('  未找到任何ashx接口！')
    print('  页面内容前500字符:')
    print(resp.text[:500])

print('\n=== 5. 尝试调用查询接口 ===')
query_url = None
select_url = None
for u in urls:
    action = re.search(r'action=(\w+)', u, re.I)
    if not action:
        continue
    act = action.group(1).lower()
    full = u if u.startswith('http') else (BASE + u if u.startswith('/') else BASE + '/' + u)
    if not query_url and any(k in act for k in ['query', 'get', 'load', 'search', 'list']):
        query_url = full
    elif not select_url and any(k in act for k in ['submit', 'save', 'select', 'xk', 'add']):
        select_url = full

if query_url:
    print(f'查询接口: {query_url}')
    resp = s.post(query_url, data={'lubn': lubn}, timeout=5)
    print(f'返回前200字符: {resp.text[:200]}')
else:
    print('✗ 未找到查询接口')

if select_url:
    print(f'\n选课接口: {select_url}')
    print('（不会自动提交，仅展示接口地址）')
else:
    print('✗ 未找到选课接口')

print('\n=== 完成 ===')
print(f'lubn={lubn}, type={type_}')
if query_url:
    print(f'query_url={query_url}')
if select_url:
    print(f'select_url={select_url}')