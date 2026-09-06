# -*- coding: utf-8 -*-
# ==========================================================
# سیستم اشتراک‌گذاری سوسولی پلاس - نسخه اصلاح‌شده (API 9)
# رفع مشکل عدم نمایش پنل + مقیاس + شبکه غیرهمگام
# ==========================================================

from __future__ import annotations

import json
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

import babase
from babase import AppTimer, Call, CallPartial, CallStrict, Plugin, pushcall
from bauiv1 import (
    apptimer as teck,
    buttonwidget as bw,
    columnwidget as clw,
    containerwidget as cw,
    getsound as gs,
    gettexture as gt,
    scrollwidget as sw,
    screenmessage as push,
    textwidget as tw,
)

try:
    from bauiv1 import get_special_widget as gsw
except Exception:
    gsw = None

# فقط get_game_roster لازم است (توابع چت در API 9 حذف شده‌اند)
from bascenev1 import get_game_roster

# ==========================================================
# تنظیمات
# ==========================================================

WORKER_URL = "https://soft-cloud-613d.hamid1384098.workers.dev"
SYSTEM_NAME = "سوسولی پلاس"
ADMIN_PASSWORD = "uagugauaa1384rty"
CONNECT_TIMEOUT = 10

# ==========================================================
# اجرای غیرهمگام شبکه (رفع فریز UI)
# ==========================================================

class Net:
    @staticmethod
    def run(func, callback):
        def _work():
            try:
                result = func()
            except Exception as exc:
                result = {'error': 'exception: %s' % exc}
            try:
                pushcall(CallStrict(callback, result), from_other_thread=True)
            except Exception:
                pass
        threading.Thread(target=_work, daemon=True).start()

# ==========================================================
# بخش 1: تشخیص اطلاعات بازیکن
# ==========================================================

class GameDetector:
    @staticmethod
    def get_account_id():
        # 1) حساب رسمی بمب‌اسکواد (آیدی واقعی - خودکار)
        try:
            plus = babase.app.plus
            if plus is not None:
                state = str(plus.get_v1_account_state())
                if 'SIGNED_IN' in state.upper():
                    try:
                        aid = plus.get_v1_account_id()
                        if aid:
                            return str(aid)
                    except Exception:
                        pass
                    try:
                        name = plus.get_v1_account_name()
                        if name:
                            return str(name)
                    except Exception:
                        pass
        except Exception:
            pass
        # 2) از لیست بازیکنان جلسه فعلی
        try:
            nickname = GameDetector.get_nickname()
            for client in get_game_roster():
                for p in client.get('players', []):
                    if p.get('name') == nickname:
                        aid = client.get('account_id')
                        if aid:
                            return str(aid)
                        cid = client.get('client_id', -1)
                        if cid != -1:
                            return 'client_%s' % cid
        except Exception:
            pass
        # 3) نام پروفایل به عنوان آخرین راه
        try:
            name = babase.app.config.get('Player Name')
            if name:
                return str(name)
        except Exception:
            pass
        return 'Unknown'

    @staticmethod
    def get_nickname():
        try:
            name = babase.app.config.get('Player Name')
            if name:
                return str(name)
        except Exception:
            pass
        try:
            for client in get_game_roster():
                for p in client.get('players', []):
                    if p.get('name'):
                        return str(p.get('name'))
        except Exception:
            pass
        return 'Unknown'

    @staticmethod
    def get_special_name():
        try:
            nickname = GameDetector.get_nickname()
            for client in get_game_roster():
                for p in client.get('players', []):
                    if p.get('name') == nickname:
                        special = client.get('display_string')
                        if special:
                            return str(special)
        except Exception:
            pass
        return GameDetector.get_nickname()

# ==========================================================
# بخش 2: مدیریت اشتراک‌ها (ظرفیت‌محور)
# ==========================================================

class SubscriptionManager:
    WORKER_URL = WORKER_URL
    _cache = {}
    _cache_time = {}
    CACHE_DURATION = 30

    @staticmethod
    def _make_request(endpoint, data=None, method='GET'):
        url = WORKER_URL + endpoint
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
        }
        try:
            try:
                ctx = ssl.create_default_context()
            except Exception:
                ctx = ssl._create_unverified_context()

            if method == 'GET' and data:
                params = '&'.join(
                    '%s=%s' % (k, urllib.parse.quote(str(v))) for k, v in data.items()
                )
                url = '%s?%s' % (url, params)
                req = urllib.request.Request(url, headers=headers)
            elif method in ('POST', 'PUT', 'DELETE'):
                req = urllib.request.Request(
                    url,
                    data=json.dumps(data).encode('utf-8'),
                    headers=headers,
                    method=method,
                )
            else:
                req = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(req, timeout=CONNECT_TIMEOUT, context=ctx) as response:
                return json.loads(response.read().decode('utf-8'))

        except urllib.error.HTTPError as e:
            try:
                return json.loads(e.read().decode('utf-8'))
            except Exception:
                return {'error': 'HTTP %s' % e.code}
        except Exception as e:
            return {'error': str(e), 'code': 'CONNECTION_ERROR'}

    @staticmethod
    def _get_cached(key):
        if key in SubscriptionManager._cache:
            if time.time() - SubscriptionManager._cache_time.get(key, 0) < SubscriptionManager.CACHE_DURATION:
                return SubscriptionManager._cache[key]
        return None

    @staticmethod
    def _set_cached(key, value):
        SubscriptionManager._cache[key] = value
        SubscriptionManager._cache_time[key] = time.time()

    @classmethod
    def get_capacity_info(cls):
        cached = cls._get_cached('capacity')
        if cached is not None:
            return cached
        result = cls._make_request('/api/subs/capacity')
        cls._set_cached('capacity', result)
        return result

    @classmethod
    def get_my_subscription(cls, account_id=None):
        if not account_id or account_id == 'Unknown':
            account_id = GameDetector.get_account_id()
        return cls._make_request('/api/subs/my', {'account_id': account_id})

    @classmethod
    def connect_to_subscription(cls, special_name, account_id=None, nickname=None, client_id=None):
        if not account_id or account_id == 'Unknown':
            account_id = GameDetector.get_account_id()
        if not nickname:
            nickname = GameDetector.get_nickname()
        result = cls._make_request(
            '/api/subs/connect',
            {
                'account_id': account_id,
                'nickname': nickname,
                'special_name': special_name,
                'client_id': client_id if client_id is not None else -1,
            },
            'POST',
        )
        cls._cache = {}
        return result

    @classmethod
    def disconnect_subscription(cls, account_id=None):
        if not account_id or account_id == 'Unknown':
            account_id = GameDetector.get_account_id()
        result = cls._make_request(
            '/api/subs/disconnect', {'account_id': account_id}, 'POST'
        )
        cls._cache = {}
        return result

    @classmethod
    def get_chat_messages(cls, account_id=None, limit=50):
        if not account_id or account_id == 'Unknown':
            account_id = GameDetector.get_account_id()
        return cls._make_request(
            '/api/subs/chat/get', {'account_id': account_id, 'limit': limit}
        )

    @classmethod
    def send_chat_message(cls, message, account_id=None):
        if not account_id or account_id == 'Unknown':
            account_id = GameDetector.get_account_id()
        return cls._make_request(
            '/api/subs/chat/send',
            {'account_id': account_id, 'message': message},
            'POST',
        )

    @classmethod
    def update_online_status(cls, is_online=True, account_id=None):
        if not account_id or account_id == 'Unknown':
            account_id = GameDetector.get_account_id()
        return cls._make_request(
            '/api/subs/status',
            {'account_id': account_id, 'is_online': is_online},
            'POST',
        )

    @classmethod
    def get_all_subscriptions(cls, password):
        return cls._make_request(
            '/api/subs', {'password': password, 'account_id': GameDetector.get_account_id()}
        )

# ==========================================================
# بخش 3: ابزارهای UI
# ==========================================================

class SubUI:
    @staticmethod
    def UIS():
        u = ''
        try:
            u = str(babase.app.ui_v1.uiscale).lower()
        except Exception:
            u = ''
        if 'large' in u:
            return 1.2
        if 'medium' in u:
            return 1.0
        if 'small' in u:
            return 0.8
        return 1.0

    @staticmethod
    def overlay_stack():
        try:
            if gsw is not None:
                return gsw('overlay_stack')
        except Exception:
            pass
        return None

    @staticmethod
    def bw(**k):
        kwargs = dict(k)
        kwargs.setdefault('textcolor', (1, 1, 1))
        kwargs.setdefault('enable_sound', False)
        kwargs.setdefault('button_type', 'square')
        kwargs.setdefault('color', (0.18, 0.18, 0.18))
        return bw(**kwargs)

    @staticmethod
    def cw(source, **k):
        o = None
        try:
            if source is not None:
                o = source.get_screen_space_center()
        except Exception:
            o = None
        kwargs = dict(k)
        scale = SubUI.UIS()
        filtered = {}
        for key, value in kwargs.items():
            if key not in ('parent', 'scale_origin_stack_offset', 'scale', 'transition', 'color'):
                filtered[key] = value
        r = cw(
            parent=SubUI.overlay_stack(),
            scale_origin_stack_offset=o,
            scale=scale,
            transition='in_scale',
            color=(0.18, 0.18, 0.18),
            **filtered
        )
        cw(r, on_outside_click_call=CallPartial(SubUI.swish, r))
        return r

    @staticmethod
    def swish(t=None):
        try:
            gs('swish').play()
        except Exception:
            pass
        if t is not None:
            try:
                cw(t, transition='out_scale')
            except Exception:
                pass

    @staticmethod
    def err(t):
        try:
            gs('block').play()
        except Exception:
            pass
        push(str(t), color=(1, 1, 0))

    @staticmethod
    def ok():
        try:
            gs('dingSmallHigh').play()
        except Exception:
            pass
        push('Success!', color=(0, 1, 0))

    @staticmethod
    def get_text(widget):
        try:
            return tw(query=widget).text or ''
        except Exception:
            return ''

    @staticmethod
    def set_text(widget, text):
        try:
            tw(widget, text=text)
        except Exception:
            pass

# ==========================================================
# بخش 4: پنل‌ها
# ==========================================================

class MainPanel:
    def __init__(self, source, data=None):
        self.source = source
        try:
            SubUI.swish(getattr(self, 'w', None))
        except Exception:
            pass

        if data is None:
            self._show_loading()
            return
        self._build(data)

    def _show_loading(self):
        w = self.w = SubUI.cw(source=self.source, size=(420, 190))
        tw(
            parent=w, text='🔑 ' + SYSTEM_NAME, scale=1.2,
            position=(210, 155), h_align='center', color=(0.8, 0.6, 0.2)
        )
        tw(
            parent=w, text='⏳ در حال دریافت اطلاعات...',
            position=(210, 95), h_align='center', scale=0.85, color=(0.7, 0.7, 0.9)
        )
        SubUI.bw(
            parent=w, label='✖ بستن', size=(80, 30), position=(330, 10),
            on_activate_call=CallPartial(SubUI.swish, w), color=(0.3, 0.1, 0.1)
        )
        SubUI.swish()
        Net.run(self._fetch_data, self._on_data)

    @staticmethod
    def _fetch_data():
        cap = SubscriptionManager.get_capacity_info()
        my = SubscriptionManager.get_my_subscription(GameDetector.get_account_id())
        return {'capacity': cap, 'my': my}

    def _on_data(self, result):
        if isinstance(result, dict) and 'capacity' in result:
            SubUI.swish(getattr(self, 'w', None))
            teck(0.12, CallStrict(MainPanel, self.source, result))
        else:
            msg = result.get('error', 'خطا در ارتباط با سرور') if isinstance(result, dict) else 'خطا در ارتباط با سرور'
            SubUI.err('❌ ' + str(msg))

    def _build(self, data):
        capacity_info = data.get('capacity', {}) if isinstance(data, dict) else {}
        my_sub = data.get('my', {}) if isinstance(data, dict) else {}

        total = capacity_info.get('total_subscriptions', 0) if isinstance(capacity_info, dict) else 0
        used = capacity_info.get('used_capacity', 0) if isinstance(capacity_info, dict) else 0
        remaining = capacity_info.get('remaining_capacity', 0) if isinstance(capacity_info, dict) else 0

        has_subscription = isinstance(my_sub, dict) and 'subscription' in my_sub and 'error' not in my_sub

        # افزایش ارتفاع پنل برای دکمه ثبت‌نام
        h = 620 if has_subscription else 560
        w = self.w = SubUI.cw(source=self.source, size=(430, h))

        tw(parent=w, text='🔑 ' + SYSTEM_NAME, scale=1.2,
           position=(215, h - 35), h_align='center', color=(0.8, 0.6, 0.2))
        tw(parent=w, text='🆔 آیدی: %s' % GameDetector.get_account_id(),
           position=(20, h - 65), scale=0.75, color=(0.6, 0.8, 1), maxwidth=390)
        tw(parent=w, text='👤 اسم خاص: %s' % GameDetector.get_special_name(),
           position=(20, h - 90), scale=0.75, color=(0.8, 0.8, 1), maxwidth=390)

        cap_bg = cw(
            parent=w, size=(410, 80), position=(10, h - 200),
            color=(0.12, 0.15, 0.2), border=2, border_color=(0.3, 0.5, 0.8)
        )
        tw(parent=cap_bg, text='📊 وضعیت ظرفیت اشتراک‌ها',
           position=(205, 55), h_align='center', scale=0.75, color=(0.6, 0.8, 1))
        tw(parent=cap_bg, text='📦 کل: %s' % total,
           position=(15, 25), scale=0.7, color=(0.8, 0.8, 0.8))
        tw(parent=cap_bg, text='🔴 استفاده: %s' % used,
           position=(135, 25), scale=0.7, color=(1, 0.5, 0.5))
        remain_color = (0.5, 1, 0.5) if remaining > 0 else (1, 0.3, 0.3)
        tw(parent=cap_bg, text='🟢 باقی: %s' % remaining,
           position=(280, 25), scale=0.7, color=remain_color)

        if not has_subscription:
            tw(parent=w, text='❌ شما به اشتراکی متصل نیستید',
               position=(215, h - 225), h_align='center', scale=0.75, color=(1, 0.5, 0))
        else:
            sub_data = my_sub.get('subscription', {})
            tw(parent=w, text='✅ متصل به: %s' % sub_data.get('name', 'Unknown'),
               position=(215, h - 225), h_align='center', scale=0.8, color=(0, 1, 0.5))
            remain_text = MainPanel.format_remaining(sub_data.get('remaining', {}))
            tw(parent=w, text='⏱️ %s' % remain_text,
               position=(215, h - 250), h_align='center', scale=0.7, color=(1, 0.8, 0.2))

        scroll = sw(parent=w, size=(410, h - 380), position=(10, 55),
                    color=(0.1, 0.1, 0.1), highlight=False)
        column = clw(parent=scroll, left_border=10, top_border=10, bottom_border=10)

        btn_y = 0
        btn_h = 42

        if not has_subscription:
            if remaining > 0:
                SubUI.bw(
                    parent=column, label='🔗 ثبت‌نام با اسم خاص (اتصال خودکار)',
                    size=(380, btn_h), position=(0, btn_y),
                    on_activate_call=CallStrict(self._show_connect),
                    color=(0.1, 0.4, 0.1)
                )
                tw(parent=column, text='✅ فقط اسم خاص خود را وارد کنید، سیستم به صورت خودکار وصل میشود',
                   position=(190, btn_y - 15), h_align='center', scale=0.55, color=(0.5, 0.8, 0.5))
                btn_y += btn_h + 30
            else:
                tw(parent=column, text='⛔ ظرفیت تکمیل است! لطفا با ادمین تماس بگیرید',
                   position=(190, btn_y + 10), h_align='center', color=(1, 0.3, 0.3))
                btn_y += btn_h + 5
        else:
            SubUI.bw(
                parent=column, label='💬 چت اشتراک',
                size=(380, btn_h), position=(0, btn_y),
                on_activate_call=CallStrict(self._show_chat),
                color=(0.1, 0.3, 0.2)
            )
            btn_y += btn_h + 5
            SubUI.bw(
                parent=column, label='🚪 قطع اتصال',
                size=(380, btn_h), position=(0, btn_y),
                on_activate_call=CallStrict(self._disconnect),
                color=(0.3, 0.1, 0.1)
            )
            btn_y += btn_h + 5

        SubUI.bw(
            parent=column, label='⚙️ پنل مدیریت (نیاز به رمز)',
            size=(380, btn_h), position=(0, btn_y),
            on_activate_call=CallStrict(self._show_admin_login),
            color=(0.2, 0.1, 0.3)
        )
        btn_y += btn_h + 5

        SubUI.bw(
            parent=w, label='✖ بستن', size=(80, 30), position=(340, 10),
            on_activate_call=CallPartial(SubUI.swish, w), color=(0.3, 0.1, 0.1)
        )
        SubUI.swish()

    @staticmethod
    def format_remaining(remaining):
        if not isinstance(remaining, dict) or remaining.get('totalSeconds', 0) <= 0:
            return 'منقضی شده'
        parts = []
        if remaining.get('days', 0) > 0:
            parts.append('%d روز' % remaining['days'])
        if remaining.get('hours', 0) > 0:
            parts.append('%d ساعت' % remaining['hours'])
        if remaining.get('minutes', 0) > 0:
            parts.append('%d دقیقه' % remaining['minutes'])
        return ' '.join(parts) if parts else 'کمتر از یک دقیقه'

    def _show_connect(self):
        SubUI.swish(self.w)
        teck(0.1, CallStrict(ConnectPanel, self.source))

    def _show_admin_login(self):
        SubUI.swish(self.w)
        teck(0.1, CallStrict(AdminLoginPanel, self.source))

    def _show_chat(self):
        SubUI.swish(self.w)
        teck(0.1, CallStrict(ChatPanel, self.source))

    def _disconnect(self):
        push('⏳ در حال قطع اتصال...', color=(1, 1, 0))
        Net.run(self._do_disconnect, self._on_disconnect)

    @staticmethod
    def _do_disconnect():
        return SubscriptionManager.disconnect_subscription(GameDetector.get_account_id())

    def _on_disconnect(self, result):
        if isinstance(result, dict) and result.get('success'):
            SubUI.ok()
            push('✅ اتصال شما قطع شد', color=(1, 0.5, 0))
            SubUI.swish(getattr(self, 'w', None))
            teck(0.3, CallStrict(MainPanel, self.source))
        else:
            msg = result.get('error', 'خطا') if isinstance(result, dict) else 'خطا'
            SubUI.err('❌ ' + str(msg))


class ConnectPanel:
    def __init__(self, source):
        self.source = source
        try:
            SubUI.swish(getattr(self, 'w', None))
        except Exception:
            pass

        self.account_id = GameDetector.get_account_id()

        w = self.w = SubUI.cw(source=source, size=(420, 280))

        tw(parent=w, text='🔗 ثبت‌نام در اشتراک', scale=1.2,
           position=(210, 250), h_align='center', color=(0.8, 0.6, 0.2))
        
        tw(parent=w, text='📌 کافیست اسم خاص خود را وارد کنید',
           position=(210, 220), h_align='center', scale=0.8, color=(0.5, 0.8, 0.5))
        tw(parent=w, text='سیستم به صورت خودکار شما را به یک اشتراک خالی متصل میکند',
           position=(210, 195), h_align='center', scale=0.7, color=(0.6, 0.6, 0.8))
        
        tw(parent=w, text='👤 اسم خاص شما (همان نام بازیکن):',
           position=(20, 160), scale=0.8, color=(0.8, 0.8, 1))

        current_special = GameDetector.get_special_name()
        self.special_input = tw(
            parent=w, maxwidth=250, size=(250, 32), editable=True,
            v_align='center', color=(0.75, 0.75, 0.75), position=(20, 125),
            allow_clear_button=False, text=current_special
        )

        SubUI.bw(
            parent=w, label='✅ ثبت‌نام و اتصال', size=(130, 35), position=(270, 122),
            on_activate_call=CallStrict(self._connect), color=(0.1, 0.4, 0.1)
        )

        tw(parent=w, text='💡 توجه: اگر اسم خاص شما قبلاً ثبت شده باشد،',
           position=(210, 80), h_align='center', scale=0.6, color=(0.8, 0.6, 0.3))
        tw(parent=w, text='به همان اشتراک قبلی متصل خواهید شد',
           position=(210, 58), h_align='center', scale=0.6, color=(0.8, 0.6, 0.3))

        SubUI.bw(
            parent=w, label='↩ بازگشت', size=(100, 30), position=(20, 15),
            on_activate_call=CallPartial(self._close), color=(0.2, 0.2, 0.3)
        )
        SubUI.swish()

    def _connect(self):
        special_name = SubUI.get_text(self.special_input).strip()
        if not special_name:
            SubUI.err('⚠️ لطفاً اسم خاص خود را وارد کنید!')
            return
        
        push('⏳ در حال ثبت‌نام و اتصال...', color=(1, 1, 0))
        Net.run(
            CallPartial(SubscriptionManager.connect_to_subscription, special_name),
            self._on_connect,
        )

    def _on_connect(self, result):
        if isinstance(result, dict) and result.get('success'):
            sub_name = result.get('subscription_name', 'اشتراک')
            SubUI.ok()
            push('✅ ثبت‌نام با موفقیت انجام شد!', color=(0, 1, 0))
            push('🔗 به اشتراک "%s" متصل شدید!' % sub_name, color=(0.5, 0.8, 1))
            push('👤 اسم خاص شما: %s' % GameDetector.get_special_name(), color=(0.8, 0.8, 0.5))
            self._close()
            teck(0.4, CallStrict(MainPanel, self.source))
        else:
            msg = result.get('error', 'خطا در اتصال') if isinstance(result, dict) else 'خطا در اتصال'
            SubUI.err('❌ ' + str(msg))
            if 'ظرفیت' in str(msg) or 'خالی' in str(msg):
                push('💡 هیچ اشتراک خالی موجود نیست، با ادمین تماس بگیرید', color=(1, 0.8, 0))
            elif 'قبلاً' in str(msg):
                push('💡 شما قبلاً به اشتراکی متصل هستید', color=(1, 0.8, 0))

    def _close(self):
        SubUI.swish(getattr(self, 'w', None))


class AdminLoginPanel:
    def __init__(self, source):
        self.source = source
        try:
            SubUI.swish(getattr(self, 'w', None))
        except Exception:
            pass

        w = self.w = SubUI.cw(source=source, size=(350, 220))

        tw(parent=w, text='⚙️ ورود به پنل مدیریت', scale=1.1,
           position=(175, 190), h_align='center', color=(0.8, 0.6, 0.2))
        tw(parent=w, text='رمز مدیریت را وارد کنید:',
           position=(20, 150), scale=0.8, color=(0.8, 0.8, 1))

        self.password_input = tw(
            parent=w, maxwidth=240, size=(240, 32), editable=True,
            v_align='center', color=(0.75, 0.75, 0.75), position=(20, 115),
            allow_clear_button=False, text=''
        )

        SubUI.bw(
            parent=w, label='✅ ورود', size=(100, 35), position=(225, 112),
            on_activate_call=CallStrict(self._check_password), color=(0.1, 0.3, 0.1)
        )
        SubUI.bw(
            parent=w, label='↩ بازگشت', size=(100, 30), position=(20, 15),
            on_activate_call=CallPartial(self._close), color=(0.2, 0.2, 0.3)
        )
        SubUI.swish()

    def _check_password(self):
        password = SubUI.get_text(self.password_input).strip()
        if not password:
            SubUI.err('⚠️ رمز را وارد کنید!')
            return
        if password == ADMIN_PASSWORD:
            SubUI.ok()
            push('✅ رمز صحیح!', color=(0, 1, 0))
            self._close()
            teck(0.3, CallStrict(AdminPanel, self.source))
        else:
            SubUI.err('❌ رمز اشتباه!')

    def _close(self):
        SubUI.swish(getattr(self, 'w', None))


class ChatPanel:
    def __init__(self, source, data=None):
        self.source = source
        self.account_id = GameDetector.get_account_id()
        self.special_name = GameDetector.get_special_name()
        self._alive = True
        self._busy = False
        self._timer = None
        self.chat_data = {'chat': []}

        try:
            SubUI.swish(getattr(self, 'w', None))
        except Exception:
            pass

        if data is None:
            self._show_loading()
            return
        self._build(data)

    def _show_loading(self):
        w = self.w = SubUI.cw(source=self.source, size=(420, 190))
        tw(parent=w, text='💬 چت اشتراک', scale=1.2,
           position=(210, 155), h_align='center', color=(0.8, 0.6, 0.2))
        tw(parent=w, text='⏳ در حال دریافت پیام‌ها...',
           position=(210, 95), h_align='center', scale=0.85, color=(0.7, 0.7, 0.9))
        SubUI.bw(
            parent=w, label='↩ بازگشت', size=(100, 30), position=(20, 15),
            on_activate_call=CallPartial(self._close), color=(0.2, 0.2, 0.3)
        )
        SubUI.swish()
        Net.run(
            CallPartial(SubscriptionManager.get_chat_messages, self.account_id),
            self._on_loaded,
        )

    def _on_loaded(self, result):
        if isinstance(result, dict) and 'chat' in result:
            SubUI.swish(getattr(self, 'w', None))
            teck(0.12, CallStrict(ChatPanel, self.source, result))
        else:
            msg = result.get('error', 'خطا در دریافت پیام‌ها') if isinstance(result, dict) else 'خطا در دریافت پیام‌ها'
            SubUI.err('❌ ' + str(msg))

    def _build(self, data):
        self.chat_data = data if isinstance(data, dict) else {'chat': []}

        w = self.w = SubUI.cw(source=self.source, size=(500, 460))

        tw(parent=w, text='💬 چت اشتراک', scale=1.2,
           position=(250, 430), h_align='center', color=(0.8, 0.6, 0.2))

        self._render_messages()

        self.input_field = tw(
            parent=w, maxwidth=330, size=(330, 32), editable=True,
            v_align='center', color=(0.75, 0.75, 0.75), position=(20, 50),
            allow_clear_button=False, text='پیام...'
        )

        SubUI.bw(
            parent=w, label='📤 ارسال', size=(80, 32), position=(360, 50),
            on_activate_call=CallStrict(self._send_message), color=(0.1, 0.3, 0.1)
        )
        SubUI.bw(
            parent=w, label='↩ بازگشت', size=(100, 30), position=(20, 10),
            on_activate_call=CallPartial(self._close), color=(0.2, 0.2, 0.3)
        )

        try:
            self._timer = AppTimer(3.0, CallStrict(self._refresh_tick), repeat=True)
        except TypeError:
            self._timer = AppTimer(3.0, CallStrict(self._refresh_tick))

        SubUI.swish()

    def _render_messages(self):
        try:
            if getattr(self, 'msg_scroll', None) is not None:
                self.msg_scroll.delete()
        except Exception:
            pass

        self.msg_scroll = sw(
            parent=self.w, size=(460, 320), position=(20, 100),
            color=(0.05, 0.05, 0.05), highlight=False
        )
        self.msg_col = clw(parent=self.msg_scroll, left_border=5,
                           right_border=5, top_border=5, bottom_border=5)

        chat_list = self.chat_data.get('chat', []) if isinstance(self.chat_data, dict) else []
        if not chat_list:
            tw(parent=self.msg_col, text='💬 پیامی نیست',
               position=(230, 150), h_align='center', color=(0.5, 0.5, 0.5))
            return

        line_h = 24
        y = 10
        for msg in chat_list:
            sender = msg.get('sender_special_name') or msg.get('sender_nickname') or 'Unknown'
            message = msg.get('message', '')
            ts = msg.get('timestamp', 0)
            try:
                time_str = time.strftime('%H:%M', time.localtime(ts / 1000))
            except Exception:
                time_str = '--:--'

            color = (0.6, 1, 0.6) if sender == self.special_name else (0.8, 0.8, 1)
            tw(parent=self.msg_col, text='%s [%s]:' % (sender, time_str),
               position=(5, y), scale=0.65, color=color, maxwidth=130)
            tw(parent=self.msg_col, text=str(message),
               position=(145, y), scale=0.65, color=(0.9, 0.9, 0.9), maxwidth=300)
            y += line_h

        col_h = max(310, y + 10)
        try:
            cw(self.msg_col, size=(450, col_h))
        except Exception:
            pass

    def _send_message(self):
        message = SubUI.get_text(self.input_field).strip()
        if not message or message == 'پیام...':
            SubUI.err('⚠️ پیام را وارد کنید!')
            return
        self._busy = True
        Net.run(
            CallPartial(SubscriptionManager.send_chat_message, message, self.account_id),
            self._on_sent,
        )

    def _on_sent(self, result):
        self._busy = False
        if isinstance(result, dict) and result.get('success'):
            SubUI.set_text(self.input_field, '')
            self._refresh_tick()
        else:
            msg = result.get('error', 'خطا در ارسال') if isinstance(result, dict) else 'خطا در ارسال'
            SubUI.err('❌ ' + str(msg))

    def _refresh_tick(self):
        if not self._alive or self._busy:
            return
        self._busy = True
        Net.run(
            CallPartial(SubscriptionManager.get_chat_messages, self.account_id),
            self._on_refresh,
        )

    def _on_refresh(self, result):
        self._busy = False
        if not self._alive:
            return
        if isinstance(result, dict) and 'chat' in result:
            if result != self.chat_data:
                self.chat_data = result
                try:
                    self._render_messages()
                except Exception:
                    pass

    def _close(self):
        self._alive = False
        self._timer = None
        SubUI.swish(getattr(self, 'w', None))


class AdminPanel:
    def __init__(self, source, data=None):
        self.source = source
        try:
            SubUI.swish(getattr(self, 'w', None))
        except Exception:
            pass

        if data is None:
            w = self.w = SubUI.cw(source=source, size=(420, 190))
            tw(parent=w, text='⚙️ پنل مدیریت', scale=1.2,
               position=(210, 155), h_align='center', color=(0.8, 0.6, 0.2))
            tw(parent=w, text='⏳ در حال دریافت اشتراک‌ها...',
               position=(210, 95), h_align='center', scale=0.85, color=(0.7, 0.7, 0.9))
            SubUI.bw(
                parent=w, label='✖ بستن', size=(80, 30), position=(330, 10),
                on_activate_call=CallPartial(SubUI.swish, w), color=(0.3, 0.1, 0.1)
            )
            SubUI.swish()
            Net.run(self._fetch, self._on_data)
            return
        self._build(data)

    @staticmethod
    def _fetch():
        return SubscriptionManager.get_all_subscriptions(ADMIN_PASSWORD)

    def _on_data(self, result):
        if isinstance(result, dict) and 'subscriptions' in result:
            SubUI.swish(getattr(self, 'w', None))
            teck(0.12, CallStrict(AdminPanel, self.source, result))
        else:
            msg = result.get('error', 'خطا در دریافت اشتراک‌ها') if isinstance(result, dict) else 'خطا در دریافت اشتراک‌ها'
            SubUI.err('❌ ' + str(msg))

    def _build(self, data):
        total = data.get('total', 0)
        used = data.get('used', 0)
        free = data.get('free', 0)
        subs = data.get('subscriptions', [])

        w = self.w = SubUI.cw(source=self.source, size=(500, 490))

        tw(parent=w, text='⚙️ پنل مدیریت اشتراک‌ها', scale=1.2,
           position=(250, 460), h_align='center', color=(0.8, 0.6, 0.2))
        tw(parent=w, text='🔒 دسترسی با رمز تایید شد',
           position=(250, 435), h_align='center', scale=0.7, color=(0, 1, 0))
        tw(parent=w, text='📦 کل: %s | 🔴 استفاده: %s | 🟢 خالی: %s' % (total, used, free),
           position=(250, 405), h_align='center', scale=0.75, color=(0.8, 0.8, 1))

        scroll = sw(parent=w, size=(460, 320), position=(20, 55),
                    color=(0.1, 0.1, 0.1), highlight=False)
        column = clw(parent=scroll, left_border=10, top_border=10, bottom_border=10)

        if subs:
            for sub in subs:
                row = cw(parent=column, size=(440, 52), background=False)

                sub_name = sub.get('name', 'Unknown')
                is_active = sub.get('isActive', False)
                connected_to = sub.get('connected_to')
                remaining = sub.get('remaining', {})

                if connected_to:
                    status_text = '🔒 %s' % connected_to.get('special_name', 'Unknown')
                    status_color = (1, 0.5, 0.5)
                elif is_active:
                    status_text = '✅ فعال'
                    status_color = (0, 1, 0.5)
                else:
                    status_text = '⏰ منقضی'
                    status_color = (0.5, 0.5, 0.5)

                tw(parent=row, text='📋 %s' % sub_name,
                   position=(5, 25), scale=0.75, color=(0.8, 0.8, 1), maxwidth=150)
                tw(parent=row, text=status_text,
                   position=(160, 25), scale=0.7, color=status_color, maxwidth=150)
                remain_text = MainPanel.format_remaining(remaining)
                tw(parent=row, text='⏱️ %s' % remain_text,
                   position=(320, 25), scale=0.6, color=(0.8, 0.8, 0.5), maxwidth=115)
        else:
            tw(parent=column, text='📭 اشتراکی وجود ندارد',
               position=(230, 20), h_align='center', color=(0.5, 0.5, 0.5))

        SubUI.bw(
            parent=w, label='↩ بازگشت', size=(100, 30), position=(20, 15),
            on_activate_call=CallPartial(SubUI.swish, w), color=(0.2, 0.2, 0.3)
        )
        SubUI.swish()

# ==========================================================
# بخش 5: پلاگین اصلی
# ==========================================================

# ba_meta require api 9
# ba_meta export babase.Plugin

class SosooliPlusPlugin(Plugin):
    """پلاگین سوسولی پلاس - سیستم اشتراک‌گذاری ظرفیت‌محور (نسخه اصلاح‌شده)"""

    def __init__(self):
        super().__init__()
        print('🔑 %s - Plugin Activated!' % SYSTEM_NAME)
        print('📡 Worker URL: %s' % WORKER_URL)

        self._start_status_updater()
        self._inject_party_button()

    def _start_status_updater(self):
        teck(5.0, CallStrict(self._status_tick))

    def _status_tick(self):
        def _work():
            try:
                aid = GameDetector.get_account_id()
                if not aid or aid == 'Unknown':
                    return
                my_sub = SubscriptionManager.get_my_subscription(aid)
                if isinstance(my_sub, dict) and 'subscription' in my_sub:
                    SubscriptionManager.update_online_status(True, aid)
            except Exception:
                pass
            try:
                pushcall(CallStrict(self._schedule_status), from_other_thread=True)
            except Exception:
                pass
        threading.Thread(target=_work, daemon=True).start()

    def _schedule_status(self):
        AppTimer(30.0, CallStrict(self._status_tick))

    def _inject_party_button(self):
        try:
            from bauiv1lib import party
            original_init = party.PartyWindow.__init__

            def new_init(self2, *args, **kwargs):
                result = original_init(self2, *args, **kwargs)
                try:
                    btn_x = self2._width - 530
                    btn_y = self2._height - 260
                    sub_btn = SubUI.bw(
                        parent=self2._root_widget,
                        position=(btn_x, btn_y),
                        size=(30, 30),
                        label='',
                        icon=gt('achievementCrossHair'),
                        iconscale=1.2,
                        color=(0.3, 0.2, 0.1),
                    )
                    bw(sub_btn, on_activate_call=CallPartial(MainPanel, self2._root_widget))
                except Exception as exc:
                    print('🔑 %s - button error: %s' % (SYSTEM_NAME, exc))
                return result

            party.PartyWindow.__init__ = new_init
            print('🔑 %s - party button injected!' % SYSTEM_NAME)
        except Exception as exc:
            print('🔑 %s - inject error: %s' % (SYSTEM_NAME, exc))

    def __del__(self):
        try:
            print('🔑 %s - Plugin Deactivated!' % SYSTEM_NAME)
        except Exception:
            pass