# MiniBrowser - مرورگر کامل مثل کروم داخل بازی (یک کد کامل)
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
    get_special_widget as gsw,
    screenmessage as push
)
from bascenev1 import chatmessage as CM
import os
import urllib.request
import re
import webbrowser
import json

# ============================================
# کلاس WebView داخلی (شبیه‌سازی کروم)
# ============================================
class ChromeView:
    def __init__(s, parent_widget):
        s.parent = parent_widget
        s.history = []
        s.current_index = -1
        s.bookmarks = []
        s._create_ui()
    
    def _create_ui(s):
        # ===== نوار ابزار =====
        s.toolbar = cw(
            parent=s.parent,
            size=(560, 40),
            position=(10, 310),
            background=False
        )
        
        # دکمه‌های ناوبری
        s.btn_back = bw(
            parent=s.toolbar,
            label='◀',
            size=(30, 30),
            position=(5, 5),
            on_activate_call=CallStrict(s._go_back),
            color=(0.2, 0.3, 0.5),
            text_scale=0.7
        )
        
        s.btn_forward = bw(
            parent=s.toolbar,
            label='▶',
            size=(30, 30),
            position=(40, 5),
            on_activate_call=CallStrict(s._go_forward),
            color=(0.2, 0.3, 0.5),
            text_scale=0.7
        )
        
        s.btn_refresh = bw(
            parent=s.toolbar,
            label='🔄',
            size=(30, 30),
            position=(75, 5),
            on_activate_call=CallStrict(s._refresh),
            color=(0.2, 0.4, 0.2),
            text_scale=0.7
        )
        
        s.btn_home = bw(
            parent=s.toolbar,
            label='🏠',
            size=(30, 30),
            position=(110, 5),
            on_activate_call=CallStrict(s._go_home),
            color=(0.2, 0.3, 0.2),
            text_scale=0.7
        )
        
        # نوار آدرس
        s.url_bar = tw(
            parent=s.toolbar,
            maxwidth=280,
            size=(280, 30),
            editable=True,
            v_align='center',
            color=(0.75, 0.75, 0.75),
            position=(145, 5),
            allow_clear_button=True,
            text='https://www.google.com'
        )
        
        # دکمه Go
        s.btn_go = bw(
            parent=s.toolbar,
            label='🚀',
            size=(30, 30),
            position=(430, 5),
            on_activate_call=CallStrict(s._navigate),
            color=(0.2, 0.4, 0.6),
            text_scale=0.7
        )
        
        # دکمه بوکمارک
        s.btn_bookmark = bw(
            parent=s.toolbar,
            label='⭐',
            size=(30, 30),
            position=(465, 5),
            on_activate_call=CallStrict(s._toggle_bookmark),
            color=(0.3, 0.3, 0.1),
            text_scale=0.7
        )
        
        # دکمه تاریخچه
        s.btn_history = bw(
            parent=s.toolbar,
            label='📜',
            size=(30, 30),
            position=(500, 5),
            on_activate_call=CallStrict(s._show_history),
            color=(0.2, 0.2, 0.4),
            text_scale=0.7
        )
        
        # دکمه بستن
        s.btn_close = bw(
            parent=s.toolbar,
            label='✖',
            size=(30, 30),
            position=(535, 5),
            on_activate_call=CallStrict(s._close),
            color=(0.5, 0.1, 0.1),
            text_scale=0.7
        )
        
        # ===== صفحه نمایش محتوا =====
        s.content_area = cw(
            parent=s.parent,
            size=(560, 260),
            position=(10, 40),
            color=(0.05, 0.05, 0.08)
        )
        
        # وضعیت
        s.status = tw(
            parent=s.parent,
            text='✅ Ready',
            scale=0.5,
            position=(20, 18),
            color=(0.5, 0.8, 0.5)
        )
        
        # بارگذاری صفحه اول
        s._load_url("https://www.google.com")
    
    def _navigate(s):
        url = tw(query=s.url_bar).strip()
        if url:
            if not url.startswith('http://') and not url.startswith('https://'):
                url = 'https://' + url
            s._load_url(url)
    
    def _load_url(s, url):
        # پاک کردن محتوا
        for child in s.content_area.get_children():
            child.delete()
        
        tw(s.status, text=f'🔄 Loading: {url}')
        
        # اضافه به تاریخچه
        if s.current_index == -1 or s.history[s.current_index] != url:
            s.history = s.history[:s.current_index + 1]
            s.history.append(url)
            s.current_index += 1
        
        # ===== نمایش محتوا =====
        try:
            # تلاش برای دریافت محتوا
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode('utf-8', errors='ignore')
                
                # استخراج اطلاعات
                title = s._extract_title(content)
                text = s._extract_text(content)
                links = s._extract_links(content, url)
                
                # نمایش عنوان
                if title:
                    tw(
                        parent=s.content_area,
                        text=f'📄 {title}',
                        scale=0.9,
                        position=(280, 230),
                        h_align='center',
                        color=(0.8, 1, 0.8),
                        maxwidth=500
                    )
                    tw(s.url_bar, text=url)
                    tw(s.status, text=f'✅ {title}')
                
                # نمایش متن
                if text:
                    tw(
                        parent=s.content_area,
                        text=text[:300] + ('...' if len(text) > 300 else ''),
                        scale=0.55,
                        position=(20, 200),
                        color=(0.7, 0.7, 0.8),
                        maxwidth=520
                    )
                
                # نمایش لینک‌ها
                if links:
                    tw(
                        parent=s.content_area,
                        text='🔗 Links:',
                        scale=0.65,
                        position=(20, 175),
                        color=(0.6, 0.8, 1)
                    )
                    y_pos = 155
                    for link_text, link_url in links[:8]:
                        bw(
                            parent=s.content_area,
                            label=f'🔗 {link_text[:25]}',
                            size=(520, 22),
                            position=(20, y_pos),
                            on_activate_call=CallStrict(s._load_url, link_url),
                            color=(0.1, 0.12, 0.18),
                            text_scale=0.5
                        )
                        y_pos -= 28
                
                if not title and not text:
                    tw(
                        parent=s.content_area,
                        text='✅ Page loaded successfully',
                        scale=0.8,
                        position=(280, 140),
                        h_align='center',
                        color=(0.6, 1, 0.6)
                    )
                
                push(f'🌐 Loaded: {url}', color=(0, 1, 0))
                
        except Exception as e:
            tw(
                parent=s.content_area,
                text=f'❌ Error:\n{str(e)}',
                scale=0.7,
                position=(280, 140),
                h_align='center',
                color=(1, 0.5, 0.5)
            )
            tw(s.status, text=f'❌ Error: {str(e)}')
            push(f'❌ Error: {str(e)}', color=(1, 0.5, 0))
    
    def _extract_title(s, html):
        try:
            match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
            return match.group(1).strip() if match else None
        except:
            return None
    
    def _extract_text(s, html):
        try:
            text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text[:500]
        except:
            return None
    
    def _extract_links(s, html, base_url):
        links = []
        try:
            pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>'
            matches = re.findall(pattern, html, re.IGNORECASE)
            for link_url, link_text in matches[:15]:
                if link_url.startswith('/'):
                    base = '/'.join(base_url.split('/')[:3])
                    link_url = base + link_url
                elif link_url.startswith('#'):
                    continue
                if link_url and not link_url.startswith('javascript:'):
                    clean_text = re.sub(r'<[^>]+>', '', link_text).strip()
                    if clean_text and len(clean_text) > 1:
                        links.append((clean_text[:30], link_url))
        except:
            pass
        return links
    
    def _go_back(s):
        if s.current_index > 0:
            s.current_index -= 1
            s._load_url(s.history[s.current_index])
    
    def _go_forward(s):
        if s.current_index < len(s.history) - 1:
            s.current_index += 1
            s._load_url(s.history[s.current_index])
    
    def _refresh(s):
        if s.current_index >= 0 and s.current_index < len(s.history):
            s._load_url(s.history[s.current_index])
    
    def _go_home(s):
        s._load_url("https://www.google.com")
    
    def _toggle_bookmark(s):
        url = tw(query=s.url_bar).strip()
        if url in s.bookmarks:
            s.bookmarks.remove(url)
            tw(s.status, text=f'⭐ Bookmark removed')
            push('⭐ Bookmark removed', color=(1, 1, 0))
        else:
            s.bookmarks.append(url)
            tw(s.status, text=f'⭐ Bookmark added: {url}')
            push(f'⭐ Bookmark added: {url}', color=(1, 1, 0))
    
    def _show_history(s):
        if not s.history:
            tw(s.status, text='📜 No history')
            return
        
        # نمایش تاریخچه در پنجره جدید
        hist_window = cw(
            parent=gsw('overlay_stack'),
            size=(300, 200),
            scale=0.8,
            transition='in_scale',
            color=(0.08, 0.08, 0.12)
        )
        
        tw(
            parent=hist_window,
            text='📜 History',
            scale=0.9,
            position=(150, 180),
            h_align='center',
            color=(0.6, 0.8, 1)
        )
        
        y_pos = 155
        for i, url in enumerate(s.history[-10:]):
            bw(
                parent=hist_window,
                label=f'{i+1}. {url[:30]}',
                size=(280, 22),
                position=(10, y_pos),
                on_activate_call=CallStrict(s._load_url, url),
                color=(0.1, 0.12, 0.18),
                text_scale=0.5
            )
            y_pos -= 28
        
        bw(
            parent=hist_window,
            label='✖ Close',
            size=(100, 25),
            position=(100, 10),
            on_activate_call=CallStrict(lambda: cw(hist_window, transition='out_scale')),
            color=(0.4, 0.1, 0.1),
            text_scale=0.6
        )
        
        cw(hist_window, on_outside_click_call=CallStrict(lambda: cw(hist_window, transition='out_scale')))
    
    def _close(s):
        if s.parent:
            try:
                cw(s.parent, transition='out_scale')
            except:
                pass

# ============================================
# کلاس پنجره اصلی مرورگر (مثل کروم)
# ============================================
class MiniBrowserWindow:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is not None:
            try:
                cls._instance._close()
            except:
                pass
        cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(s, source=None):
        if hasattr(s, '_initialized') and s._initialized:
            return
        s._initialized = True
        
        # ===== پنجره اصلی مثل کروم =====
        w = s.w = cw(
            parent=gsw('overlay_stack'),
            size=(600, 400),
            scale=0.9,
            transition='in_scale',
            color=(0.06, 0.06, 0.1)
        )
        
        # عنوان
        tw(
            parent=w,
            text='🌐 Chrome Mini',
            scale=1.1,
            position=(300, 380),
            h_align='center',
            color=(0.6, 0.8, 1)
        )
        
        # ===== ایجاد WebView =====
        s.webview = ChromeView(w)
        
        # دکمه بستن پایین
        bw(
            parent=w,
            label='❌ Close Chrome',
            size=(120, 28),
            position=(460, 8),
            on_activate_call=CallStrict(s._close),
            color=(0.4, 0.1, 0.1),
            text_scale=0.6
        )
        
        cw(w, on_outside_click_call=CallStrict(s._close))
        s._initialized = True
        push('🌐 Chrome Mini opened!', color=(0, 1, 0))
    
    def _close(s):
        try:
            gs('swish').play()
            if hasattr(s, 'w') and s.w:
                cw(s.w, transition='out_scale')
                s.w = None
            s._initialized = False
            MiniBrowserWindow._instance = None
            push('❌ Chrome closed', color=(1, 0.5, 0))
        except:
            pass

# ============================================
# کلاس دکمه (دقیقاً مثل zed2.py)
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
# کلاس اصلی پلاگین (دقیقاً مثل zed2.py)
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
        
        print("🌐 Chrome Mini Plugin activated")
        
        # ===== ذخیره تابع اصلی (مثل zed2.py) =====
        original_init = party.PartyWindow.__init__
        
        # ===== تعریف تابع جدید با دکمه (مثل zed2.py) =====
        def patched_init(self, *a, **k):
            r = original_init(self, *a, **k)
            
            # ===== ایجاد دکمه کروم (دقیقاً مثل zed2.py ولی جای متفاوت) =====
            b = SC.bw(
                icon=gt('achievementCrossHair'),
                position=(self._width - 495, self._height - 300),  # جای متفاوت از آنتی‌کد
                parent=self._root_widget,
                iconscale=1.2,
                size=(30, 30),
                label=''
            )
            bw(b, on_activate_call=CallPartial(MiniBrowserWindow, source=b))
            return r
        
        # ===== جایگزینی تابع (مثل zed2.py) =====
        party.PartyWindow.__init__ = patched_init
        
        s._patched = True
        print("✅ Chrome Mini button added (different position than anti-code)")

    def on_app_quit(s):
        try:
            if MiniBrowserWindow._instance:
                MiniBrowserWindow._instance._close()
        except:
            pass