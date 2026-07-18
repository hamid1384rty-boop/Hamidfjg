# ChromeOverlay - کروم روی بازی (با استفاده از WebView اندروید)
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
    get_special_widget as gsw,
    screenmessage as push
)
import os
import threading
import time

# ============================================
# کلاس کروم روی بازی (با WebView اندروید)
# ============================================
class ChromeOverlay:
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
        
        # ===== پنجره اصلی =====
        w = s.w = cw(
            parent=gsw('overlay_stack'),
            size=(600, 450),
            scale=0.9,
            transition='in_scale',
            color=(0.05, 0.05, 0.1)
        )
        
        # عنوان
        tw(
            parent=w,
            text='🌐 Chrome Overlay',
            scale=1.2,
            position=(300, 425),
            h_align='center',
            color=(0.6, 0.8, 1)
        )
        
        # نوار آدرس
        s.url_input = tw(
            parent=w,
            maxwidth=400,
            size=(400, 30),
            editable=True,
            v_align='center',
            color=(0.75, 0.75, 0.75),
            position=(40, 385),
            allow_clear_button=True,
            text='https://bslife.ir'
        )
        
        bw(
            parent=w,
            label='🚀',
            size=(40, 30),
            position=(450, 385),
            on_activate_call=CallStrict(s._open_chrome),
            color=(0.2, 0.4, 0.6)
        )
        
        bw(
            parent=w,
            label='✖',
            size=(30, 30),
            position=(560, 420),
            on_activate_call=CallStrict(s._close),
            color=(0.5, 0.1, 0.1)
        )
        
        # ===== اطلاعات =====
        s.info_text = tw(
            parent=w,
            text='📱 Tap "Open Chrome" to view page\n(Chrome will open as overlay on the game)',
            scale=0.7,
            position=(300, 200),
            h_align='center',
            color=(0.7, 0.7, 0.8)
        )
        
        # دکمه اصلی
        bw(
            parent=w,
            label='🌐 Open Chrome Overlay',
            size=(200, 40),
            position=(200, 150),
            on_activate_call=CallStrict(s._open_chrome),
            color=(0.2, 0.4, 0.6),
            text_scale=0.8
        )
        
        bw(
            parent=w,
            label='❌ Close',
            size=(100, 30),
            position=(480, 20),
            on_activate_call=CallStrict(s._close),
            color=(0.4, 0.1, 0.1),
            text_scale=0.7
        )
        
        cw(w, on_outside_click_call=CallStrict(s._close))
        s._initialized = True
        push('🌐 Chrome Overlay ready!', color=(0, 1, 0))
        
        # ===== تلاش برای راه‌اندازی WebView =====
        s._try_webview()
    
    def _try_webview(s):
        """تلاش برای راه‌اندازی WebView اندروید"""
        try:
            # بررسی وجود jnius (برای اندروید)
            import jnius
            from jnius import autoclass
            
            # کلاس‌های اندروید
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            WebView = autoclass('android.webkit.WebView')
            WebViewClient = autoclass('android.webkit.WebViewClient')
            WebChromeClient = autoclass('android.webkit.WebChromeClient')
            LinearLayout = autoclass('android.widget.LinearLayout')
            ViewGroup = autoclass('android.view.ViewGroup')
            LayoutParams = autoclass('android.view.ViewGroup$LayoutParams')
            
            # ایجاد WebView
            activity = PythonActivity.mActivity
            s.webview = WebView(activity)
            s.webview.getSettings().setJavaScriptEnabled(True)
            s.webview.getSettings().setDomStorageEnabled(True)
            s.webview.getSettings().setAllowFileAccess(True)
            s.webview.getSettings().setLoadWithOverviewMode(True)
            s.webview.getSettings().setUseWideViewPort(True)
            s.webview.setWebViewClient(WebViewClient())
            s.webview.setWebChromeClient(WebChromeClient())
            
            # افزودن به layout
            layout = LinearLayout(activity)
            layout.setOrientation(LinearLayout.VERTICAL)
            
            # پارامترها برای نمایش روی بازی
            params = LayoutParams(
                LayoutParams.MATCH_PARENT,
                LayoutParams.MATCH_PARENT
            )
            
            activity.addContentView(layout, params)
            layout.addView(s.webview, params)
            
            s.webview.loadUrl("https://bslife.ir")
            s._webview_active = True
            
            tw(s.info_text, text='✅ Chrome WebView loaded!\nPage is shown on top of the game')
            push('✅ Chrome WebView loaded successfully!', color=(0, 1, 0))
            
        except Exception as e:
            print(f"WebView error: {e}")
            s._webview_active = False
            tw(s.info_text, text=f'⚠️ WebView not available\nWill open in browser instead\nError: {str(e)[:50]}')
    
    def _open_chrome(s):
        """باز کردن صفحه در کروم"""
        url = tw(query=s.url_input).strip()
        if not url:
            return
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url
        
        push(f'🌐 Opening: {url}', color=(0, 1, 1))
        
        # اگر WebView فعال باشه
        if hasattr(s, '_webview_active') and s._webview_active:
            try:
                s.webview.loadUrl(url)
                tw(s.info_text, text=f'✅ Loading in Chrome overlay: {url}')
                return
            except:
                pass
        
        # روش جایگزین: باز کردن در مرورگر
        try:
            import webbrowser
            webbrowser.open(url)
            tw(s.info_text, text=f'📱 Opened in browser: {url}')
            push(f'📱 Opened in browser', color=(0, 1, 0))
        except:
            push(f'❌ Could not open', color=(1, 0.5, 0))
    
    def _close(s):
        try:
            gs('swish').play()
            
            # بستن WebView
            if hasattr(s, 'webview') and s.webview:
                try:
                    s.webview.destroy()
                except:
                    pass
            
            if hasattr(s, 'w') and s.w:
                cw(s.w, transition='out_scale')
                s.w = None
            s._initialized = False
            ChromeOverlay._instance = None
            push('❌ Chrome overlay closed', color=(1, 0.5, 0))
        except:
            pass

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
class ChromeOverlayPlugin(Plugin):
    def __init__(s):
        from bauiv1lib import party
        
        print("🌐 Chrome Overlay Plugin activated")
        
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
            bw(b, on_activate_call=CallPartial(ChromeOverlay, source=b))
            return r
        
        party.PartyWindow.__init__ = patched_init
        s._patched = True
        print("✅ Chrome Overlay ready!")

    def on_app_quit(s):
        try:
            if ChromeOverlay._instance:
                ChromeOverlay._instance._close()
        except:
            pass