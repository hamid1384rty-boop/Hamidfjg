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
    get_special_widget as gsw
)
from bascenev1 import chatmessage as CM
import urllib.request
import urllib.error
import json

# ============================================
# کلاس مدیریت پنجره مرورگر
# ============================================
class MiniBrowser:
    def __init__(s, source=None):
        if hasattr(s, 'w') and s.w:
            try:
                s._close()
            except:
                pass

        # ایجاد پنجره اصلی
        w = s.w = cw(
            parent=gsw('overlay_stack'),
            size=(500, 400),
            scale=0.9,
            transition='in_scale',
            color=(0.15, 0.15, 0.2)
        )

        # عنوان پنجره
        tw(
            parent=w,
            text='🌐 Mini Browser',
            scale=1.1,
            position=(250, 375),
            h_align='center',
            color=(0.6, 0.8, 1)
        )

        # نوار آدرس
        s.url_input = tw(
            parent=w,
            maxwidth=350,
            size=(350, 30),
            editable=True,
            v_align='center',
            color=(0.75, 0.75, 0.75),
            position=(40, 340),
            allow_clear_button=False,
            text='https://www.google.com'
        )

        # دکمه رفتن
        bw(
            parent=w,
            label='🔍',
            size=(40, 30),
            position=(400, 340),
            on_activate_call=CallStrict(s._navigate),
            color=(0.2, 0.4, 0.6)
        )

        # دکمه تازه‌سازی
        bw(
            parent=w,
            label='🔄',
            size=(40, 30),
            position=(445, 340),
            on_activate_call=CallStrict(s._refresh),
            color=(0.2, 0.4, 0.2)
        )

        # دکمه بستن
        bw(
            parent=w,
            label='✖',
            size=(30, 30),
            position=(465, 375),
            on_activate_call=CallStrict(s._close),
            color=(0.5, 0.1, 0.1)
        )

        # منطقه نمایش محتوا (اسکرول)
        s.scroll = sw(
            parent=w,
            size=(460, 260),
            position=(20, 50),
            color=(0.1, 0.1, 0.12),
            highlight=False
        )

        # کانتینر محتوا
        s.content_container = cw(
            parent=s.scroll,
            size=(440, 240),
            background=False
        )

        # پیام پیش‌فرض
        tw(
            parent=s.content_container,
            text='🌐 لطفاً یک آدرس وارد کنید\n\nمثال:\nhttps://www.google.com\nhttps://www.wikipedia.org\nhttps://www.github.com',
            scale=0.9,
            position=(220, 120),
            h_align='center',
            color=(0.7, 0.7, 0.8)
        )

        # دکمه‌های سریع
        quick_buttons = [
            ('Google', 'https://www.google.com'),
            ('Wikipedia', 'https://www.wikipedia.org'),
            ('Github', 'https://www.github.com'),
            ('Stack', 'https://stackoverflow.com')
        ]

        x_pos = 20
        for label, url in quick_buttons:
            bw(
                parent=w,
                label=label,
                size=(70, 25),
                position=(x_pos, 18),
                on_activate_call=CallStrict(s._quick_open, url),
                color=(0.2, 0.25, 0.3),
                text_scale=0.6
            )
            x_pos += 75

        # دکمه خروج
        bw(
            parent=w,
            label='❌ Close',
            size=(100, 25),
            position=(380, 18),
            on_activate_call=CallStrict(s._close),
            color=(0.4, 0.1, 0.1),
            text_scale=0.7
        )

        cw(w, on_outside_click_call=CallStrict(s._close))
        s._load_url("https://www.google.com")

    def _navigate(s):
        """بارگذاری آدرس وارد شده"""
        url = tw(query=s.url_input).strip()
        if not url:
            return
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url
        s._load_url(url)

    def _refresh(s):
        """تازه‌سازی صفحه فعلی"""
        url = tw(query=s.url_input).strip()
        if url:
            s._load_url(url)

    def _quick_open(s, url):
        """باز کردن آدرس سریع"""
        tw(s.url_input, text=url)
        s._load_url(url)

    def _load_url(s, url):
        """بارگذاری URL و نمایش محتوا"""
        for child in s.content_container.get_children():
            child.delete()

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode('utf-8', errors='ignore')

                title = s._extract_title(content)
                if title:
                    tw(
                        parent=s.content_container,
                        text=f'📄 {title}',
                        scale=0.8,
                        position=(220, 215),
                        h_align='center',
                        color=(0.8, 1, 0.8),
                        maxwidth=400
                    )

                text_content = s._extract_text(content)
                if text_content:
                    tw(
                        parent=s.content_container,
                        text=text_content[:500] + ('...' if len(text_content) > 500 else ''),
                        scale=0.6,
                        position=(20, 190),
                        color=(0.8, 0.8, 0.9),
                        maxwidth=420
                    )

                links = s._extract_links(content)
                if links:
                    tw(
                        parent=s.content_container,
                        text='🔗 لینک‌های پیدا شده:',
                        scale=0.7,
                        position=(20, 170),
                        color=(0.6, 0.8, 1)
                    )
                    y_pos = 150
                    for link_text, link_url in links[:5]:
                        bw(
                            parent=s.content_container,
                            label=link_text[:30],
                            size=(200, 20),
                            position=(20, y_pos),
                            on_activate_call=CallStrict(s._quick_open, link_url),
                            color=(0.15, 0.2, 0.3),
                            text_scale=0.5
                        )
                        y_pos -= 25

                if not title and not text_content:
                    tw(
                        parent=s.content_container,
                        text='✅ صفحه با موفقیت بارگذاری شد\n(محتوا قابل نمایش نیست)',
                        scale=0.8,
                        position=(220, 120),
                        h_align='center',
                        color=(0.6, 1, 0.6)
                    )

                push(f'🌐 صفحه بارگذاری شد: {url}', color=(0, 1, 0))

        except urllib.error.URLError as e:
            tw(
                parent=s.content_container,
                text=f'❌ خطا در بارگذاری:\n{str(e)}',
                scale=0.8,
                position=(220, 120),
                h_align='center',
                color=(1, 0.5, 0.5)
            )
            push(f'❌ خطا: {str(e)}', color=(1, 0.5, 0))
        except Exception as e:
            tw(
                parent=s.content_container,
                text=f'❌ خطای ناشناخته:\n{str(e)}',
                scale=0.8,
                position=(220, 120),
                h_align='center',
                color=(1, 0.5, 0.5)
            )
            push(f'❌ خطا: {str(e)}', color=(1, 0.5, 0))

    def _extract_title(s, html):
        try:
            start = html.find('<title>')
            if start != -1:
                end = html.find('</title>', start)
                if end != -1:
                    return html[start+7:end].strip()
        except:
            pass
        return None

    def _extract_text(s, html):
        try:
            import re
            text = re.sub(r'<[^>]+>', ' ', html)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
        except:
            return None

    def _extract_links(s, html):
        links = []
        try:
            import re
            pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>'
            matches = re.findall(pattern, html, re.IGNORECASE)
            for url, text in matches[:10]:
                if url.startswith('/'):
                    base = tw(query=s.url_input).strip()
                    if base and base.endswith('/'):
                        url = base + url
                    elif base:
                        url = base + '/' + url
                if url and not url.startswith('javascript:'):
                    links.append((text.strip()[:30], url))
        except:
            pass
        return links

    def _close(s):
        try:
            gs('swish').play()
            if hasattr(s, 'w') and s.w:
                cw(s.w, transition='out_scale')
                s.w = None
        except:
            pass

# ============================================
# کلاس دکمه در صفحه چت (همانند روش zed2.py)
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
        
        # ===== ذخیره تابع اصلی =====
        original_init = party.PartyWindow.__init__
        
        # ===== تعریف تابع جدید با دکمه در جایگاه متفاوت =====
        def patched_init(self, *a, **k):
            r = original_init(self, *a, **k)
            
            # ===== ایجاد دکمه مرورگر در جایگاه متفاوت =====
            # اینجا موقعیت دکمه رو تغییر میدیم
            # در zed2.py موقعیت: (slf._width-495, slf._height-260)
            # موقعیت جدید: پایین سمت چپ (30, 30) یا هر جای دیگه
            b = SC.bw(
                icon=gt('achievementCrossHair'),  # یا هر آیکون دیگه
                position=(30, 30),  # 🔥 جایگاه جدید: گوشه پایین سمت چپ
                parent=self._root_widget,
                iconscale=1.5,
                size=(40, 40),
                label='🌐',
                color=(0.2, 0.3, 0.5)
            )
            bw(b, on_activate_call=CallPartial(MiniBrowser, source=b))
            return r
        
        # ===== جایگزینی تابع =====
        party.PartyWindow.__init__ = patched_init
        
        s._patched = True
        print("✅ MiniBrowser button added to chat (position: bottom-left)")

    def on_app_quit(s):
        """هنگام خروج برنامه"""
        try:
            from bauiv1lib import party
            # بازیابی تابع اصلی (اختیاری)
            pass
        except:
            pass