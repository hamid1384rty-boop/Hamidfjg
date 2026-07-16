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
        # پاک کردن محتوای قبلی
        for child in s.content_container.get_children():
            child.delete()
        
        try:
            # ارسال درخواست
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode('utf-8', errors='ignore')
                
                # نمایش عنوان صفحه
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
                
                # نمایش محتوای متنی ساده
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
                
                # نمایش لینک‌ها
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
                
                # اگر چیزی پیدا نشد
                if not title and not text_content:
                    tw(
                        parent=s.content_container,
                        text='✅ صفحه با موفقیت بارگذاری شد\n(محتوا قابل نمایش نیست)',
                        scale=0.8,
                        position=(220, 120),
                        h_align='center',
                        color=(0.6, 1, 0.6)
                    )
                
                # پیام موفقیت
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
        """استخراج عنوان صفحه از HTML"""
        try:
            start = html.find('<title>')
            if start != -1:
                end = html.find('</title>', start)
                if end != -1:
                    title = html[start+7:end].strip()
                    return title
        except:
            pass
        return None
    
    def _extract_text(s, html):
        """استخراج متن از HTML"""
        try:
            # حذف تگ‌ها
            import re
            text = re.sub(r'<[^>]+>', ' ', html)
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
            return text
        except:
            return None
    
    def _extract_links(s, html):
        """استخراج لینک‌ها از HTML"""
        links = []
        try:
            import re
            # پیدا کردن لینک‌های a
            pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>'
            matches = re.findall(pattern, html, re.IGNORECASE)
            for url, text in matches[:10]:
                if url.startswith('/'):
                    # تبدیل لینک نسبی به کامل
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
        """بستن پنجره"""
        try:
            gs('swish').play()
            if hasattr(s, 'w') and s.w:
                cw(s.w, transition='out_scale')
                s.w = None
        except:
            pass

# ============================================
# کلاس دکمه در صفحه چت
# ============================================
class ChatButton:
    def __init__(s):
        # پیدا کردن صفحه چت
        s._inject_button()
        
        # بررسی دوره‌ای برای تزریق مجدد
        teck(2, CallStrict(s._check_inject))
    
    def _check_inject(s):
        """بررسی دوره‌ای برای تزریق دکمه"""
        s._inject_button()
        teck(2, CallStrict(s._check_inject))
    
    def _inject_button(s):
        """تزریق دکمه به صفحه چت"""
        try:
            # پیدا کردن ویجت چت
            chat_widget = gsw('chat_input')
            if not chat_widget:
                return
            
            # بررسی اینکه دکمه قبلاً اضافه شده
            if hasattr(s, '_btn_added') and s._btn_added:
                return
            
            # ایجاد دکمه مرورگر
            btn = bw(
                parent=chat_widget,
                label='🌐',
                size=(35, 35),
                position=(0, -40),  # بالای دکمه ارسال
                on_activate_call=CallPartial(MiniBrowser),
                color=(0.2, 0.3, 0.5),
                text_scale=0.8
            )
            
            s._btn_added = True
            print("✅ MiniBrowser button added to chat")
            
        except Exception as e:
            print(f"Error injecting button: {e}")
    
    def _remove_button(s):
        """حذف دکمه (در صورت نیاز)"""
        try:
            if hasattr(s, '_btn') and s._btn:
                s._btn.delete()
                s._btn = None
                s._btn_added = False
        except:
            pass

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
        print("🌐 MiniBrowser Plugin activated")
        
        # تنظیمات
        s.chat_button = None
        
        # تزریق دکمه بعد از بارگذاری کامل
        teck(1, CallStrict(s._init_button))
    
    def _init_button(s):
        """راه‌اندازی دکمه"""
        try:
            s.chat_button = ChatButton()
            print("✅ MiniBrowser ready")
        except Exception as e:
            print(f"Error initializing button: {e}")
            teck(2, CallStrict(s._init_button))
    
    def on_app_quit(s):
        """هنگام خروج برنامه"""
        try:
            if hasattr(s, 'chat_button') and s.chat_button:
                s.chat_button._remove_button()
        except:
            pass