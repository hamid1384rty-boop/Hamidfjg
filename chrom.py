# MiniBrowser - مرورگر کوچک داخل بازی BombSquad
# Copyright 2025
from babase import Plugin
from bauiv1 import (
    containerwidget as cw,
    textwidget as tw,
    buttonwidget as bw,
    gettexture as gt,
    apptimer as teck,
    getsound as gs,
    app as APP,
    CallStrict,
    CallPartial,
    scrollwidget as sw,
    columnwidget as clw,
    imagewidget as iw,
    get_special_widget as gsw,
    screenmessage as push
)
from bascenev1 import chatmessage as CM
import urllib.request
import urllib.error
import json
import re

# ============================================
# کلاس مدیریت پنجره مرورگر با نمایش بهتر
# ============================================
class MiniBrowser:
    def __init__(s, source=None):
        if hasattr(s, 'w') and s.w:
            try:
                s._close()
            except:
                pass

        # پنجره بزرگتر
        w = s.w = cw(
            parent=gsw('overlay_stack'),
            size=(600, 500),
            scale=0.95,
            transition='in_scale',
            color=(0.1, 0.1, 0.15)
        )

        # عنوان و نوار آدرس
        tw(
            parent=w,
            text='🌐 Mini Browser',
            scale=1.2,
            position=(300, 470),
            h_align='center',
            color=(0.6, 0.8, 1)
        )

        s.url_input = tw(
            parent=w,
            maxwidth=450,
            size=(450, 35),
            editable=True,
            v_align='center',
            color=(0.75, 0.75, 0.75),
            position=(30, 420),
            allow_clear_button=False,
            text='https://bslife.ir/index.php?post=Tactic'
        )

        # دکمه‌ها
        bw(
            parent=w,
            label='🔍',
            size=(40, 35),
            position=(490, 420),
            on_activate_call=CallStrict(s._navigate),
            color=(0.2, 0.4, 0.6)
        )
        bw(
            parent=w,
            label='🔄',
            size=(40, 35),
            position=(535, 420),
            on_activate_call=CallStrict(s._refresh),
            color=(0.2, 0.4, 0.2)
        )
        bw(
            parent=w,
            label='✖',
            size=(35, 35),
            position=(565, 470),
            on_activate_call=CallStrict(s._close),
            color=(0.5, 0.1, 0.1)
        )

        # منطقه نمایش محتوا (بزرگتر)
        s.scroll = sw(
            parent=w,
            size=(560, 330),
            position=(20, 60),
            color=(0.05, 0.05, 0.1),
            highlight=False
        )

        s.content_container = cw(
            parent=s.scroll,
            size=(540, 310),
            background=False
        )

        # دکمه‌های سریع
        quick_buttons = [
            ('Google', 'https://www.google.com'),
            ('BSLIFE', 'https://bslife.ir'),
            ('Github', 'https://www.github.com'),
            ('Wiki', 'https://www.wikipedia.org')
        ]

        x_pos = 20
        for label, url in quick_buttons:
            bw(
                parent=w,
                label=label,
                size=(70, 25),
                position=(x_pos, 20),
                on_activate_call=CallStrict(s._quick_open, url),
                color=(0.2, 0.25, 0.3),
                text_scale=0.6
            )
            x_pos += 80

        bw(
            parent=w,
            label='❌ Close',
            size=(100, 25),
            position=(480, 20),
            on_activate_call=CallStrict(s._close),
            color=(0.4, 0.1, 0.1),
            text_scale=0.7
        )

        cw(w, on_outside_click_call=CallStrict(s._close))
        teck(0.5, CallStrict(s._load_url, "https://bslife.ir/index.php?post=Tactic"))

    def _navigate(s):
        url = tw(query=s.url_input).strip()
        if not url:
            return
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url
        s._load_url(url)

    def _refresh(s):
        url = tw(query=s.url_input).strip()
        if url:
            s._load_url(url)

    def _quick_open(s, url):
        tw(s.url_input, text=url)
        s._load_url(url)

    def _load_url(s, url):
        for child in s.content_container.get_children():
            child.delete()

        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5"
                }
            )

            with urllib.request.urlopen(req, timeout=15) as response:
                content = response.read().decode('utf-8', errors='ignore')

                # ===== نمایش بهتر =====
                y_pos = 290
                
                # 1. عنوان صفحه
                title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
                if title_match:
                    title = title_match.group(1).strip()
                    tw(
                        parent=s.content_container,
                        text=f'📄 {title}',
                        scale=0.9,
                        position=(20, y_pos),
                        color=(0.8, 1, 0.8),
                        maxwidth=500
                    )
                    y_pos -= 35

                # 2. توضیحات متا
                desc_match = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']', content, re.IGNORECASE)
                if desc_match:
                    desc = desc_match.group(1).strip()
                    tw(
                        parent=s.content_container,
                        text=f'📝 {desc[:200]}...' if len(desc) > 200 else f'📝 {desc}',
                        scale=0.65,
                        position=(20, y_pos),
                        color=(0.7, 0.9, 0.7),
                        maxwidth=500
                    )
                    y_pos -= 30

                # 3. لینک‌ها
                links = []
                pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>'
                matches = re.findall(pattern, content, re.IGNORECASE)
                for link_url, link_text in matches[:15]:
                    if link_url.startswith('/'):
                        base = '/'.join(url.split('/')[:3])
                        link_url = base + link_url
                    if link_url and not link_url.startswith('javascript:') and not link_url.startswith('#'):
                        clean_text = re.sub(r'<[^>]+>', '', link_text).strip()
                        if clean_text and len(clean_text) > 1:
                            links.append((clean_text[:30], link_url))

                if links:
                    tw(
                        parent=s.content_container,
                        text='🔗 لینک‌ها:',
                        scale=0.8,
                        position=(20, y_pos),
                        color=(0.6, 0.8, 1)
                    )
                    y_pos -= 30
                    
                    for link_text, link_url in links[:8]:
                        btn = bw(
                            parent=s.content_container,
                            label=f'🔗 {link_text}',
                            size=(500, 25),
                            position=(20, y_pos),
                            on_activate_call=CallStrict(s._quick_open, link_url),
                            color=(0.12, 0.15, 0.2),
                            text_scale=0.55
                        )
                        y_pos -= 30

                # 4. محتوای متنی
                text_content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
                text_content = re.sub(r'<style[^>]*>.*?</style>', '', text_content, flags=re.DOTALL)
                text_content = re.sub(r'<[^>]+>', ' ', text_content)
                text_content = re.sub(r'\s+', ' ', text_content).strip()
                
                if text_content:
                    tw(
                        parent=s.content_container,
                        text='📝 متن صفحه:',
                        scale=0.7,
                        position=(20, y_pos),
                        color=(0.5, 0.7, 0.9)
                    )
                    y_pos -= 25
                    
                    # نمایش متن به صورت پاراگراف‌های کوتاه
                    paragraphs = text_content.split('. ')
                    for para in paragraphs[:5]:
                        if len(para) > 5:
                            para_text = para[:200] + ('...' if len(para) > 200 else '')
                            tw(
                                parent=s.content_container,
                                text=f'• {para_text}',
                                scale=0.55,
                                position=(30, y_pos),
                                color=(0.75, 0.75, 0.85),
                                maxwidth=480
                            )
                            y_pos -= 25

                if not title_match and not links and not text_content:
                    tw(
                        parent=s.content_container,
                        text='✅ صفحه بارگذاری شد\n(محتوای قابل نمایش نیست)',
                        scale=0.8,
                        position=(270, 150),
                        h_align='center',
                        color=(0.6, 1, 0.6)
                    )

                push(f'🌐 بارگذاری شد: {url}', color=(0, 1, 0))

        except Exception as e:
            tw(
                parent=s.content_container,
                text=f'❌ خطا:\n{str(e)}',
                scale=0.8,
                position=(270, 150),
                h_align='center',
                color=(1, 0.5, 0.5)
            )
            push(f'❌ خطا: {str(e)}', color=(1, 0.5, 0))

    def _close(s):
        try:
            gs('swish').play()
            if hasattr(s, 'w') and s.w:
                cw(s.w, transition='out_scale')
                s.w = None
        except:
            pass

# ============================================
# کلاس دکمه (همانند روش zed2.py)
# ============================================
class SC:
    @classmethod
    def bw(c, **k):
        kwargs = dict(k)
        if 'textcolor' not in kwargs:
            kwargs['textcolor'] = (1, 1, 1)
        if 'enable_sound' not in kwargs:
            kwargs['enable_sound'] = False
        if 'button_type' not in kwargs:
            kwargs['button_type'] = 'square'
        if 'color' not in kwargs:
            kwargs['color'] = (0.18, 0.18, 0.18)
        return bw(**kwargs)

# ============================================
# کلاس اصلی پلاگین
# ============================================
pr = 'mb_'

def var(s, v=None):
    c = APP.config
    s = pr + s
    if v is None:
        return c.get(s, v)
    c[s] = v
    c.commit()

# ba_meta require api 9
# ba_meta export babase.Plugin
class MiniBrowserPlugin(Plugin):
    def __init__(s):
        from bauiv1lib import party
        
        print("🌐 MiniBrowser Plugin activated")
        
        original_init = party.PartyWindow.__init__
        
        def patched_init(self, *a, **k):
            r = original_init(self, *a, **k)
            
            # 🔥 دکمه در گوشه پایین چپ (30, 30)
            b = SC.bw(
                icon=gt('achievementCrossHair'),
                position=(30, 30),  # گوشه پایین چپ
                parent=self._root_widget,
                iconscale=1.5,
                size=(45, 45),
                label='🌐',
                color=(0.2, 0.3, 0.5)
            )
            bw(b, on_activate_call=CallPartial(MiniBrowser, source=b))
            return r
        
        party.PartyWindow.__init__ = patched_init
        
        s._patched = True
        print("✅ MiniBrowser button added (bottom-left)")

    def on_app_quit(s):
        pass