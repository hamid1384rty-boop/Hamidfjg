# minibrowser.py - مرورگر WebView داخل بازی (یک فایل کامل)
# Copyright 2025
# جایگذاری: /Android/data/net.froemling.bombsquad/files/mods/

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
import os
import sys
import json

# ============================================
# تلاش برای import WebView (اگر موجود باشه)
# ============================================
WEBVIEW_AVAILABLE = False
try:
    # بررسی وجود WebView در سیستم
    import jnius
    from jnius import autoclass
    WEBVIEW_AVAILABLE = True
    print("✅ WebView available (Android)")
except:
    print("⚠️ WebView not available, using fallback mode")
    WEBVIEW_AVAILABLE = False

# ============================================
# کلاس WebView اندروید
# ============================================
class AndroidWebView:
    def __init__(s):
        s.webview = None
        s.layout = None
        s.is_active = False
        s.current_url = "https://www.google.com"
        
        if WEBVIEW_AVAILABLE:
            s._init_webview()
    
    def _init_webview(s):
        try:
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            WebView = autoclass('android.webkit.WebView')
            WebViewClient = autoclass('android.webkit.WebViewClient')
            WebChromeClient = autoclass('android.webkit.WebChromeClient')
            LinearLayout = autoclass('android.widget.LinearLayout')
            ViewGroup = autoclass('android.view.ViewGroup')
            LayoutParams = autoclass('android.view.ViewGroup$LayoutParams')
            
            activity = PythonActivity.mActivity
            
            # ایجاد WebView
            s.webview = WebView(activity)
            settings = s.webview.getSettings()
            settings.setJavaScriptEnabled(True)
            settings.setDomStorageEnabled(True)
            settings.setAllowFileAccess(True)
            settings.setAllowContentAccess(True)
            settings.setLoadWithOverviewMode(True)
            settings.setUseWideViewPort(True)
            s.webview.setWebViewClient(WebViewClient())
            s.webview.setWebChromeClient(WebChromeClient())
            
            # ایجاد Layout
            s.layout = LinearLayout(activity)
            s.layout.setOrientation(LinearLayout.VERTICAL)
            
            params = LayoutParams(
                LayoutParams.MATCH_PARENT,
                LayoutParams.MATCH_PARENT
            )
            
            activity.addContentView(s.layout, params)
            s.layout.addView(s.webview, params)
            
            # مخفی کردن در ابتدا
            s.webview.setVisibility(8)  # GONE
            
            s.is_active = False
            print("✅ WebView initialized")
            
        except Exception as e:
            print(f"❌ WebView init error: {e}")
            s.is_active = False
    
    def show(s, url=None):
        """نمایش WebView روی بازی"""
        if not s.webview:
            return False
        
        try:
            if url:
                s.current_url = url
                s.webview.loadUrl(url)
            
            s.webview.setVisibility(0)  # VISIBLE
            s.is_active = True
            print(f"✅ WebView shown: {s.current_url}")
            return True
        except Exception as e:
            print(f"❌ Show error: {e}")
            return False
    
    def hide(s):
        """مخفی کردن WebView"""
        if not s.webview:
            return
        
        try:
            s.webview.setVisibility(8)  # GONE
            s.is_active = False
            print("✅ WebView hidden")
        except Exception as e:
            print(f"❌ Hide error: {e}")
    
    def load_url(s, url):
        """بارگذاری آدرس جدید"""
        if not s.webview:
            return False
        
        try:
            s.current_url = url
            s.webview.loadUrl(url)
            return True
        except Exception as e:
            print(f"❌ Load error: {e}")
            return False
    
    def destroy(s):
        """نابود کردن WebView"""
        try:
            if s.webview:
                s.webview.destroy()
                s.webview = None
            if s.layout:
                s.layout = None
            s.is_active = False
            print("✅ WebView destroyed")
        except Exception as e:
            print(f"❌ Destroy error: {e}")

# ============================================
# کلاس اصلی مرورگر
# ============================================
class MiniBrowser:
    _instance = None
    _webview = None
    
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
        
        # ایجاد WebView اگر موجود باشه
        if WEBVIEW_AVAILABLE and MiniBrowser._webview is None:
            MiniBrowser._webview = AndroidWebView()
        
        # ===== پنجره کنترل =====
        w = s.w = cw(
            parent=gsw('overlay_stack'),
            size=(550, 400),
            scale=0.9,
            transition='in_scale',
            color=(0.05, 0.05, 0.1)
        )
        
        # عنوان
        tw(
            parent=w,
            text='🌐 WebView Browser',
            scale=1.2,
            position=(275, 375),
            h_align='center',
            color=(0.6, 0.8, 1)
        )
        
        # دکمه بستن
        bw(
            parent=w,
            label='✖',
            size=(30, 30),
            position=(520, 370),
            on_activate_call=CallStrict(s._close),
            color=(0.5, 0.1, 0.1),
            text_scale=0.8
        )
        
        # ===== نوار آدرس =====
        tw(
            parent=w,
            text='🔍 URL:',
            scale=0.7,
            position=(20, 335),
            color=(0.6, 0.8, 1)
        )
        
        s.url_input = tw(
            parent=w,
            maxwidth=350,
            size=(350, 30),
            editable=True,
            v_align='center',
            color=(0.75, 0.75, 0.75),
            position=(70, 330),
            allow_clear_button=True,
            text='https://bslife.ir'
        )
        
        # ===== دکمه‌ها =====
        bw(
            parent=w,
            label='🚀 Go',
            size=(60, 30),
            position=(430, 330),
            on_activate_call=CallStrict(s._go),
            color=(0.2, 0.4, 0.6),
            text_scale=0.7
        )
        
        # ===== وضعیت WebView =====
        status_text = "✅ WebView Ready" if WEBVIEW_AVAILABLE else "⚠️ WebView Unavailable\n(Will open in external browser)"
        s.status = tw(
            parent=w,
            text=status_text,
            scale=0.55,
            position=(20, 290),
            color=(0.5, 0.8, 0.5) if WEBVIEW_AVAILABLE else (1, 0.8, 0.5)
        )
        
        # ===== دکمه‌های اصلی =====
        if WEBVIEW_AVAILABLE:
            bw(
                parent=w,
                label='🌐 Show WebView',
                size=(180, 35),
                position=(20, 240),
                on_activate_call=CallStrict(s._show_webview),
                color=(0.2, 0.4, 0.6),
                text_scale=0.7
            )
            
            bw(
                parent=w,
                label='🙈 Hide WebView',
                size=(180, 35),
                position=(210, 240),
                on_activate_call=CallStrict(s._hide_webview),
                color=(0.4, 0.2, 0.2),
                text_scale=0.7
            )
        
        # ===== لینک‌های سریع =====
        tw(
            parent=w,
            text='📌 Quick Links:',
            scale=0.6,
            position=(20, 200),
            color=(0.6, 0.8, 1)
        )
        
        quick_links = [
            ('Google', 'https://www.google.com'),
            ('BSLIFE', 'https://bslife.ir'),
            ('Github', 'https://www.github.com'),
            ('Wiki', 'https://www.wikipedia.org')
        ]
        
        x_pos = 20
        y_pos = 180
        for label, url in quick_links:
            bw(
                parent=w,
                label=label,
                size=(80, 25),
                position=(x_pos, y_pos),
                on_activate_call=CallStrict(s._quick_open, url),
                color=(0.1, 0.15, 0.2),
                text_scale=0.6
            )
            x_pos += 90
            if x_pos > 400:
                x_pos = 20
                y_pos -= 35
        
        # ===== دکمه بستن =====
        bw(
            parent=w,
            label='❌ Close Browser',
            size=(120, 30),
            position=(410, 20),
            on_activate_call=CallStrict(s._close),
            color=(0.4, 0.1, 0.1),
            text_scale=0.7
        )
        
        cw(w, on_outside_click_call=CallStrict(s._close))
        s._initialized = True
        push('🌐 Browser opened!', color=(0, 1, 0))
    
    def _go(s):
        """رفتن به آدرس"""
        url = tw(query=s.url_input).strip()
        if url:
            if not url.startswith('http://') and not url.startswith('https://'):
                url = 'https://' + url
            s._load_url(url)
    
    def _load_url(s, url):
        """بارگذاری آدرس"""
        tw(s.url_input, text=url)
        push(f'🌐 Loading: {url}', color=(0, 1, 1))
        
        if WEBVIEW_AVAILABLE and MiniBrowser._webview:
            MiniBrowser._webview.load_url(url)
            tw(s.status, text=f'✅ Loading in WebView: {url}')
        else:
            # روش جایگزین: باز کردن در مرورگر
            try:
                import webbrowser
                webbrowser.open(url)
                tw(s.status, text=f'📱 Opened in external browser: {url}')
                push(f'📱 Opened in browser', color=(0, 1, 0))
            except Exception as e:
                tw(s.status, text=f'❌ Error: {str(e)}')
                push(f'❌ Error: {str(e)}', color=(1, 0.5, 0))
    
    def _quick_open(s, url):
        """باز کردن سریع"""
        s._load_url(url)
    
    def _show_webview(s):
        """نمایش WebView روی بازی"""
        if WEBVIEW_AVAILABLE and MiniBrowser._webview:
            url = tw(query=s.url_input).strip()
            if MiniBrowser._webview.show(url):
                tw(s.status, text=f'✅ WebView shown: {url}')
                push('🌐 WebView displayed on game!', color=(0, 1, 0))
            else:
                tw(s.status, text='❌ Failed to show WebView')
                push('❌ Failed to show WebView', color=(1, 0.5, 0))
        else:
            tw(s.status, text='⚠️ WebView not available')
            push('⚠️ WebView not available', color=(1, 0.8, 0))
    
    def _hide_webview(s):
        """مخفی کردن WebView"""
        if WEBVIEW_AVAILABLE and MiniBrowser._webview:
            MiniBrowser._webview.hide()
            tw(s.status, text='🙈 WebView hidden')
            push('🙈 WebView hidden', color=(1, 0.8, 0))
    
    def _close(s):
        """بستن کامل"""
        try:
            # مخفی کردن WebView
            if WEBVIEW_AVAILABLE and MiniBrowser._webview:
                MiniBrowser._webview.hide()
            
            gs('swish').play()
            if hasattr(s, 'w') and s.w:
                cw(s.w, transition='out_scale')
                s.w = None
            s._initialized = False
            MiniBrowser._instance = None
            push('❌ Browser closed', color=(1, 0.5, 0))
        except Exception as e:
            print(f"Close error: {e}")

# ============================================
# کلاس دکمه
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
        
        print("🌐 WebView Browser Plugin activated")
        print(f"📁 WebView available: {WEBVIEW_AVAILABLE}")
        
        original_init = party.PartyWindow.__init__
        
        def patched_init(self, *a, **k):
            r = original_init(self, *a, **k)
            
            b = SC.bw(
                icon=gt('achievementCrossHair'),
                position=(self._width - 495, self._height - 300),
                parent=self._root_widget,
                iconscale=1.2,
                size=(30, 30),
                label=''
            )
            bw(b, on_activate_call=CallPartial(MiniBrowser, source=b))
            return r
        
        party.PartyWindow.__init__ = patched_init
        s._patched = True
        print("✅ Browser ready!")

    def on_app_quit(s):
        try:
            if MiniBrowser._instance:
                MiniBrowser._instance._close()
            if MiniBrowser._webview:
                MiniBrowser._webview.destroy()
        except:
            pass