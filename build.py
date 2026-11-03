# src.html의 __img_이름__ 자리에 img/ 파일을 넣어 index.html 한 파일로 만듭니다.
# 고화질: 모든 이미지를 3배(1206×2622, 1080p급 이상)로 확대 + 선명화해 WebP로 넣음 → 레티나·고해상도 화면에서 선명
import base64, io, os, re
from PIL import Image, ImageFilter
d = os.path.dirname(os.path.abspath(__file__))
CACHE = f'{d}/.hq'; os.makedirs(CACHE, exist_ok=True)
SCALE = 3

def factor(name):
    if name.startswith('ev_part_'): return 1.5      # 키링 부품은 이미 2배 해상도
    if name.startswith('el_') or name == 'f_card': return 1   # 이미 고해상도로 만든 이미지
    return SCALE

def upscale(path, name):
    im = Image.open(path); f = factor(name)
    alpha = im.mode in ('RGBA', 'LA', 'P') and 'A' in im.convert('RGBA').getbands()
    im = im.convert('RGBA') if alpha else im.convert('RGB')
    if f != 1:
        size = (round(im.width * f), round(im.height * f))
        if alpha:   # 미리곱한 알파로 확대 → 가장자리 어두운 테두리 없음
            im = im.convert('RGBa').resize(size, Image.LANCZOS).convert('RGBA')
        else:
            im = im.resize(size, Image.LANCZOS)
        rgb = im.convert('RGB').filter(ImageFilter.UnsharpMask(radius=2.4, percent=70, threshold=1))
        if alpha: rgb.putalpha(im.getchannel('A')); im = rgb
        else: im = rgb
    return im, alpha

def data_uri(name, fname):
    src = f'{d}/img/{fname}'; is_mask = name.endswith('_mask')
    out = f'{CACHE}/{name}.{"png" if is_mask else "webp"}'
    if not os.path.exists(out) or os.path.getmtime(out) < max(os.path.getmtime(src), os.path.getmtime(__file__)):
        im, alpha = upscale(src, name)
        if is_mask: im.save(out, 'PNG', optimize=True)
        else: im.save(out, 'WEBP', quality=88 if not alpha else 90, method=6)
    mime = 'image/png' if is_mask else 'image/webp'
    return f'data:{mime};base64,' + base64.b64encode(open(out, 'rb').read()).decode()

h = open(f'{d}/src.html').read()
files = {os.path.splitext(f)[0]: f for f in os.listdir(f'{d}/img')}
used = set(re.findall(r'__img_([a-z0-9_]+?)__', h))
missing = used - set(files); assert not missing, missing
uris = {n: data_uri(n, files[n]) for n in used}
h = re.sub(r'__img_([a-z0-9_]+?)__', lambda m: uris[m.group(1)], h)
for n in set(re.findall(r'__snd_([a-z0-9_]+?)__', h)):   # 사운드
    h = h.replace(f'__snd_{n}__', 'data:audio/mp4;base64,' + base64.b64encode(open(f'{d}/snd/{n}.m4a', 'rb').read()).decode())
# Claude 아티팩트용: 문서 머리말 없이 (뷰어가 붙여 줌)
open(f'{d}/artifact.html', 'w').write(h)
# GitHub Pages용: 완전한 HTML 문서 (doctype·문자 인코딩·뷰포트 포함 → 표준 모드로 정확히 렌더링)
full = ('<!DOCTYPE html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<meta name="theme-color" content="#050505">\n' + h + '\n</html>\n')
open(f'{d}/index.html', 'w').write(full); print(len(h) // 1024, 'KB,', len(used), 'images')
