# Pretendard에서 이 페이지에 쓰인 글자만 뽑아 작은 woff2로 만듭니다. (pretendard 패키지 경로를 인자로)
import re, sys, os
from fontTools import subset
pkg = sys.argv[1]
d = os.path.dirname(os.path.abspath(__file__))
src = open(f'{d}/src.html', encoding='utf-8').read()
text = re.sub(r'data:[^"\')]+', '', src)
chars = set(text) | set('0123456789:~!?.,ㅋㅎㅠㄱ ')
chars = ''.join(sorted(c for c in chars if c >= ' '))
for w in ['Medium', 'SemiBold', 'Bold']:
    opts = subset.Options(); opts.flavor = 'woff2'; opts.layout_features = ['*']; opts.name_IDs = ['*']
    f = subset.load_font(f'{pkg}/dist/web/static/woff2/Pretendard-{w}.woff2', opts)
    s = subset.Subsetter(opts); s.populate(text=chars); s.subset(f)
    subset.save_font(f, f'{d}/fonts/pretendard-{w.lower()}.woff2', opts)
    print(w, os.path.getsize(f'{d}/fonts/pretendard-{w.lower()}.woff2') // 1024, 'KB')
