# 디자인 화면(1x 캡처)에서 프로토타입용 레이어를 잘라냅니다.
import numpy as np, sys, os
from PIL import Image, ImageFilter
SRC = sys.argv[1]
O = 'img'
L = lambda n: Image.open(f'{SRC}/{n}.jpg').convert('RGB')
dim3, dim4, fort, home, homeT = L(3), L(4), L(5), L(6), L(7)

def feather(im, px=3):
    """사각 크롭 가장자리를 부드럽게 — 배경과 이음새가 보이지 않도록"""
    w, h = im.size
    a = np.ones((h, w), np.float32)
    for i in range(px):
        v = (i + 1) / (px + 1)
        a[i, :] = np.minimum(a[i, :], v); a[h-1-i, :] = np.minimum(a[h-1-i, :], v)
        a[:, i] = np.minimum(a[:, i], v); a[:, w-1-i] = np.minimum(a[:, w-1-i], v)
    out = im.convert('RGBA'); out.putalpha(Image.fromarray((a*255).astype(np.uint8))); return out

def rowspan_mask(arr, is_inside, y0=0):
    h, w = arr.shape[:2]; m = np.zeros((h, w), np.float32)
    for y in range(y0, h):
        xs = np.nonzero(is_inside[y])[0]
        if len(xs): m[y, xs.min():xs.max()+1] = 1
    return Image.fromarray((m*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(.6))

def superellipse_mask(inside):
    """카드는 상하좌우 대칭 — 윗변 모서리 곡선을 재서 아래쪽에 그대로 반사 (아이템에 가려진 아래 모서리 복원)"""
    h, w = inside.shape
    rows = [y for y in range(h) if inside[y].any()]
    top = rows[0]
    left = {y: np.nonzero(inside[y])[0].min() for y in rows}
    right = {y: np.nonzero(inside[y])[0].max() for y in rows}
    lmin = min(left.values()); rmax = max(right.values()); cx = (lmin + rmax) / 2
    col = inside[:, lmin + 2]; side = np.nonzero(col)[0]
    bottom = top + (side.max() - top) + (side.min() - top)
    prof = []
    for y in range(top, h):
        if y in left: prof.append(max(cx - left[y], right[y] - cx))
        else: prof.append(prof[-1] if prof else 0)
        if prof[-1] >= (rmax - lmin) / 2 - .5: break
    full = (rmax - lmin + 1) / 2
    m = np.zeros((h * 4, w * 4), np.float32)
    for yy in range(h * 4):
        y = yy / 4
        if y < top or y > bottom: continue
        d = min(y - top, bottom - y)
        i = int(d); hw = prof[i] if i < len(prof) else full
        x0 = int((cx - hw) * 4); x1 = int((cx + hw + 1) * 4)
        m[yy, max(0, x0):min(w * 4, x1)] = 1
    return Image.fromarray((m * 255).astype(np.uint8)).resize((w, h), Image.LANCZOS)

def key_out_background(im, is_bg):
    """테두리에서 연결된 배경 색만 투명하게 (글자 속 같은 색은 유지)"""
    h, w = is_bg.shape; seen = np.zeros_like(is_bg); stack = []
    for x in range(w): stack += [(0, x), (h - 1, x)]
    for y in range(h): stack += [(y, 0), (y, w - 1)]
    while stack:
        y, x = stack.pop()
        if 0 <= y < h and 0 <= x < w and not seen[y, x] and is_bg[y, x]:
            seen[y, x] = True; stack += [(y+1, x), (y-1, x), (y, x+1), (y, x-1)]
    alpha = Image.fromarray(((~seen) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(.5))
    out = im.convert('RGBA'); out.putalpha(alpha); return out

# ── 오늘의운세_딤: X·버튼이 없는 배경 (딤 화면에서 해당 영역만 가져옴)
base = dim4.copy()
for box in [(316, 217, 360, 261), (130, 606, 272, 663)]:
    base.paste(dim3.crop(box), box[:2])
base.save(f'{O}/dim_base.jpg', quality=92)
for name, box in [('dim_x', (316, 217, 360, 261)), ('dim_btn', (130, 606, 272, 663))]:
    feather(dim4.crop(box), 4).save(f'{O}/{name}.png')

# ── 모달 카드 (민트) : 민트 픽셀의 좌우 끝으로 카드 모양 마스크
box = (58, 225, 356, 580); c = dim4.crop(box); a = np.asarray(c).astype(int)
mint = (a[..., 1] > 200) & (a[..., 0] < 90) & (a[..., 2] > 150)
mask = superellipse_mask(mint); c = c.convert('RGBA'); c.putalpha(mask); c.save(f'{O}/modal_card.png')
mk = Image.new('RGBA', mask.size, (0, 0, 0, 0)); mk.putalpha(mask); mk.save(f'{O}/modal_mask.png')  # CSS mask는 알파 채널을 씀
# 블러용 불투명 버전: 카드 밖을 민트로 채워 블러 시 가장자리가 어두워지지 않게
fill = Image.new('RGB', c.size, (0, 255, 195)); fill.paste(c, (0, 0), c); fill.save(f'{O}/modal_fill.jpg', quality=92)

# ── 운세 화면 카드 (검정) : 스티커가 겹친 윗부분은 카드색으로 메움
box = (34, 215, 368, 549); c = fort.crop(box); a = np.asarray(c).copy()
x0, y0 = box[:2]
a[219-y0:253-y0, 120-x0:290-x0] = (14, 14, 14)
c = Image.fromarray(a); ai = a.astype(int)
dark = ~((ai[..., 1] > 200) & (ai[..., 0] < 140))
mask = rowspan_mask(ai, dark, y0=219-y0); c = c.convert('RGBA'); c.putalpha(mask); c.save(f'{O}/f_card.png')

# ── 운세 화면 요소들 (민트 배경 위 사각 크롭 + 가장자리 페더)
for name, box in {
    'f_status': (0, 0, 402, 52), 'f_header': (0, 52, 402, 110),
    'f_title': (40, 570, 362, 614), 'f_body': (28, 614, 374, 668),
    'f_chip1': (80, 690, 322, 754), 'f_chip2': (44, 752, 358, 814), 'f_home': (120, 848, 282, 872),
}.items():
    feather(fort.crop(box), 4).save(f'{O}/{name}.png')

# 스티커: 민트 배경과 카드 검정(14)만 빼고 — 스티커 외곽선은 순수 검정(0)이라 구분됨
st = fort.crop((122, 138, 288, 258)); sa = np.asarray(st).astype(int)
mint_bg = (sa[..., 1] - sa[..., 0] > 12)                       # 민트 및 민트-검정 경계색
card_bg = (np.abs(sa - 14).max(2) <= 4) | (sa.min(2) > 50)      # 카드 검정, 아래쪽 막대(회색)
key_out_background(st, mint_bg | card_bg).save(f'{O}/f_sticker.png')

# ── 홈
home.save(f'{O}/home.jpg', quality=92)
for name, src in []:  # 아래 CARDS에서 처리
    feather(src.crop((14, 474, 388, 648)), 3).save(f'{O}/{name}.png')
print(np.asarray(fort)[300, 10], np.asarray(fort)[800, 10])

# ═════════ 홈 카드 3종 선택 상태 + Lucky 상세 화면 ═════════
L8, L9, L10, L11, L12 = L(8), L(9), L(10), L(11), L(12)
MINT = np.array([94, 255, 199], float); WHITE_CARD = 244

def to_selected(crop):
    """흰 카드 → 민트 카드, 핑크 화살표 원 → 검정 원 (홈_탭 시안의 Lucky Place 규칙을 그대로 적용)"""
    a = np.asarray(crop).astype(float); h, w, _ = a.shape
    pink = (a[..., 0] > 200) & (a[..., 1] < 150) & (a[..., 2] > 150)
    ys, xs = np.nonzero(pink); cy, cx = ys.mean(), xs.mean()
    r = np.percentile(np.hypot(ys - cy, xs - cx), 99.5)
    yy, xx = np.mgrid[0:h, 0:w]; dist = np.hypot(yy - cy, xx - cx)
    t = np.clip((a.mean(2) - 12) / (WHITE_CARD - 12), 0, 1)[..., None]
    out = 12 + t * (MINT - 12)                                    # 카드 바탕·글자
    p = np.clip((245 - a[..., 1]) / (245 - 56), 0, 1)[..., None]  # 핑크 비율
    base = np.where((dist < r - 1.5)[..., None], 255.0, MINT)     # 원 안 글리프=흰색, 원 밖=민트
    ring = (dist < r + 2)[..., None]
    out = np.where(ring, (1 - p) * base, out)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))

CARDS = {'item': (14, 282, 388, 474), 'place': (14, 474, 388, 648), 'music': (14, 648, 388, 781)}
for name, box in CARDS.items():
    off = home.crop(box)
    on = homeT.crop(box) if name == 'place' else to_selected(off)
    feather(off, 3).save(f'{O}/{name}_off.png'); feather(on, 3).save(f'{O}/{name}_on.png')
# 검증용: 시안의 Lucky Place 탭 상태와 자동 변환 결과의 차이
diff = np.abs(np.asarray(to_selected(home.crop(CARDS['place']))).astype(int) - np.asarray(homeT.crop(CARDS['place'])).astype(int))
print('place recolor mean abs diff', diff.mean().round(2), 'p99', np.percentile(diff, 99))

# 상세 화면: 같은 레이아웃이라 같은 박스로 자름 (배경 #0e0e0e 위 사각 크롭 + 페더)
DETAIL = {'head': (0, 0, 402, 112), 'hero': (18, 110, 384, 480), 'body': (28, 482, 374, 538),
          'icons': (18, 606, 384, 742), 'btn': (14, 774, 388, 848), 'bar': (120, 848, 282, 872)}
for key, src in [('d_item', L8), ('d_place', L9), ('d_music', L10)]:
    for part, box in DETAIL.items():
        feather(src.crop(box), 4).save(f'{O}/{key}_{part}.png')
L11.save(f'{O}/shop1.jpg', quality=90); L12.save(f'{O}/shop2.jpg', quality=90)

# ═════════ 홈_기본_담기버튼 · Place/Music 연결 · 행운 담기(카메라) · 참 ═════════
L13, L14, L15, L16, L17 = L(13), L(14), L(15), L(16), L(17)
L13.save(f'{O}/place_link.jpg', quality=90); L14.save(f'{O}/music_link.jpg', quality=90)

# 홈 교체: 담기 버튼이 생기며 카드가 아래로 내려감
L15.save(f'{O}/home.jpg', quality=92)
def to_selected_safe(crop):
    a = np.asarray(crop).astype(float)
    if ((a[..., 0] > 200) & (a[..., 1] < 150) & (a[..., 2] > 150)).sum() > 40: return to_selected(crop)
    t = np.clip((a.mean(2) - 12) / (WHITE_CARD - 12), 0, 1)[..., None]    # 화살표가 내비 뒤에 가려진 카드
    return Image.fromarray(np.clip(12 + t * (MINT - 12), 0, 255).astype(np.uint8))
CARDS2 = {'item': (14, 364, 388, 553), 'place': (14, 553, 388, 728), 'music': (14, 728, 388, 781)}
for name, box in CARDS2.items():
    off = L15.crop(box)
    feather(off, 3).save(f'{O}/{name}_off.png'); feather(to_selected_safe(off), 3).save(f'{O}/{name}_on.png')
feather(L15.crop((124, 298, 278, 352)), 3).save(f'{O}/home_cta.png')

# 카메라: 뷰파인더 사진(모양 마스크) + 1x 칩 + 썸네일
vb = (18, 203, 384, 651); vf = L16.crop(vb); va = np.asarray(vf).astype(int)
inside = np.abs(va - 14).max(2) > 10
vmask = superellipse_mask(inside)
mk = Image.new('RGBA', vmask.size, (0, 0, 0, 0)); mk.putalpha(vmask); mk.save(f'{O}/cam_mask.png')
# 사진 속 1x 칩 지우기: 주변 링 색으로 채운 뒤 블러 (흔들림 표현 때 칩이 두 개로 보이지 않게)
cx, cy, r = 201 - vb[0], 610 - vb[1], 23
arr = np.asarray(vf).copy(); yy, xx = np.mgrid[0:arr.shape[0], 0:arr.shape[1]]; d = np.hypot(yy - cy, xx - cx)
ring = (d > r) & (d < r + 6)
for y, x in zip(*np.nonzero(d <= r)):
    ang = np.arctan2(y - cy, x - cx); sy, sx = int(cy + (r + 3) * np.sin(ang)), int(cx + (r + 3) * np.cos(ang))
    arr[y, x] = arr[min(max(sy, 0), arr.shape[0]-1), min(max(sx, 0), arr.shape[1]-1)]
patched = Image.fromarray(arr); blur = patched.filter(ImageFilter.GaussianBlur(4))
m = Image.fromarray(((d <= r + 2) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2))
patched.paste(blur, (0, 0), m); patched.save(f'{O}/cam_photo.jpg', quality=92)
chip = L16.crop((176, 585, 226, 635)).convert('RGBA'); cd = np.hypot(*np.mgrid[-24.5:25, -24.5:25])
chip.putalpha(Image.fromarray(np.clip((21.5 - cd) * 255, 0, 255).astype(np.uint8))); chip.save(f'{O}/cam_chip.png')
# 바탕: 뷰파인더·칩·셔터 안쪽을 비운 카메라 화면
base = L16.copy(); bd = ImageDraw.Draw(base) if False else None
base.save(f'{O}/cam_base.jpg', quality=92)
thumb = L16.crop((48, 684, 112, 748)); thumb.save(f'{O}/cam_thumb.png')

# 참 화면: 세로 그라데이션 배경을 줄마다 왼쪽 끝 색으로 복원해 참을 지우고, 참은 차이 키잉으로 분리
A17 = np.asarray(L17).astype(float); bgcol = A17[:, 6:14].mean(1)          # 줄별 배경색
cb = (100, 300, 312, 600); ch = A17[cb[1]:cb[3], cb[0]:cb[2]]; bgr = bgcol[cb[1]:cb[3]][:, None, :]
diff = np.abs(ch - bgr).max(2)
alpha = np.clip((diff - 5) / 40, 0, 1)
col = np.clip((ch - (1 - alpha[..., None]) * bgr) / np.maximum(alpha[..., None], 1e-3), 0, 255)
charm = np.dstack([col, alpha * 255]).astype(np.uint8)
Image.fromarray(charm, 'RGBA').save(f'{O}/charm.png')
clean = A17.copy(); clean[cb[1]:cb[3], cb[0]:cb[2]] = bgr
Image.fromarray(clean.astype(np.uint8)).save(f'{O}/charm_bg.jpg', quality=93)
feather(L17.crop((14, 80, 388, 176)), 4).save(f'{O}/charm_title.png')
feather(L17.crop((14, 776, 388, 848)), 4).save(f'{O}/charm_btn.png')
w = alpha / alpha.sum(); yy, xx = np.mgrid[0:alpha.shape[0], 0:alpha.shape[1]]
print('charm com (page)', round(float((w * xx).sum()) + cb[0], 1), round(float((w * yy).sum()) + cb[1], 1))

# ═════════ 참(확인 버튼) · 결과 · 모아보기 · 저녁(키링) ═════════
import shutil, glob
L18, L19, L20 = L(18), L(19), L(20)
# 참 화면: 버튼이 '확인'으로 바뀐 시안 기준으로 다시 추출
A18 = np.asarray(L18).astype(float); bgcol = A18[:, 6:14].mean(1)
ch = A18[cb[1]:cb[3], cb[0]:cb[2]]; bgr = bgcol[cb[1]:cb[3]][:, None, :]
alpha = np.clip((np.abs(ch - bgr).max(2) - 5) / 40, 0, 1)
col = np.clip((ch - (1 - alpha[..., None]) * bgr) / np.maximum(alpha[..., None], 1e-3), 0, 255)
Image.fromarray(np.dstack([col, alpha * 255]).astype(np.uint8), 'RGBA').save(f'{O}/charm.png')
clean = A18.copy(); clean[cb[1]:cb[3], cb[0]:cb[2]] = bgr
Image.fromarray(clean.astype(np.uint8)).save(f'{O}/charm_bg.jpg', quality=93)
feather(L18.crop((14, 776, 388, 848)), 4).save(f'{O}/charm_btn.png')

# 결과 화면 (오늘의 행운 담기)
for name, box in {'r_head': (0, 0, 402, 112), 'r_title': (14, 126, 388, 228), 'r_trio': (0, 250, 402, 470),
                  'r_sub': (60, 488, 342, 566), 'r_tile1': (18, 602, 142, 760), 'r_tile2': (142, 602, 264, 760),
                  'r_tile3': (264, 602, 386, 760), 'r_btn': (14, 776, 388, 848), 'r_bar': (120, 848, 282, 872)}.items():
    feather(L19.crop(box), 2 if 'tile' in name else 4).save(f'{O}/{name}.png')

# 모아보기 화면: 상단·버튼은 시안, 사진은 시안 속 카드 안쪽을 잘라 씀
feather(L20.crop((0, 0, 402, 206)), 4).save(f'{O}/c_head.png')
feather(L20.crop((14, 776, 388, 848)), 4).save(f'{O}/c_btn.png')
feather(L20.crop((120, 848, 282, 872)), 4).save(f'{O}/c_bar.png')
COL = {'girl': (60, 340, 140, 430), 'beads': (180, 378, 262, 462), 'poster': (28, 462, 122, 556),
       'blob': (142, 505, 234, 598), 'doll': (268, 470, 368, 584), 'coffee': (6, 598, 156, 752),
       'bunny': (182, 632, 300, 760), 'umbrella': (326, 600, 402, 756)}
for name, box in COL.items():
    L20.crop(box).save(f'{O}/col_{name}.jpg', quality=92)
for name in ['item', 'place', 'music']:   # 오늘 인증한 세 장소/아이템/음악 사진
    Image.open(f'{O}/d_{name}_hero.png').convert('RGB').crop((88, 70, 278, 260)).save(f'{O}/col_{name}.jpg', quality=92)

# 저녁 키링: 이전 프로토타입의 부품 레이어를 그대로 가져옴
for f in glob.glob('/home/user/spin-shutter-proto/parts/*.png'):
    shutil.copy(f, f'{O}/ev_part_' + os.path.basename(f))

# ═════════ 수정: 운세 카드 윗변 · 스티커 잡티 · Lucky Place 버튼 · 친구방 ═════════
L23, L25, L26, L27 = L(23), L(25), L(26), L(27)

def largest_component(alpha_u8, thr=40):
    """알파에서 가장 큰 덩어리만 남김 (스티커 주변 잡티 제거)"""
    m = alpha_u8 > thr; h, w = m.shape; lab = np.zeros((h, w), np.int32); n = 0; sizes = {}
    for y0 in range(h):
        for x0 in range(w):
            if m[y0, x0] and not lab[y0, x0]:
                n += 1; stack = [(y0, x0)]; lab[y0, x0] = n; c = 0
                while stack:
                    y, x = stack.pop(); c += 1
                    for yy, xx in ((y+1, x), (y-1, x), (y, x+1), (y, x-1)):
                        if 0 <= yy < h and 0 <= xx < w and m[yy, xx] and not lab[yy, xx]:
                            lab[yy, xx] = n; stack.append((yy, xx))
                sizes[n] = c
    keep = max(sizes, key=sizes.get)
    grown = Image.fromarray(((lab == keep) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))
    return np.minimum(alpha_u8, np.asarray(grown))

st = Image.open(f'{O}/f_sticker.png'); sa = np.asarray(st).copy()
sa[..., 3] = largest_component(sa[..., 3]); Image.fromarray(sa, 'RGBA').save(f'{O}/f_sticker.png')

# 운세 카드: 위쪽은 스티커에 가려 있으니, 깨끗한 아래쪽 곡선을 위아래로 뒤집어 카드 모양을 만듦
box = (34, 215, 368, 549); c = L23.crop(box); a = np.asarray(c).copy(); x0, y0 = box[:2]
ai = a.astype(int); dark = ~((ai[..., 1] > 200) & (ai[..., 0] < 140))
dark[:240 - y0] = False                                   # 스티커가 걸친 윗부분은 판정에서 제외
flip_mask = superellipse_mask(dark[::-1].copy())          # 아래 → 위로 뒤집어 '윗변' 곡선 측정
mask = flip_mask.transpose(Image.FLIP_TOP_BOTTOM)
a[: 256 - y0, 110 - x0: 300 - x0] = (14, 14, 14)          # 스티커 아래는 카드 검정으로 (기둥은 256부터)
out = Image.fromarray(a).convert('RGBA'); out.putalpha(mask); out.save(f'{O}/f_card.png')

# Lucky Place 버튼: '가는 길 찾아보기'
feather(L25.crop((14, 774, 388, 848)), 4).save(f'{O}/d_place_btn.png')

# 친구방: 헤더·내비는 고정, 그 사이 내용은 한 장의 긴 스크롤 이미지 (두 시안은 정확히 178px 차이)
OFF = 178
feather(L26.crop((0, 0, 402, 104)), 0 or 1).save(f'{O}/fr_head.png')
L26.crop((0, 780, 402, 874)).save(f'{O}/fr_nav.png')
strip = Image.new('RGB', (402, 958 - 104), (14, 14, 14))
strip.paste(L26.crop((0, 104, 402, 780)), (0, 0))
strip.paste(L27.crop((0, 780 - OFF, 402, 780)), (0, 780 - 104))
strip.save(f'{O}/fr_strip.jpg', quality=92)

# ═════════ 친구방 가로 스크롤 · 행운 공구방 채팅 · 운세 순위 비교 ═════════
L28, L29, L30, L31, L32 = L(28), L(29), L(30), L(31), L(32)
# Lucky Moments 줄: 세 시안을 이어 붙인 가로 띠 (이동량 342px, 138px)
ROW = (488, 762); D1, D2 = 342, 138
wide = Image.new('RGB', (402 + D1 + D2, ROW[1] - ROW[0]), (14, 14, 14))
wide.paste(L29.crop((0, ROW[0], 402, ROW[1])), (D1 + D2, 0))
wide.paste(L28.crop((0, ROW[0], 402, ROW[1])), (D1, 0))
wide.paste(L27.crop((0, ROW[0], 402, ROW[1])), (0, 0))
wide.save(f'{O}/fr_row.jpg', quality=92)

# 채팅
L30.crop((0, 0, 402, 178)).save(f'{O}/ch_head.png')            # 칩 기본 상태
L32.crop((0, 0, 402, 300)).save(f'{O}/ch_panel.png')           # 칩 선택 + 순위 바
L30.crop((0, 187, 402, 768)).save(f'{O}/ch_msgs.jpg', quality=92)
L30.crop((0, 760, 402, 874)).save(f'{O}/ch_input.png')
# 운세 순위 비교_딤
L31.save(f'{O}/rk_dim.jpg', quality=92)
for name, box in {'rk_title': (80, 160, 322, 240), 'rk_group': (96, 268, 312, 700),
                  'rk_gem': (34, 130, 98, 190), 'rk_fire': (232, 70, 296, 134), 'rk_leaf2': (306, 300, 366, 370)}.items():
    feather(L31.crop(box), 5).save(f'{O}/{name}.png')

# ═════════ 딤 화면 요소 분리 (배경 = 채팅을 흐리고 어둡게 한 것 → 차이로 요소만 추출) ═════════
L33 = Image.open(f'{SRC}/33.webp').convert('RGB')
L34, L35, L36, L37 = L(34), L(35), L(36), L(37)
R874 = lambda im: im.resize((402, 874))
def synth(src, blur, alpha, color):
    b = np.asarray(R874(src).filter(ImageFilter.GaussianBlur(blur))).astype(float)
    return b * (1 - alpha) + np.array(color) * alpha
def keyed(img, bg, box, thr=10, soft=34):
    """디자인 화면에서 배경(재현한 딤)과 다른 부분만 남긴 투명 PNG"""
    x0, y0, x1, y1 = box
    a = np.asarray(R874(img)).astype(float)[y0:y1, x0:x1]; g = bg[y0:y1, x0:x1]
    al = np.clip((np.abs(a - g).max(2) - thr) / soft, 0, 1)
    al = np.asarray(Image.fromarray((al * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(.4))).astype(float) / 255
    col = np.clip((a - (1 - al[..., None]) * g) / np.maximum(al[..., None], 1e-3), 0, 255)
    return Image.fromarray(np.dstack([col, al * 255]).astype(np.uint8), 'RGBA')

# 운세 순위 비교_딤: 거의 불투명한 회색(43) — 흐림 30px
bgR = synth(L30, 30, .97, (43, 43, 43))
for name, box in {'rk_title': (80, 160, 322, 240), 'rk_card': (108, 270, 306, 545), 'rk_name': (150, 545, 255, 580),
                  'rk_ranks': (105, 590, 300, 695), 'rk_gem': (34, 130, 98, 190), 'rk_fire': (232, 70, 296, 134),
                  'rk_leaf2': (306, 300, 366, 370), 'rk_ok': (16, 780, 200, 846), 'rk_gift': (202, 780, 386, 846)}.items():
    keyed(L31, bgR, box).save(f'{O}/{name}.png')

# 운세 겹쳐보기_딤1·2: 흐림 8px + 어두운 막 91%
bgM = synth(L34, 8, .91, (21, 22, 22))
keyed(L35, bgM, (96, 145, 310, 220)).save(f'{O}/mx_title.png')
keyed(L35, bgM, (70, 225, 332, 270)).save(f'{O}/mx_sub.png')
keyed(L36, bgM, (90, 730, 315, 770)).save(f'{O}/mx_caption.png')
keyed(L36, bgM, (16, 780, 200, 846)).save(f'{O}/mx_ok.png')
keyed(L36, bgM, (202, 780, 386, 846)).save(f'{O}/mx_share.png')
CARDS_MX = {'mx_picnic': (36, 92, 232, 336), 'mx_playlist': (196, 298, 380, 528), 'mx_shirt': (36, 452, 246, 698)}
for name, box in CARDS_MX.items():
    im = keyed(L36, bgM, box, thr=14); im.save(f'{O}/{name}.png')
    a = np.asarray(im)[..., 3].astype(float) / 255; yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    w = a / a.sum(); cx, cy = (w * xx).sum() + box[0], (w * yy).sum() + box[1]
    mu20 = (w * (xx - cx + box[0]) ** 2).sum(); mu02 = (w * (yy - cy + box[1]) ** 2).sum(); mu11 = (w * (xx - cx + box[0]) * (yy - cy + box[1])).sum()
    ang = 0.5 * np.degrees(np.arctan2(2 * mu11, mu20 - mu02))
    print(name, 'center', round(cx, 1), round(cy, 1), 'area', round(a.sum()), 'axis', round(ang, 1))
# 겹쳐보기 딤1의 앞 카드(피크닉) 크기 비교용
a35 = np.abs(np.asarray(L35).astype(float)[455:672, 115:278] - bgM[455:672, 115:278]).max(2) > 30
print('dim1 picnic area', a35.sum())

# 오행 이모지 (흰 배경에서 분리)
ar = np.asarray(L33).astype(int)
for name, (x0, x1) in {'el_earth': (100, 300), 'el_wood': (520, 670), 'el_fire': (880, 1040), 'el_metal': (1270, 1460), 'el_water': (1680, 1850)}.items():
    crop = L33.crop((x0, 100, x1, 275)); ca = np.asarray(crop).astype(int)
    out = key_out_background(crop, ca.min(2) > 235)
    bb = out.getchannel('A').getbbox(); out.crop(bb).resize(((bb[2]-bb[0]) // 3, (bb[3]-bb[1]) // 3), Image.LANCZOS).save(f'{O}/{name}.png')

# 겹쳐보기 채팅: 대화 B(img34) + 새로 보낼 메시지들(img37)
L34.crop((0, 195, 402, 672)).save(f'{O}/ch_msgs2.jpg', quality=92)
for name, box in {'nm_1': (168, 674, 388, 720), 'nm_place': (108, 722, 390, 870), 'nm_3': (172, 870, 388, 918),
                  'nm_4': (12, 942, 292, 1012), 'nm_5': (12, 1012, 222, 1080), 'nm_6': (60, 1080, 242, 1128)}.items():
    feather(L37.crop(box), 3).save(f'{O}/{name}.png')
# 공유용 Lucky Place 화면 버튼 ('채팅방에 공유하기')
feather(L9.crop((14, 774, 388, 848)), 4).save(f'{O}/d_place_share.png')

# ═════════ 수정: 딤은 정적 배경 이미지로 (사파리에서 backdrop-filter 위 요소가 검은 상자로 보이던 문제) ═════════
Image.fromarray(np.clip(bgM, 0, 255).astype(np.uint8)).save(f'{O}/mx_bg.jpg', quality=92)
# 오행 이모지: 투명 가장자리가 어두워지지 않도록 미리곱한 알파로 축소
for name, (x0, x1) in {'el_earth': (100, 300), 'el_wood': (520, 670), 'el_fire': (880, 1040), 'el_metal': (1270, 1460), 'el_water': (1680, 1850)}.items():
    crop = L33.crop((x0, 100, x1, 275)); ca = np.asarray(crop).astype(int)
    out = key_out_background(crop, ca.min(2) > 235); bb = out.getchannel('A').getbbox()
    out.crop(bb).save(f'{O}/{name}.png')   # 원본(약 5배) 해상도 유지
# 운세 겹쳐보기_오늘의 행운 장소 연결 (Mapo River)
L38 = L(38)
for name, box in {'mp_head': (0, 0, 402, 112), 'mp_hero': (18, 110, 384, 480), 'mp_body': (28, 482, 374, 538),
                  'mp_icons': (18, 606, 384, 742), 'mp_ok': (14, 776, 202, 848), 'mp_share': (202, 776, 388, 848),
                  'mp_bar': (120, 848, 282, 872)}.items():
    feather(L38.crop(box), 4).save(f'{O}/{name}.png')


# ═════════ 순위 딤: 이모지를 뺀 배경 + 이모지 4개 따로 / 겹쳐보기 카드를 온전한 모양으로 ═════════
def fill_holes(m):
    """테두리에서 닿지 않는 빈 곳(카드 안의 어두운 부분)을 채움"""
    h, w = m.shape; outside = np.zeros_like(m); stack = [(0, x) for x in range(w)] + [(h-1, x) for x in range(w)] + [(y, 0) for y in range(h)] + [(y, w-1) for y in range(h)]
    while stack:
        y, x = stack.pop()
        if 0 <= y < h and 0 <= x < w and not outside[y, x] and not m[y, x]:
            outside[y, x] = True; stack += [(y+1, x), (y-1, x), (y, x+1), (y, x-1)]
    return ~outside
def solid_piece(img, bg, box, thr=12):
    """요소의 가장 큰 덩어리 + 내부 구멍 메움 → 다른 카드 조각·투명 구멍 없이 온전한 모양"""
    x0, y0, x1, y1 = box
    a = np.asarray(R874(img)).astype(float)[y0:y1, x0:x1]; g = bg[y0:y1, x0:x1]
    m = np.abs(a - g).max(2) > thr
    m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))) > 0
    keep = largest_component((m * 255).astype(np.uint8), 128) > 128
    keep = fill_holes(keep)
    al = np.asarray(Image.fromarray((keep * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(.7))).astype(float) / 255
    edge = (al > 0) & (al < 1)
    col = a.copy(); col[edge] = np.clip((a[edge] - (1 - al[edge, None]) * g[edge]) / np.maximum(al[edge, None], .25), 0, 255)
    return Image.fromarray(np.dstack([col, al * 255]).astype(np.uint8), 'RGBA')

def harmonic_fill(img, mask, iters=600):
    """마스크 영역을 주변 픽셀에서 매끄럽게 이어 채움 (흐린 배경용)"""
    out = img.copy(); out[mask] = out[~mask].mean(0)
    for _ in range(iters):
        avg = (np.roll(out, 1, 0) + np.roll(out, -1, 0) + np.roll(out, 1, 1) + np.roll(out, -1, 1)) / 4
        out[mask] = avg[mask]
    return out
def hull(pts):
    pts = sorted(set(map(tuple, pts)))
    def cross(o, a, b): return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return np.array(lo[:-1] + up[:-1], float)
def card_piece(img, bg, box, radius=.24):
    """카드 = 회전된 둥근 사각형. 밝거나 색이 있는 픽셀의 외곽(볼록 껍질)에 맞춰 모양을 정확히 만듦"""
    x0, y0, x1, y1 = box
    a = np.asarray(R874(img)).astype(float)[y0:y1, x0:x1]; g = bg[y0:y1, x0:x1]
    sat = a.max(2) - a.min(2)
    m = ((a.mean(2) - g.mean(2)) > 28) | (sat > 70)
    m = largest_component((m * 255).astype(np.uint8), 128) > 128
    ys, xs = np.nonzero(m); P = hull(np.c_[xs, ys])
    best = None
    for k in range(len(P)):
        e = P[(k+1) % len(P)] - P[k]; th = np.arctan2(e[1], e[0])
        R = np.array([[np.cos(th), np.sin(th)], [-np.sin(th), np.cos(th)]]); Q = P @ R.T
        lo, hi = Q.min(0), Q.max(0); area = np.prod(hi - lo)
        if best is None or area < best[0]: best = (area, th, lo, hi)
    _, th, lo, hi = best
    S = 4; H, W = a.shape[:2]
    yy, xx = np.mgrid[0:H*S, 0:W*S] / S
    R = np.array([[np.cos(th), np.sin(th)], [-np.sin(th), np.cos(th)]])
    u = xx * R[0, 0] + yy * R[0, 1]; v = xx * R[1, 0] + yy * R[1, 1]
    c = (lo + hi) / 2; hw = (hi - lo) / 2 + .5; r = radius * min(hw) * 2
    dx = np.maximum(np.abs(u - c[0]) - (hw[0] - r), 0); dy = np.maximum(np.abs(v - c[1]) - (hw[1] - r), 0)
    inside = (np.hypot(dx, dy) <= r) & (np.abs(u - c[0]) <= hw[0]) & (np.abs(v - c[1]) <= hw[1])
    al = np.asarray(Image.fromarray((inside * 255).astype(np.uint8)).resize((W, H), Image.LANCZOS)).astype(float) / 255
    return Image.fromarray(np.dstack([a, al * 255]).astype(np.uint8), 'RGBA')
def sticker_piece(img, bg, box, thr=18):
    x0, y0, x1, y1 = box
    a = np.asarray(R874(img)).astype(float)[y0:y1, x0:x1]; g = bg[y0:y1, x0:x1]
    m = np.abs(a - g).max(2) > thr
    keep = largest_component((m * 255).astype(np.uint8), 128) > 128
    keep = fill_holes(keep)
    al = np.asarray(Image.fromarray((keep * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(.5))).astype(float) / 255
    return Image.fromarray(np.dstack([a, al * 255]).astype(np.uint8), 'RGBA')

A31 = np.asarray(R874(L31)).astype(float)
STK = {'rk_fire': (229, 66, 292, 136), 'rk_gem': (30, 129, 99, 193), 'rk_leaf1': (256, 271, 310, 335), 'rk_leaf2': (304, 300, 368, 374)}
clean = A31.copy(); M = A31[:, ::-1]                       # 좌우 대칭 화면 (카드도 대칭)
cardM = (M.min(2) > 150)                                   # 반대편이 카드인 픽셀
for (x0, y0, x1, y1) in STK.values():
    p = 8; X0, Y0, X1, Y1 = x0 - p, y0 - p, x1 + p, y1 + p   # 스티커 그림자까지 넉넉히
    A = clean[Y0:Y1, X0:X1].copy(); Mm = M[Y0:Y1, X0:X1]; cm = cardM[Y0:Y1, X0:X1]
    hole = np.zeros(A.shape[:2], bool); hole[3:-3, 3:-3] = True
    known = ~hole | cm                                     # 테두리 + 카드 픽셀은 값이 정해져 있음
    out = A.copy(); out[cm & hole] = Mm[cm & hole]
    bgok = ~cm                                             # 카드 흰색이 배경 쪽으로 번지지 않게 배경 이웃만 평균
    out[hole & ~cm] = A[~hole & bgok].mean(0)
    for _ in range(3000):
        acc = np.zeros_like(out); cnt = np.zeros(out.shape[:2])
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            v = np.roll(np.roll(out, dy, 0), dx, 1); ok = np.roll(np.roll(bgok, dy, 0), dx, 1)
            acc += v * ok[..., None]; cnt += ok
        upd = hole & ~cm & (cnt > 0)
        out[upd] = (acc[upd] / cnt[upd, None])
    clean[Y0:Y1, X0:X1] = out
    region = clean[Y0 - 6:Y1 + 6, X0 - 6:X1 + 6]; notcard = region.min(2) < 150   # 배경은 무채색 → 남은 초록 기운 제거
    region[notcard] = region[notcard].mean(1, keepdims=True)
Image.fromarray(clean.astype(np.uint8)).save(f'{O}/rk_bg.jpg', quality=93)
for name, box in STK.items(): sticker_piece(L31, clean, box, thr=32).save(f'{O}/{name}.png')
for name, box in CARDS_MX.items(): card_piece(L36, bgM, box).save(f'{O}/{name}.png')
keyed(L35, bgM, (96, 145, 310, 220), thr=30, soft=40).save(f'{O}/mx_title.png')
keyed(L35, bgM, (70, 225, 332, 270), thr=30, soft=40).save(f'{O}/mx_sub.png')
keyed(L36, bgM, (90, 730, 315, 770), thr=30, soft=40).save(f'{O}/mx_caption.png')

# ═════════ 홈 스크롤 (홈_기본_하단 스크롤: 카드 132px, 제목·설명 53px 이동) ═════════
L44 = L(44)
L15.crop((0, 0, 402, 104)).save(f'{O}/home_head.png')
L15.crop((0, 104, 402, 164)).save(f'{O}/home_hello.png')        # '오늘은' — 스크롤하면 사라짐
L15.crop((0, 164, 402, 266)).save(f'{O}/home_title.png')        # 木의 기운 + 설명
L44.crop((0, 780, 402, 874)).save(f'{O}/home_nav.png')
mus = L44.crop((14, 596, 388, 772))                                # 다 보이는 Lucky Music 카드
feather(mus, 3).save(f'{O}/music_off.png'); feather(to_selected_safe(mus), 3).save(f'{O}/music_on.png')

# ═════════ 운세 카드: 시안 윤곽을 4배 정밀도로 측정해 매끄러운 3배 해상도 카드로 다시 그림 ═════════
# (이전엔 자르기 상자가 y=215에서 시작해 카드 윗변(y≈210)이 평평하게 잘렸음)
A47 = np.asarray(L(47).resize((402 * 4, 874 * 4), Image.LANCZOS)).astype(int)
mint47 = (A47[..., 1] > 200) & (A47[..., 0] < 160)
CX, CY = 200.85, 377.9                       # 카드 중심 (위아래·좌우 대칭)
prof = {}                                    # 아래쪽 가장자리에서의 거리(d) → 좌우 반폭
for yy in range(int(CY * 4), 560 * 4):
    xs = np.nonzero(~mint47[yy, 20 * 4:385 * 4])[0]
    if len(xs): prof[yy / 4] = ((xs.max() - xs.min()) / 4) / 2
BOTTOM = max(prof); ds = np.array(sorted(BOTTOM - y for y in prof)); hws = np.array([prof[BOTTOM - d] for d in ds])
hws = np.maximum.accumulate(hws)             # 단조 증가로 정리 (잡음 제거)
TOP = 2 * CY - BOTTOM; HW = hws.max()
print('fortune card', round(TOP, 2), round(BOTTOM, 2), 'half-width', HW)
BOX = (34, 206, 368, 551); K = 3
W3, H3 = (BOX[2] - BOX[0]) * K, (BOX[3] - BOX[1]) * K
SS = 4; yy, xx = np.mgrid[0:H3 * SS, 0:W3 * SS]
py = BOX[1] + (yy + .5) / (K * SS); px = BOX[0] + (xx + .5) / (K * SS)
d = np.minimum(py - TOP, BOTTOM - py)
hw = np.interp(d, ds, hws, left=-1, right=HW)
inside = (d >= 0) & (np.abs(px - CX) <= hw)
alpha = Image.fromarray((inside * 255).astype(np.uint8)).resize((W3, H3), Image.LANCZOS)
col = np.asarray(L23.crop(BOX)).copy(); x0, y0 = BOX[:2]
col[: 257 - y0, 110 - x0: 300 - x0] = (14, 14, 14)                 # 스티커 아래(가려진 곳)는 카드 검정
col[: 250 - y0] = 14                                               # 기둥(y≈257) 위쪽은 모두 카드 검정 → 윗변 잡티 제거
big = Image.fromarray(col).resize((W3, H3), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=2.4, percent=70, threshold=1))
big.putalpha(alpha); big.save(f'{O}/f_card.png')

# ═════════ 채팅 고화질: 사진류만 이미지로 (텍스트·말풍선·버튼은 HTML로 다시 그림) ═════════
def circle_crop(img, cx, cy, r, name):
    c = img.crop((cx - r, cy - r, cx + r, cy + r)).convert('RGBA'); S4 = 4
    yy, xx = np.mgrid[0:2*r*S4, 0:2*r*S4]; m = (np.hypot(yy - r*S4 + .5, xx - r*S4 + .5) <= r*S4 - 1).astype(np.uint8) * 255
    c.putalpha(Image.fromarray(m).resize((2*r, 2*r), Image.LANCZOS)); c.save(f'{O}/{name}.png')
circle_crop(L30, 40, 244, 21, 'av_dayun'); circle_crop(L30, 40, 490, 21, 'av_sumin')
# 순위 바 아바타 (둥근 모양 + 숫자 배지 포함, 이미지 그대로)
for name, box in {'rk_av1': (24, 198, 92, 262), 'rk_av2': (104, 198, 172, 262), 'rk_av3': (184, 198, 252, 262)}.items():
    feather(L32.crop(box), 3).save(f'{O}/{name}.png')
L37.crop((122, 735, 244, 860)).save(f'{O}/ch_place_photo.jpg', quality=93)   # 장소 카드 사진
feather(L37.crop((82, 568, 194, 605)), 2).save(f'{O}/ch_mix_logo.png')        # Lucky mix 로고
# 순위 아바타: 원형(지름 62) + 숫자 배지는 HTML로 다시 그림
# 순위 아바타: 시안 그대로(숫자 배지 포함), 윤곽 = 아바타 원 ∪ 배지 원 → 배지가 잘리지 않음
for name, (cx, cy, bx) in {'rk_av1': (58, 231, 72.1), 'rk_av2': (137, 231, 152.4), 'rk_av3': (217, 231, 233.1)}.items():
    r = 31; K = 4; c = L32.crop((cx - r, cy - r, cx + r, cy + r)).convert('RGBA')
    yy, xx = (np.mgrid[0:2*r*K, 0:2*r*K] + .5) / K
    m = (np.hypot(yy - r, xx - r) <= r - .3) | (np.hypot(yy - (238.4 - cy + r), xx - (bx - cx + r)) <= 16.4)
    c.putalpha(Image.fromarray((m * 255).astype(np.uint8)).resize((2*r, 2*r), Image.LANCZOS)); c.save(f'{O}/{name}.png')
L37.crop((121, 735, 245, 859)).save(f'{O}/ch_place_photo.jpg', quality=93)

# ═════════ 피드백 반영 ═════════
L58 = L(58)
# 운세 순위 비교_딤_0: 제목만 크게 → 위로 올라가며 딤_1로
A58 = np.asarray(R874(L58)).astype(float)
TB = (40, 340, 362, 432)
hole = np.zeros(A58.shape[:2], bool); hole[TB[1]:TB[3], TB[0]:TB[2]] = True
bg0 = harmonic_fill(A58, hole, iters=1500)
Image.fromarray(bg0.clip(0, 255).astype(np.uint8)).save(f'{O}/rk_bg0.jpg', quality=93)
keyed(L58, bg0, TB, thr=22, soft=40).save(f'{O}/rk_title0.png')

# 오늘의운세_딤1: 흐린 카드는 파이썬에서 미리 흐리게 + 은색 기둥이 희끗하게 번지지 않도록 민트로 물들임
mf = np.asarray(Image.open(f'{O}/modal_fill.jpg').convert('RGB')).astype(float)
pad = 40; big = np.pad(mf, ((pad, pad), (pad, pad), (0, 0)), mode='edge')
bl = np.asarray(Image.fromarray(big.astype(np.uint8)).filter(ImageFilter.GaussianBlur(17))).astype(float)[pad:-pad, pad:-pad]
mint = np.array([0, 255, 195], float); lum = bl.mean(2, keepdims=True)
gray = (bl.max(2, keepdims=True) - bl.min(2, keepdims=True)) < 60          # 무채색(은색) 부분
bl = np.where(gray, bl * .45 + mint * .55, bl * .8 + mint * .2)
Image.fromarray(bl.clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(4)).save(f'{O}/modal_blur.jpg', quality=92)

# 카메라 뷰파인더: 4배 정밀도로 윤곽 측정 → 위아래 대칭의 매끄러운 곡선으로 3배 해상도 마스크
A16 = np.asarray(L16.resize((402 * 4, 874 * 4), Image.LANCZOS)).astype(int)
ins16 = np.abs(A16 - 14).max(2) > 12
vb = (18, 203, 384, 651); prof16 = {}
for yy in range(vb[1] * 4, vb[3] * 4):
    xs = np.nonzero(ins16[yy, vb[0] * 4:vb[2] * 4])[0]
    if len(xs) > 40: prof16[yy / 4] = (xs.min() / 4 + vb[0], xs.max() / 4 + vb[0])
ys = sorted(prof16); TOPv, BOTv = ys[0], ys[-1] + .25
L_ = min(v[0] for v in prof16.values()); R_ = max(v[1] for v in prof16.values()); CXv = (L_ + R_ + .25) / 2; HWv = (R_ - L_ + .25) / 2
ds = []; hws = []
for y in ys:
    d = min(y - TOPv, BOTv - y)
    if d < 80: ds.append(d); hws.append((prof16[y][1] - prof16[y][0] + .25) / 2)
order = np.argsort(ds); ds = np.array(ds)[order]; hws = np.maximum.accumulate(np.array(hws)[order])
# 같은 d의 값들을 평균해 잡음 제거
ud = np.unique(np.round(ds * 4) / 4); uh = np.array([hws[np.abs(ds - u) < .2].mean() for u in ud]); uh = np.maximum.accumulate(uh)
print('viewfinder', TOPv, BOTv, CXv, HWv)
K = 3; W3, H3 = (vb[2] - vb[0]) * K, (vb[3] - vb[1]) * K; SS = 4
yy, xx = np.mgrid[0:H3 * SS, 0:W3 * SS]
py = vb[1] + (yy + .5) / (K * SS); px = vb[0] + (xx + .5) / (K * SS)
d = np.minimum(py - TOPv, BOTv - py); hw = np.interp(d, ud, uh, left=-1, right=HWv)
inside = (d >= 0) & (np.abs(px - CXv) <= hw)
al = Image.fromarray((inside * 255).astype(np.uint8)).resize((W3, H3), Image.LANCZOS)
mk = Image.new('RGBA', (W3, H3), (0, 0, 0, 0)); mk.putalpha(al); mk.save(f'{O}/cam_mask.png')

# ═════════ 새 오늘의운세_딤1/딤2 (시안 62·63) ═════════
L62, L63 = L(62), L(63)
A62 = np.asarray(L62).astype(float); A63 = np.asarray(L63).astype(float)
Image.fromarray(A62.astype(np.uint8)).save(f'{O}/dim1_full.jpg', quality=95)
# 딤2에서 X·보러가기를 뺀 배경: X는 카드의 좌우 대칭 반대편, 버튼은 딤1 배경으로
diff = np.abs(A62 - A63).max(2) > 12
CXm = (61.75 + 351.0) / 2
cleanB = A63.copy()
XB = (316, 214, 362, 264)
for y in range(XB[1], XB[3]):
    for x in range(XB[0], XB[2]):
        mx = int(round(2 * CXm - x)); src = A63[y, mx]
        cleanB[y, x] = src if (src[1] > 200 and src[0] < 150) else A62[y, x]   # 카드 안쪽만 대칭 복사, 바깥은 딤1 배경
BB = (120, 600, 284, 672); cleanB[BB[1]:BB[3], BB[0]:BB[2]] = A62[BB[1]:BB[3], BB[0]:BB[2]]
Image.fromarray(cleanB.astype(np.uint8)).save(f'{O}/dim2_clean.jpg', quality=95)
xi = np.asarray(keyed(L63, cleanB, XB, thr=14, soft=30)).copy(); xi[..., 3] = largest_component(xi[..., 3], 60)
Image.fromarray(xi, 'RGBA').save(f'{O}/dim_x.png')
keyed(L63, cleanB, BB, thr=14, soft=30).save(f'{O}/dim_btn.png')
# 운세 화면으로 이어지는 카드(모프 시작): 왼쪽 윤곽을 4배로 재고 좌우·상하 대칭으로 매끄럽게
A63x4 = np.asarray(L63.resize((402 * 4, 874 * 4), Image.LANCZOS)).astype(int)
mint63 = (A63x4[..., 1] > 200) & (A63x4[..., 0] < 150) & (A63x4[..., 2] > 140)
TOPm, BOTm = 229.25, 574.5
left = {}
for yy in range(int(TOPm * 4), int(BOTm * 4)):
    xs = np.nonzero(mint63[yy, 40 * 4:210 * 4])[0]
    if len(xs): left[yy / 4] = xs.min() / 4 + 40
dsm = np.array([min(y - TOPm, BOTm - y) for y in left]); hwm = np.array([CXm - v for v in left.values()])
o = np.argsort(dsm); dsm = dsm[o]; hwm = np.maximum.accumulate(hwm[o]); HWm = hwm.max()
MB = (60, 228, 353, 576); K = 3; W3, H3 = (MB[2] - MB[0]) * K, (MB[3] - MB[1]) * K; SS = 4
yy, xx = np.mgrid[0:H3 * SS, 0:W3 * SS]; py = MB[1] + (yy + .5) / (K * SS); px = MB[0] + (xx + .5) / (K * SS)
d = np.minimum(py - TOPm, BOTm - py); hw = np.interp(d, dsm, hwm, left=-1, right=HWm)
alm = Image.fromarray((((d >= 0) & (np.abs(px - CXm) <= hw)) * 255).astype(np.uint8)).resize((W3, H3), Image.LANCZOS)
cardc = Image.fromarray(cleanB[MB[1]:MB[3], MB[0]:MB[2]].astype(np.uint8)).resize((W3, H3), Image.LANCZOS)
cardc.putalpha(alm); cardc.save(f'{O}/modal_card.png')
print('modal', MB, 'hw', HWm)

# 카메라: 원래 시안의 뷰파인더 사진을 배경에서 지움 → 매끄러운 마스크 밖으로 옛 사진 모서리가 삐져나오지 않음
cb = np.asarray(L16).copy(); cb[203:651, 18:384] = 14
Image.fromarray(cb).save(f'{O}/cam_base.jpg', quality=92)
# 뷰파인더 사진: 원래 둥근 모서리 바깥(검정)을 사진 가장자리 색으로 채움 → 새 마스크 경계에 검은 틈이 안 생김
ph = np.asarray(Image.open(f'{O}/cam_photo.jpg').convert('RGB')).astype(float)
dark = np.abs(ph - 14).max(2) <= 14
ins = fill_holes(~dark)                                     # 가장자리에서 이어진 어두운 영역만 '사진 밖'
ins = np.asarray(Image.fromarray((ins * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(5))) > 0   # 경계의 어두운 테두리도 제외
filled = ph.copy(); known = ins.copy()
for _ in range(60):
    if known.all(): break
    acc = np.zeros_like(filled); cnt = np.zeros(known.shape)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        acc += np.roll(np.roll(filled * known[..., None], dy, 0), dx, 1); cnt += np.roll(np.roll(known, dy, 0), dx, 1)
    grow = ~known & (cnt > 0); filled[grow] = acc[grow] / cnt[grow, None]; known |= grow
Image.fromarray(filled.clip(0, 255).astype(np.uint8)).save(f'{O}/cam_photo.jpg', quality=93)

# ═════════ 도형 윤곽을 수식(슈퍼타원)으로 맞춰 완전히 매끄럽게 + 딤1·딤2 같은 윤곽 ═════════
def fit_superellipse(ds, hws, A, B):
    """반폭 프로필(가장자리에서 거리 d → 반폭)에 맞는 모서리 곡선 지수 n을 찾음. |x/A|^n + |y/B|^n = 1"""
    best = None
    for n in np.arange(2.0, 8.01, .05):
        y = B - ds; pred = A * np.clip(1 - np.abs(y / B) ** n, 0, 1) ** (1 / n)
        err = np.mean((pred - hws) ** 2)
        if best is None or err < best[0]: best = (err, n)
    return best
def shape_alpha(box, CX, CY, A, B, n, K=3, SS=4):
    W3, H3 = (box[2] - box[0]) * K, (box[3] - box[1]) * K
    yy, xx = np.mgrid[0:H3 * SS, 0:W3 * SS]
    py = box[1] + (yy + .5) / (K * SS); px = box[0] + (xx + .5) / (K * SS)
    inside = (np.abs((px - CX) / A) ** n + np.abs((py - CY) / B) ** n) <= 1
    return np.asarray(Image.fromarray((inside * 255).astype(np.uint8)).resize((W3, H3), Image.LANCZOS)).astype(float) / 255

# 카드 (딤2 기준): 왼쪽 윤곽 프로필로 지수 맞추기
Am, Bm = (351.0 - 61.75) / 2, (BOTm - TOPm) / 2; CYm = (TOPm + BOTm) / 2
errm, nm = fit_superellipse(dsm, hwm, Am, Bm)
print('card superellipse n', round(nm, 2), 'rmse', round(errm ** .5, 2))
K = 3; FULL = (0, 0, 402, 874)
am = shape_alpha(FULL, CXm, CYm, Am, Bm, nm)                 # 3배 전체 화면 크기 마스크
up = lambda arr: np.asarray(Image.fromarray(arr.clip(0, 255).astype(np.uint8)).resize((402 * K, 874 * K), Image.LANCZOS)).astype(float)
def edge_extend(img, known, iters=12):
    f = img.copy(); kn = known.copy()
    for _ in range(iters):
        acc = np.zeros_like(f); cnt = np.zeros(kn.shape)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            acc += np.roll(np.roll(f * kn[..., None], dy, 0), dx, 1); cnt += np.roll(np.roll(kn, dy, 0), dx, 1)
        g = ~kn & (cnt > 0); f[g] = acc[g] / cnt[g, None]; kn |= g
    return f
# 1배 좌표의 카드 안쪽(조금 안으로) 영역
yy1, xx1 = np.mgrid[0:874, 0:402]
inner = (np.abs((xx1 + .5 - CXm) / (Am - 3)) ** nm + np.abs((yy1 + .5 - CYm) / (Bm - 3)) ** nm) <= 1
outer = (np.abs((xx1 + .5 - CXm) / (Am + 4)) ** nm + np.abs((yy1 + .5 - CYm) / (Bm + 4)) ** nm) <= 1
# 배경: 카드 주변 띠는 바깥 배경에서 매끄럽게 채움 (원래 카드의 민트 가장자리 제거)
bgc = harmonic_fill(cleanB.copy(), outer, iters=900)
sharp = edge_extend(cleanB, inner)                           # 선명한 카드 내용
sh = np.roll(A62, 5, axis=1)                                 # 흐린 카드: 5px 오른쪽으로 옮겨 딤2와 정렬
blur = edge_extend(sh, inner)
bg3, sh3, bl3, a3 = up(bgc), up(sharp), up(blur), am[..., None]
Image.fromarray((bg3 * (1 - a3) + bl3 * a3).clip(0, 255).astype(np.uint8)).save(f'{O}/dim1_full.jpg', quality=93)
Image.fromarray((bg3 * (1 - a3) + sh3 * a3).clip(0, 255).astype(np.uint8)).save(f'{O}/dim2_clean.jpg', quality=93)
# 운세 화면으로 이어지는 카드도 같은 윤곽
MB = (60, 228, 353, 576)
cardc = Image.fromarray(sh3[MB[1] * K:MB[3] * K, MB[0] * K:MB[2] * K].clip(0, 255).astype(np.uint8))
cardc.putalpha(Image.fromarray((am[MB[1] * K:MB[3] * K, MB[0] * K:MB[2] * K] * 255).astype(np.uint8))); cardc.save(f'{O}/modal_card.png')

# 카메라 뷰파인더도 수식 곡선으로
# 왼쪽은 사진 속 어두운 물체 때문에 윤곽이 흔들림 → 깨끗한 오른쪽 윤곽만으로 측정 (좌우 대칭)
rd, rh = [], []
for y, (l, r) in prof16.items():
    d = min(y - TOPv, BOTv - y)
    if d < 95: rd.append(d); rh.append(r + .25 - CXv)
o = np.argsort(rd); ud = np.array(rd)[o]; uh = np.maximum.accumulate(np.array(rh)[o])
Av, Bv = uh.max(), (BOTv - TOPv) / 2; CYv = (TOPv + BOTv) / 2
errv, nv = fit_superellipse(ud, uh, Av, Bv)
print('viewfinder superellipse n', round(nv, 2), 'rmse', round(errv ** .5, 2))
av = shape_alpha(vb, CXv, CYv, Av, Bv, nv)
mk = Image.new('RGBA', (av.shape[1], av.shape[0]), (0, 0, 0, 0)); mk.putalpha(Image.fromarray((av * 255).astype(np.uint8))); mk.save(f'{O}/cam_mask.png')

# 더 정확한 모델: 직선 변 + 모서리만 둥근 사각형 (모서리 반경 R, 곡률 지수 n)
def fit_rrect(ds, hws, A):
    best = None
    for R in np.arange(30, min(A, 200), 1.0):
        for n in np.arange(2.0, 5.01, .1):
            t = np.clip((R - ds) / R, 0, 1)
            pred = (A - R) + R * np.clip(1 - t ** n, 0, 1) ** (1 / n)
            err = np.mean((pred - hws) ** 2)
            if best is None or err < best[0]: best = (err, R, n)
    return best
def rrect_alpha(box, CX, CY, A, B, R, n, K=3, SS=4):
    W3, H3 = (box[2] - box[0]) * K, (box[3] - box[1]) * K
    yy, xx = np.mgrid[0:H3 * SS, 0:W3 * SS]
    py = box[1] + (yy + .5) / (K * SS); px = box[0] + (xx + .5) / (K * SS)
    dx = np.maximum(np.abs(px - CX) - (A - R), 0); dy = np.maximum(np.abs(py - CY) - (B - R), 0)
    inside = ((dx / R) ** n + (dy / R) ** n <= 1) & (np.abs(px - CX) <= A) & (np.abs(py - CY) <= B)
    return np.asarray(Image.fromarray((inside * 255).astype(np.uint8)).resize((W3, H3), Image.LANCZOS)).astype(float) / 255

e, Rv, nv2 = fit_rrect(ud, uh, Av); print('viewfinder rrect R', Rv, 'n', round(nv2, 1), 'rmse', round(e ** .5, 2))
av = rrect_alpha(vb, CXv, CYv, Av, Bv, Rv, nv2)
mk = Image.new('RGBA', (av.shape[1], av.shape[0]), (0, 0, 0, 0)); mk.putalpha(Image.fromarray((av * 255).astype(np.uint8))); mk.save(f'{O}/cam_mask.png')

e2, Rm, nm2 = fit_rrect(dsm, hwm, Am); print('card rrect R', Rm, 'n', round(nm2, 1), 'rmse', round(e2 ** .5, 2))
if e2 < errm:   # 카드도 더 잘 맞으면 이 모델로 다시 그림
    am = rrect_alpha(FULL, CXm, CYm, Am, Bm, Rm, nm2); a3 = am[..., None]
    in1 = rrect_alpha(FULL, CXm, CYm, Am, Bm, Rm, nm2, K=1)   # (참고용)
    Image.fromarray((bg3 * (1 - a3) + bl3 * a3).clip(0, 255).astype(np.uint8)).save(f'{O}/dim1_full.jpg', quality=93)
    Image.fromarray((bg3 * (1 - a3) + sh3 * a3).clip(0, 255).astype(np.uint8)).save(f'{O}/dim2_clean.jpg', quality=93)
    cardc = Image.fromarray(sh3[MB[1] * K:MB[3] * K, MB[0] * K:MB[2] * K].clip(0, 255).astype(np.uint8))
    cardc.putalpha(Image.fromarray((am[MB[1] * K:MB[3] * K, MB[0] * K:MB[2] * K] * 255).astype(np.uint8))); cardc.save(f'{O}/modal_card.png')
