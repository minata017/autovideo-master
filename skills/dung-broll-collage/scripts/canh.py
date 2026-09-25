# -*- coding: utf-8 -*-
"""
canh.py - 5 an du hinh cho canh tram B-roll, viet cho HyperFrames (HTML + GSAP).

Moi canh la mot ham: nhan (L = bo cuc theo huong khung, M = bo mau)
-> tra ve (svg_markup, gsap_js).

Chat stop-motion: moi tween dung ease "steps(n)" -> chuyen dong giat nac nhu
chup tung tam giay, khong muot kieu may tinh.

Them canh moi: viet mot ham theo dung khuon, dang ky vao DS_CANH cuoi file,
va them tu khoa vao BANG_CANH trong lam_broll.py.
"""

# ---- chat lieu dung chung: bo loc + hoa tiet giay ----
def defs(M):
    return f"""
<defs>
  <filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch"/>
    <feColorMatrix type="saturate" values="0"/><feComponentTransfer><feFuncA type="linear" slope="0.07"/></feComponentTransfer>
    <feComposite operator="over" in2="SourceGraphic"/></filter>
  <filter id="torn"><feTurbulence type="fractalNoise" baseFrequency="0.018" numOctaves="3" result="n"/>
    <feDisplacementMap in="SourceGraphic" in2="n" scale="16" xChannelSelector="R" yChannelSelector="G"/></filter>
  <filter id="tornS"><feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="2" result="n"/>
    <feDisplacementMap in="SourceGraphic" in2="n" scale="8" xChannelSelector="R" yChannelSelector="G"/></filter>
  <filter id="sh" x="-40%" y="-40%" width="180%" height="180%">
    <feDropShadow dx="0" dy="14" stdDeviation="16" flood-color="#0a2b27" flood-opacity="0.3"/></filter>
  <pattern id="ht" width="12" height="12" patternUnits="userSpaceOnUse">
    <rect width="12" height="12" fill="#2c2a28"/><circle cx="6" cy="6" r="2.7" fill="#615c57"/></pattern>
  <pattern id="htL" width="11" height="11" patternUnits="userSpaceOnUse">
    <rect width="11" height="11" fill="{M['cream']}"/><circle cx="5.5" cy="5.5" r="2" fill="#c9b98e"/></pattern>
  <radialGradient id="vig" cx="50%" cy="40%" r="78%">
    <stop offset="58%" stop-color="#000" stop-opacity="0"/><stop offset="100%" stop-color="#000" stop-opacity="0.24"/></radialGradient>
  <radialGradient id="leak" cx="22%" cy="12%" r="45%">
    <stop offset="0%" stop-color="#ffd98a" stop-opacity="0.16"/><stop offset="100%" stop-color="#ffd98a" stop-opacity="0"/></radialGradient>
</defs>"""


def tam_giay(x, y, w, h, M, id="giay"):
    """Tam giay kem mep rach.
    HAI LOP: lop ngoai giu bong do (GSAP se dong vao lop <g id=...> nay),
    lop trong giu mep rach. Mot the KHONG the vua filter= vua style:filter."""
    return f"""
<g id="{id}" style="filter:url(#sh)">
  <g filter="url(#torn)">
    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{M['creamE']}"/>
    <rect x="{x+14}" y="{y+14}" width="{w-28}" height="{h-28}" rx="4" fill="{M['cream']}"/>
  </g>
</g>"""


def mieng(id, x, y, noi_dung, bong=True):
    """Boc mot mieng giay thanh HAI LOP - LUAT CUNG khi dung GSAP voi SVG:
    lop NGOAI giu vi tri (transform=translate), GSAP khong dung toi;
    lop TRONG mang id de GSAP lam dong. Neu de GSAP dong thang vao the co
    transform san, no GHI DE translate -> moi mieng van khoi cho (da dinh loi nay)."""
    sh = ' style="filter:url(#sh)"' if bong else ""
    return f"""
<g transform="translate({x} {y})"><g id="{id}"{sh} opacity="0">{noi_dung}</g></g>"""


def ban_tay(x, y, M, id="tay"):
    """Ban tay giay dat mieng chot - chu ky cua the loai collage."""
    noi_dung = f"""
  <g transform="rotate(-34)">
    <rect x="26" y="-16" width="120" height="34" rx="17" fill="{M['cream']}" stroke="{M['ink']}" stroke-width="5"/>
    <ellipse cx="196" cy="34" rx="88" ry="66" fill="{M['cream']}" stroke="{M['ink']}" stroke-width="5"/>
    <circle cx="136" cy="42" r="20" fill="{M['cream']}" stroke="{M['ink']}" stroke-width="5"/>
    <circle cx="164" cy="58" r="20" fill="{M['cream']}" stroke="{M['ink']}" stroke-width="5"/>
    <circle cx="196" cy="68" r="20" fill="{M['cream']}" stroke="{M['ink']}" stroke-width="5"/>
    <ellipse cx="150" cy="-24" rx="52" ry="22" fill="{M['cream']}" stroke="{M['ink']}" stroke-width="5" transform="rotate(24 150 -24)"/>
    <g transform="rotate(18 280 70)">
      <rect x="252" y="6" width="120" height="130" rx="8" fill="url(#htL)" stroke="{M['ink']}" stroke-width="5"/>
    </g>
  </g>"""
    return mieng(id, x, y, noi_dung)


# Rung tay giay: nhip giat nho, lap vo han - lam moi mieng "song" nhu stop-motion
def js_rung(sel, bd=0.9, bien=2.0, seed=0):
    return (f'tl.to("{sel}", {{x:"+={bien}", y:"-={bien*0.7}", rotation:"+=0.35", duration:0.26,'
            f' repeat:-1, yoyo:true, ease:"steps(1)"}}, {bd + seed*0.05});')


# ============================================================
# CANH 1 - quay -> dung -> xuat ban
# ============================================================
def quay_cat_xuat_ban(L, M):
    if L["wide"]:
        gi = (200, 110, 1520, 860); may = (330, 210)
        # duong phim chay NGANG tu day may quay toi dai phim (khong duoc dut mach)
        duong = "M540 560 C 700 720, 820 470, 960 640 C 1040 720, 1090 700, 1150 706"
        dai = (1080, 640); keo = (1400, 670); nut = (1560, 300); tay = (1400, 170)
    elif L["square"]:
        gi = (120, 120, 840, 800); may = (270, 210); duong = "M480 520 C 570 640, 400 730, 430 860"
        dai = (300, 800); keo = (620, 830); nut = (830, 300); tay = (700, 200)
    else:
        gi = (230, 330, 620, 1180); may = (360, 430); duong = "M500 740 C 560 860, 400 950, 540 1060 C 660 1160, 480 1260, 470 1380"
        dai = (250, 1330); keo = (600, 1360); nut = (760, 1640); tay = (600, 1560)

    svg = f"""
{tam_giay(*gi, M)}
<path id="duong" d="{duong}" stroke="{M['accent']}" stroke-width="110" fill="none" stroke-linecap="round" style="filter:url(#sh)"/>
<path id="loPhim" d="{duong}" stroke="{M['ink']}" stroke-width="110" fill="none" stroke-linecap="butt"
      stroke-dasharray="13 54" opacity="0.42"/>
<g transform="translate({may[0]} {may[1]})"><g id="may" style="filter:url(#sh)" opacity="0">
  <rect x="0" y="70" width="300" height="180" rx="18" fill="url(#ht)" stroke="{M['ink']}" stroke-width="6"/>
  <g id="cuon1"><circle cx="80" cy="55" r="62" fill="url(#ht)" stroke="{M['ink']}" stroke-width="6"/>
    <circle cx="80" cy="55" r="14" fill="{M['accent']}"/>
    <rect x="73" y="0" width="14" height="40" rx="7" fill="{M['ink']}" opacity="0.6"/></g>
  <g id="cuon2"><circle cx="220" cy="55" r="62" fill="url(#ht)" stroke="{M['ink']}" stroke-width="6"/>
    <circle cx="220" cy="55" r="14" fill="{M['accent']}"/>
    <rect x="213" y="0" width="14" height="40" rx="7" fill="{M['ink']}" opacity="0.6"/></g>
  <rect x="292" y="120" width="120" height="70" rx="10" fill="#2c2a28" stroke="{M['ink']}" stroke-width="6"/>
  <circle cx="412" cy="155" r="40" fill="{M['ink']}"/>
  <circle cx="412" cy="155" r="40" fill="none" stroke="{M['pop']}" stroke-width="10"/>
  <circle id="rec" cx="272" cy="100" r="10" fill="{M['pop']}"/>
</g></g>
<g transform="translate({dai[0]} {dai[1]})"><g id="dai" style="filter:url(#sh)" opacity="0">
  <g filter="url(#tornS)">
    <rect x="0" y="0" width="312" height="150" rx="4" fill="{M['ink']}"/>
    {''.join(f'<rect x="{12+i*58}" y="8" width="20" height="16" rx="3" fill="{M["cream"]}" opacity="0.85"/><rect x="{12+i*58}" y="126" width="20" height="16" rx="3" fill="{M["cream"]}" opacity="0.85"/>' for i in range(5))}
    <rect x="20" y="32" width="130" height="86" fill="url(#ht)"/>
    <rect x="168" y="32" width="130" height="86" fill="url(#ht)"/>
  </g>
  <g id="daiPhai" filter="url(#tornS)">
    <rect x="318" y="0" width="160" height="150" rx="4" fill="{M['ink']}"/>
    {''.join(f'<rect x="{330+i*58}" y="8" width="20" height="16" rx="3" fill="{M["cream"]}" opacity="0.85"/><rect x="{330+i*58}" y="126" width="20" height="16" rx="3" fill="{M["cream"]}" opacity="0.85"/>' for i in range(3))}
    <rect x="330" y="32" width="130" height="86" fill="url(#ht)"/>
  </g>
</g></g>
<g transform="translate({keo[0]} {keo[1]})"><g id="keo" style="filter:url(#sh)" opacity="0">
  <g transform="rotate(-24)">
    <g id="luoiT"><path d="M0 0 L-215 -30 L-215 -12 Z" fill="#d9d6d1" stroke="{M['ink']}" stroke-width="4"/>
      <line x1="0" y1="0" x2="62" y2="-26" stroke="{M['pop']}" stroke-width="13" stroke-linecap="round"/>
      <circle cx="92" cy="-38" r="30" fill="none" stroke="{M['pop']}" stroke-width="15"/></g>
    <g id="luoiD"><path d="M0 0 L-215 30 L-215 12 Z" fill="#efece7" stroke="{M['ink']}" stroke-width="4"/>
      <line x1="0" y1="0" x2="62" y2="26" stroke="{M['pop']}" stroke-width="13" stroke-linecap="round"/>
      <circle cx="92" cy="38" r="30" fill="none" stroke="{M['pop']}" stroke-width="15"/></g>
    <circle cx="0" cy="0" r="9" fill="{M['ink']}"/>
  </g>
</g></g>
<g transform="translate({nut[0]} {nut[1]})"><g id="nut" style="filter:url(#sh)" opacity="0">
  <circle r="80" fill="{M['pop']}"/><circle r="80" fill="none" stroke="{M['cream']}" stroke-width="7"/>
  <path d="M-24 -34 L38 0 L-24 34 Z" fill="{M['cream']}"/>
</g></g>
{ban_tay(tay[0], tay[1], M)}"""

    js = f"""
// 1. giay nen roi xuong
tl.from("#giay", {{y:-260, opacity:0, duration:0.5, ease:"steps(7)"}}, 0);
// 2. duong phim ve dan (stroke-dash)
var d=document.getElementById("duong"), len=d.getTotalLength();
gsap.set(d, {{strokeDasharray:len, strokeDashoffset:len, opacity:0}});
tl.set(d, {{opacity:1}}, 0.25);
tl.to(d, {{strokeDashoffset:0, duration:1.0, ease:"steps(14)"}}, 0.25);
// lo phim lo dan theo dung doan duong da ve toi (khong hien san)
var lo=document.getElementById("loPhim");
gsap.set(lo, {{opacity:0}});
tl.to(lo, {{opacity:0.42, duration:0.9, ease:"steps(12)"}}, 0.35);
// 3. may quay roi xuong, cuon phim quay theo nac
tl.fromTo("#may", {{y:-420, opacity:0}}, {{y:0, opacity:1, duration:0.55, ease:"steps(8)"}}, 0.35);
tl.to("#cuon1", {{rotation:-360, transformOrigin:"center", duration:1.6, repeat:-1, ease:"steps(14)"}}, 0.9);
tl.to("#cuon2", {{rotation:-360, transformOrigin:"center", duration:1.6, repeat:-1, ease:"steps(14)"}}, 0.9);
tl.to("#rec", {{opacity:0.2, duration:0.4, repeat:-1, yoyo:true, ease:"steps(1)"}}, 1.0);
// 4. dai phim truot vao
tl.fromTo("#dai", {{x:-300, opacity:0}}, {{x:0, opacity:1, duration:0.5, ease:"steps(7)"}}, 0.95);
// 5. keo truot vao, cat 2 nhip roi dai phim DUT roi ra
tl.fromTo("#keo", {{x:340, opacity:0}}, {{x:0, opacity:1, duration:0.45, ease:"steps(6)"}}, 1.3);
tl.to("#luoiT", {{rotation:-9, transformOrigin:"0px 0px", duration:0.14, yoyo:true, repeat:3, ease:"steps(2)"}}, 1.75);
tl.to("#luoiD", {{rotation:9, transformOrigin:"0px 0px", duration:0.14, yoyo:true, repeat:3, ease:"steps(2)"}}, 1.75);
tl.to("#daiPhai", {{x:20, y:28, rotation:7, transformOrigin:"318px 150px", duration:0.4, ease:"steps(5)"}}, 2.05);
// 6. tay dua nut play vao roi rut ra
tl.fromTo("#tay", {{x:380, y:520, opacity:0}}, {{x:0, y:0, opacity:1, duration:0.5, ease:"steps(7)"}}, 2.1);
tl.fromTo("#nut", {{scale:0, opacity:0, transformOrigin:"center"}}, {{scale:1, opacity:1, duration:0.4, ease:"back.out(2.2)"}}, 2.45);
tl.to("#tay", {{x:420, y:400, opacity:0, duration:0.5, ease:"steps(6)"}}, 2.65);
tl.to("#nut", {{scale:1.05, duration:0.5, repeat:-1, yoyo:true, ease:"steps(3)"}}, 2.95);
{js_rung("#giay", 0.7, 1.6)}
{js_rung("#may", 1.0, 2.2, 1)}
{js_rung("#dai", 1.5, 1.8, 2)}"""
    return svg, js


# ============================================================
# CANH 2 - thoi gian troi
# ============================================================
def thoi_gian_troi(L, M):
    if L["wide"]:
        gi = (200, 110, 1520, 860); dh = (600, 520, 1.0)
        lich = [(1000, 300), (1180, 430), (1360, 330)]; cat = (1120, 640, 900); x = (1620, 830)
    elif L["square"]:
        gi = (120, 120, 840, 800); dh = (400, 400, 0.82)
        lich = [(680, 220), (740, 450), (620, 670)]; cat = (400, 720, 960); x = (880, 900)
    else:
        gi = (230, 300, 620, 1180); dh = (540, 640, 1.0)
        lich = [(290, 1010), (470, 1120), (640, 1050)]; cat = (540, 1300, 1780); x = (830, 1530)

    to_lich = "".join(mieng(f"lich{i}", lx, ly, f"""
  <g filter="url(#tornS)">
    <rect x="0" y="0" width="150" height="180" rx="6" fill="{M['cream']}" stroke="{M['ink']}" stroke-width="5"/>
    <rect x="0" y="0" width="150" height="46" fill="{M['pop']}"/>
    <rect x="34" y="82" width="82" height="14" rx="7" fill="{M['ink']}" opacity="0.8"/>
    <rect x="34" y="112" width="58" height="14" rx="7" fill="{M['ink']}" opacity="0.55"/>
  </g>""") for i, (lx, ly) in enumerate(lich))

    hat_cat = "".join(
        f'<circle class="cat" cx="{cat[0] + (i%3-1)*22}" cy="{cat[1]}" r="{8-(i%3)}" fill="{M["accent"]}" opacity="0"/>'
        for i in range(12))

    svg = f"""
{tam_giay(*gi, M)}
<g transform="translate({dh[0]} {dh[1]}) scale({dh[2]})"><g id="dongho" style="filter:url(#sh)" opacity="0">
  <circle r="196" fill="url(#ht)" stroke="{M['ink']}" stroke-width="8"/>
  <circle r="164" fill="{M['cream']}" stroke="{M['ink']}" stroke-width="6"/>
  {''.join(f'<line x1="{__import__("math").sin(i/12*6.28318)*132:.1f}" y1="{-__import__("math").cos(i/12*6.28318)*132:.1f}" x2="{__import__("math").sin(i/12*6.28318)*152:.1f}" y2="{-__import__("math").cos(i/12*6.28318)*152:.1f}" stroke="{M["ink"]}" stroke-width="{9 if i%3==0 else 5}" stroke-linecap="round"/>' for i in range(12))}
  <rect id="kimGio" x="-9" y="-92" width="18" height="102" rx="9" fill="{M['ink']}"/>
  <rect id="kimPhut" x="-7" y="-140" width="14" height="150" rx="7" fill="{M['pop']}"/>
  <circle r="16" fill="{M['ink']}"/>
  <rect x="-22" y="-214" width="44" height="26" rx="8" fill="url(#ht)" stroke="{M['ink']}" stroke-width="6"/>
</g></g>
{to_lich}
<g id="dongcat">{hat_cat}</g>
<ellipse id="dongCat" cx="{cat[0]}" cy="{cat[2]}" rx="0" ry="0" fill="{M['accent']}" opacity="0.75"/>
<g transform="translate({x[0]} {x[1]})"><g id="dauX" style="filter:url(#sh)" opacity="0">
  <circle r="78" fill="{M['pop']}"/><circle r="78" fill="none" stroke="{M['cream']}" stroke-width="7"/>
  <path d="M-30 -30 L30 30 M30 -30 L-30 30" stroke="{M['cream']}" stroke-width="16" stroke-linecap="round"/>
</g></g>"""

    js = f"""
tl.from("#giay", {{y:-260, opacity:0, duration:0.5, ease:"steps(7)"}}, 0);
// dong ho roi xuong, kim quay NHANH DAN = thoi gian tuot khoi tay
tl.fromTo("#dongho", {{y:-400, opacity:0}}, {{y:0, opacity:1, duration:0.55, ease:"steps(8)"}}, 0.2);
tl.to("#kimPhut", {{rotation:1440, transformOrigin:"center", duration:2.4, ease:"power2.in"}}, 0.7);
tl.to("#kimGio", {{rotation:120, transformOrigin:"center", duration:2.4, ease:"power2.in"}}, 0.7);
// to lich lan luot roi
{''.join(f'tl.fromTo("#lich{i}", {{y:-40, opacity:0, rotation:{-14+i*11}}}, {{y:{110+i*34}, opacity:1, rotation:{6+i*9}, duration:0.75, ease:"steps(9)"}}, {0.9+i*0.28});' for i in range(3))}
{''.join(f'tl.to("#lich{i}", {{opacity:0.35, duration:0.5, ease:"steps(4)"}}, {2.3+i*0.15});' for i in range(3))}
// dong cat chay lien tuc xuong day
gsap.utils.toArray(".cat").forEach(function(h,i){{
  tl.fromTo(h, {{y:0, opacity:0.9}}, {{y:{cat[2]-cat[1]}, opacity:0.15, duration:1.1,
    repeat:-1, ease:"steps(10)"}}, 0.8 + i*0.09);
}});
tl.to("#dongCat", {{attr:{{rx:170, ry:40}}, duration:1.6, ease:"steps(12)"}}, 1.2);
// dau X chot y
tl.fromTo("#dauX", {{scale:0, opacity:0, transformOrigin:"center"}}, {{scale:1, opacity:1, duration:0.45, ease:"back.out(2)"}}, 2.5);
tl.to("#dauX", {{scale:1.06, duration:0.5, repeat:-1, yoyo:true, ease:"steps(3)"}}, 3.0);
{js_rung("#giay", 0.7, 1.6)}
{js_rung("#dongho", 1.1, 2.0, 1)}"""
    return svg, js


# ============================================================
# CANH 3 - hon loan -> ngan nap
# ============================================================
def hon_loan_ngan_nap(L, M):
    if L["wide"]:
        tu = (520, 230, 880, 620); bay = [(210,250),(1700,210),(170,760),(1740,780),(900,110),(1020,990)]; tick = (1660, 500)
    elif L["square"]:
        tu = (130, 330, 820, 560); bay = [(180,160),(900,150),(120,620),(960,600),(540,120),(560,990)]; tick = (880, 960)
    else:
        tu = (160, 700, 760, 560); bay = [(220,430),(830,380),(180,760),(880,700),(430,300),(700,1560)]; tick = (830, 1600)

    TX, TY, TW, TH = tu
    NG = TH / 3
    ngan = "".join(f"""
    <rect x="{TX+26}" y="{TY+22+i*NG:.0f}" width="{TW-52}" height="{NG-30:.0f}" rx="10" fill="{M['cream']}" stroke="{M['ink']}" stroke-width="6"/>
    <rect x="{TX+TW/2-52:.0f}" y="{TY+NG-42+i*NG:.0f}" width="104" height="16" rx="8" fill="{M['ink']}" opacity="0.55"/>""" for i in range(3))

    to_giay = ""
    for i, (bx, by) in enumerate(bay):
        to_giay += mieng(f"to{i}", bx, by, f"""
  <g filter="url(#tornS)">
    <rect x="-78" y="-100" width="156" height="200" rx="6" fill="{M['cream']}" stroke="{M['ink']}" stroke-width="5"/>
    <rect x="-52" y="-64" width="104" height="13" rx="6" fill="{M['ink']}" opacity="0.72"/>
    <rect x="-52" y="-32" width="78" height="13" rx="6" fill="{M['ink']}" opacity="0.5"/>
    <rect x="-52" y="0" width="94" height="13" rx="6" fill="{M['ink']}" opacity="0.5"/>
    <rect x="-52" y="32" width="60" height="13" rx="6" fill="{M['ink']}" opacity="0.36"/>
    <rect x="-78" y="-100" width="42" height="20" rx="4" fill="{M['accent'] if i%2 else M['pop']}"/>
  </g>""")

    svg = f"""
<g id="tu" style="filter:url(#sh)" opacity="0">
  <g filter="url(#tornS)">
    <rect x="{TX}" y="{TY}" width="{TW}" height="{TH}" rx="12" fill="url(#ht)" stroke="{M['ink']}" stroke-width="8"/>
    {ngan}
    <rect x="{TX-20}" y="{TY+40}" width="20" height="{TH-80}" rx="10" fill="{M['accent']}"/>
  </g>
</g>
{to_giay}
<g transform="translate({tick[0]} {tick[1]})"><g id="tick" style="filter:url(#sh)" opacity="0">
  <circle r="82" fill="{M['pop']}"/><circle r="82" fill="none" stroke="{M['cream']}" stroke-width="7"/>
  <path d="M-34 2 L-8 30 L36 -26" stroke="{M['cream']}" stroke-width="17" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
</g></g>"""

    vao = []
    for i in range(6):
        dx = TX + TW * 0.28 + (i % 2) * TW * 0.44 - bay[i][0]
        dy = TY + NG * 0.5 + (i // 2) * NG - bay[i][1]
        vao.append(f'tl.to("#to{i}", {{x:{dx:.0f}, y:{dy:.0f}, rotation:0, scale:0.62, transformOrigin:"center",'
                   f' duration:0.6, ease:"steps(8)"}}, {1.55 + i*0.16:.2f});')

    js = f"""
// 1. giay bay lung tung khap khung = HON LOAN
{''.join(f'tl.fromTo("#to{i}", {{opacity:0, scale:1.15, rotation:{-22+i*9}}}, {{opacity:1, scale:1, rotation:{-18+i*8}, duration:0.4, ease:"steps(5)"}}, {0.1+i*0.13:.2f});' for i in range(6))}
{''.join(f'tl.to("#to{i}", {{y:"+={10+i*3}", rotation:"+={4 if i%2 else -4}", duration:0.5, repeat:2, yoyo:true, ease:"steps(2)"}}, {0.5+i*0.1:.2f});' for i in range(6))}
// 2. tu ho so hien ra
tl.fromTo("#tu", {{y:300, opacity:0}}, {{y:0, opacity:1, duration:0.5, ease:"steps(7)"}}, 1.25);
// 3. giay lan luot bay VAO dung ngan = NGAN NAP
{''.join(vao)}
// 4. dau tick chot
tl.fromTo("#tick", {{scale:0, opacity:0, transformOrigin:"center"}}, {{scale:1, opacity:1, duration:0.45, ease:"back.out(2)"}}, 2.7);
tl.to("#tick", {{scale:1.06, duration:0.5, repeat:-1, yoyo:true, ease:"steps(3)"}}, 3.2);
{js_rung("#tu", 1.9, 1.6)}"""
    return svg, js


# ============================================================
# CANH 4 - tang truong
# ============================================================
def tang_truong(L, M):
    if L["wide"]:
        gi = (200, 110, 1520, 860); day = 880; rong = 150
        cot = [(400, 200), (640, 330), (880, 470), (1120, 620)]; xu = (1480, 300)
    elif L["square"]:
        gi = (120, 120, 840, 800); day = 830; rong = 120
        cot = [(250, 180), (420, 300), (590, 430), (760, 570)]; xu = (900, 190)
    else:
        gi = (230, 330, 620, 1180); day = 1300; rong = 104
        cot = [(300, 230), (440, 380), (580, 540), (720, 730)]; xu = (830, 520)

    cot_svg = "".join(f"""
<g id="cot{i}" style="filter:url(#sh)">
  <g filter="url(#tornS)">
    <rect x="{cx}" y="{day-ch}" width="{rong}" height="{ch}" rx="6"
          fill="{M['accent'] if i==3 else 'url(#ht)'}" stroke="{M['ink']}" stroke-width="5"/>
  </g>
  <rect x="{cx+rong*0.22:.0f}" y="{day-ch+26}" width="{rong*0.55:.0f}" height="10" rx="5" fill="{M['cream']}" opacity="0.5"/>
</g>""" for i, (cx, ch) in enumerate(cot))

    ten_d = f"M{cot[0][0]-20} {day-cot[0][1]+50} " + " ".join(
        f"L{cx+rong/2:.0f} {day-ch-10}" for cx, ch in cot)

    svg = f"""
{tam_giay(*gi, M)}
<rect id="truc" x="{cot[0][0]-50}" y="{day}" width="{cot[3][0]-cot[0][0]+rong+100}" height="12" rx="6" fill="{M['ink']}" opacity="0.8"/>
{cot_svg}
<path id="muiten" d="{ten_d}" stroke="{M['pop']}" stroke-width="18" fill="none" stroke-linecap="round" stroke-linejoin="round" style="filter:url(#sh)"/>
<g transform="translate({cot[3][0]+rong/2:.0f} {day-cot[3][1]-10}) rotate(-50)"><g id="dinhten" opacity="0">
  <path d="M0 -34 L30 12 L-30 12 Z" fill="{M['pop']}"/>
</g></g>
<g transform="translate({xu[0]} {xu[1]})"><g id="xu" style="filter:url(#sh)" opacity="0">
  <circle r="72" fill="{M['accent']}" stroke="{M['ink']}" stroke-width="6"/>
  <circle r="52" fill="none" stroke="{M['ink']}" stroke-width="5" opacity="0.6"/>
  <rect x="-8" y="-34" width="16" height="68" rx="8" fill="{M['ink']}" opacity="0.85"/>
  <rect x="-26" y="-12" width="52" height="12" rx="6" fill="{M['ink']}" opacity="0.85"/>
</g></g>"""

    js = f"""
tl.from("#giay", {{y:-260, opacity:0, duration:0.5, ease:"steps(7)"}}, 0);
tl.from("#truc", {{scaleX:0, transformOrigin:"left center", duration:0.4, ease:"steps(5)"}}, 0.3);
// 4 cot moc len so le
{''.join(f'tl.from("#cot{i}", {{scaleY:0, transformOrigin:"center bottom", duration:0.45, ease:"steps(6)"}}, {0.5+i*0.22:.2f});' for i in range(4))}
// mui ten leo qua dinh cac cot
var m=document.getElementById("muiten"), ml=m.getTotalLength();
gsap.set(m, {{strokeDasharray:ml, strokeDashoffset:ml, opacity:0}});
tl.set(m, {{opacity:1}}, 1.45);
tl.to(m, {{strokeDashoffset:0, duration:0.9, ease:"steps(12)"}}, 1.45);
tl.to("#dinhten", {{opacity:1, duration:0.1, ease:"steps(1)"}}, 2.3);
// dong xu nay len
tl.fromTo("#xu", {{scale:0, opacity:0, transformOrigin:"center"}}, {{scale:1, opacity:1, duration:0.45, ease:"back.out(2.2)"}}, 2.45);
tl.to("#xu", {{y:"-=14", duration:0.5, repeat:-1, yoyo:true, ease:"steps(4)"}}, 2.95);
{''.join(f'tl.to("#cot{i}", {{y:"-=3", duration:0.4, repeat:-1, yoyo:true, ease:"steps(1)"}}, {1.2+i*0.1:.2f});' for i in range(4))}
{js_rung("#giay", 0.7, 1.6)}"""
    return svg, js


# ============================================================
# CANH 5 - may lam thay
# ============================================================
def may_lam_thay(L, M):
    if L["wide"]:
        gi = (250, 120, 1420, 840)
        rang = [(560, 460, 150, 12, None), (862, 620, 106, 10, "accent"), (640, 790, 92, 10, None), (1090, 470, 80, 9, "accent")]
        tay = (1180, 700); nguon = (1520, 760)
    elif L["square"]:
        gi = (150, 150, 780, 780)
        rang = [(420, 430, 140, 12, None), (690, 590, 100, 10, "accent"), (400, 730, 88, 10, None), (700, 300, 74, 9, "accent")]
        tay = (700, 880); nguon = (880, 930)
    else:
        gi = (230, 300, 620, 1180)
        rang = [(470, 620, 150, 12, None), (748, 800, 104, 10, "accent"), (420, 968, 96, 10, None), (676, 1180, 78, 9, "accent")]
        tay = (640, 1500); nguon = (846, 1420)

    def banh(i, cx, cy, r, so, mau):
        m = M["accent"] if mau else "url(#ht)"
        rang_svg = "".join(
            f'<rect x="{cx-15}" y="{cy-r-20}" width="30" height="34" rx="5" fill="{m}" stroke="{M["ink"]}" stroke-width="4" transform="rotate({j*360/so:.1f} {cx} {cy})"/>'
            for j in range(so))
        nan = "".join(
            f'<rect x="{cx-7}" y="{cy-r*0.66+6:.0f}" width="14" height="{r*0.66-16:.0f}" rx="7" fill="{M["ink"]}" opacity="0.55" transform="rotate({k*120} {cx} {cy})"/>'
            for k in range(3))
        return f"""
<g id="rang{i}" style="filter:url(#sh)" opacity="0">{rang_svg}
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="{m}" stroke="{M['ink']}" stroke-width="6"/>
  <circle cx="{cx}" cy="{cy}" r="{r*0.66:.0f}" fill="{M['cream']}" stroke="{M['ink']}" stroke-width="5"/>
  <circle cx="{cx}" cy="{cy}" r="{r*0.18:.0f}" fill="{M['ink']}"/>{nan}
</g>"""

    tia = "".join(
        # Mau NHAN (vang), khong dung mau kem: tia kem ve tren giay kem = vo hinh.
        f'<rect class="tia" x="{rang[0][0]-8}" y="{rang[0][1]-rang[0][2]-64}" width="16" height="46" rx="8" fill="{M["accent"]}" opacity="0" transform="rotate({i*45+17} {rang[0][0]} {rang[0][1]})"/>'
        for i in range(8))

    svg = f"""
{tam_giay(*gi, M)}
{''.join(banh(i, *r) for i, r in enumerate(rang))}
{tia}
{ban_tay(tay[0], tay[1], M)}
<g transform="translate({nguon[0]} {nguon[1]})"><g id="nguon" style="filter:url(#sh)" opacity="0">
  <circle r="74" fill="{M['pop']}"/><circle r="74" fill="none" stroke="{M['cream']}" stroke-width="7"/>
  <path d="M0 -34 A 34 34 0 1 0 22 -26" stroke="{M['cream']}" stroke-width="13" fill="none" stroke-linecap="round"/>
  <rect x="-7" y="-42" width="14" height="34" rx="7" fill="{M['cream']}"/>
</g></g>"""

    quay = "".join(
        f'tl.to("#rang{i}", {{rotation:{-360 if i%2 else 360}, transformOrigin:"center",'
        f' duration:{2.2+i*0.3}, repeat:-1, ease:"steps({16+i*2})"}}, {0.9+i*0.12:.2f});'
        for i, r in enumerate(rang))

    svg_vao = "".join(
        f'tl.fromTo("#rang{i}", {{opacity:0, scale:0.4, transformOrigin:"center"}},'
        f' {{opacity:1, scale:1, duration:0.4, ease:"back.out(1.8)"}}, {0.25+i*0.2:.2f});'
        for i, r in enumerate(rang))

    js = f"""
tl.from("#giay", {{y:-260, opacity:0, duration:0.5, ease:"steps(7)"}}, 0);
// 4 banh rang vao roi an khop quay (nguoc chieu nhau)
{svg_vao}
{quay}
// tia sang toa ra khi may chay
tl.to(".tia", {{opacity:0.9, duration:0.3, stagger:0.04, ease:"steps(3)"}}, 1.5);
tl.to(".tia", {{opacity:0.35, duration:0.5, repeat:-1, yoyo:true, ease:"steps(2)"}}, 2.0);
// ban tay buong ra = may lam thay nguoi
tl.fromTo("#tay", {{x:380, y:520, opacity:0}}, {{x:0, y:0, opacity:1, duration:0.5, ease:"steps(7)"}}, 1.55);
tl.to("#tay", {{x:420, y:400, opacity:0, duration:0.55, ease:"steps(6)"}}, 2.35);
// nut nguon bat sang
tl.fromTo("#nguon", {{scale:0, opacity:0, transformOrigin:"center"}}, {{scale:1, opacity:1, duration:0.45, ease:"back.out(2)"}}, 2.55);
tl.to("#nguon", {{scale:1.06, duration:0.5, repeat:-1, yoyo:true, ease:"steps(3)"}}, 3.05);
{js_rung("#giay", 0.7, 1.6)}"""
    return svg, js


DS_CANH = {
    "quay-cat-xuat-ban": quay_cat_xuat_ban,
    "thoi-gian-troi": thoi_gian_troi,
    "hon-loan-ngan-nap": hon_loan_ngan_nap,
    "tang-truong": tang_truong,
    "may-lam-thay": may_lam_thay,
}
