# ============================================
# سیستم اشتراک‌گذاری سوسولی - نسخه ظرفیت‌محور
# ============================================

import datetime
import time
import json
import urllib.request
import urllib.parse
import urllib.error
import re
from babase import Plugin, AppTimer
from bauiv1 import (
    containerwidget as cw,
    screenmessage as push,
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
    get_special_widget as gsw
)
from bascenev1 import (
    get_chat_messages as GCM,
    chatmessage as CM,
    get_game_roster,
    get_foreground_host_session,
    disconnect_client
)

# ============================================
# تنظیمات
# ============================================

WORKER_URL = "https://soft-cloud-613d.hamid1384098.workers.dev"
SYSTEM_NAME = "سوسولی پلاس"
ADMIN_PASSWORD = "uagugauaa1384rty"

# ============================================
# بخش 1: تشخیص اطلاعات بازیکن
# ============================================

class GameDetector:
    """تشخیص اطلاعات بازیکنان از بازی"""

    @staticmethod
    def get_account_id():
        """دریافت آیدی واقعی بازی"""
        try:
            if hasattr(APP, 'plus'):
                if hasattr(APP.plus, 'get_v1_account_state'):
                    account_state = APP.plus.get_v1_account_state()
                    if account_state == 'signed_in':
                        if hasattr(APP.plus, 'get_v1_account_id'):
                            account_id = APP.plus.get_v1_account_id()
                            if account_id:
                                return account_id
                        if hasattr(APP.plus, 'get_v1_account_name'):
                            account_name = APP.plus.get_v1_account_name()
                            if account_name:
                                return account_name

            try:
                roster = get_game_roster()
                nickname = GameDetector.get_nickname()
                for client in roster:
                    if 'players' in client and client['players']:
                        for p in client['players']:
                            if p.get('name', '') == nickname:
                                account_id = client.get('account_id', '')
                                if account_id:
                                    return account_id
                                client_id = client.get('client_id', -1)
                                if client_id != -1:
                                    return str(client_id)
            except:
                pass

            account = APP.config.get('Player Name', 'Unknown')
            return account
        except:
            return 'Unknown'

    @staticmethod
    def get_nickname():
        """دریافت نام نمایشی کاربر"""
        try:
            name = APP.config.get('Player Name', 'Unknown')
            if name:
                return name
            roster = get_game_roster()
            for client in roster:
                if 'players' in client and client['players']:
                    for p in client['players']:
                        if p.get('name'):
                            return p.get('name')
            return 'Unknown'
        except:
            return 'Unknown'

    @staticmethod
    def get_special_name():
        """دریافت اسم خاص کاربر"""
        try:
            roster = get_game_roster()
            nickname = GameDetector.get_nickname()
            for client in roster:
                if 'players' in client and client['players']:
                    for p in client['players']:
                        if p.get('name', '') == nickname:
                            special = client.get('display_string', '')
                            if special:
                                return special
                            return nickname
            return nickname
        except:
            return GameDetector.get_nickname()

    @staticmethod
    def get_client_id():
        """دریافت کلاینت‌آیدی کاربر"""
        try:
            roster = get_game_roster()
            nickname = GameDetector.get_nickname()
            for client in roster:
                if 'players' in client and client['players']:
                    for p in client['players']:
                        if p.get('name', '') == nickname:
                            return client.get('client_id', -1)
            return -1
        except:
            return -1

# ============================================
# بخش 2: مدیریت اشتراک‌ها (ظرفیت‌محور)
# ============================================

class SubscriptionManager:
    WORKER_URL = WORKER_URL
    _cache = {}
    _cache_time = {}
    CACHE_DURATION = 30

    @staticmethod
    def _get_account_id():
        return GameDetector.get_account_id()

    @staticmethod
    def _get_nickname():
        return GameDetector.get_nickname()

    @staticmethod
    def _get_special_name():
        return GameDetector.get_special_name()

    @staticmethod
    def _get_client_id():
        return GameDetector.get_client_id()

    @staticmethod
    def _make_request(endpoint, data=None, method='GET'):
        url = f"{SubscriptionManager.WORKER_URL}{endpoint}"
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,fa;q=0.8',
            'Connection': 'keep-alive',
            'Origin': WORKER_URL,
            'Referer': WORKER_URL + '/',
        }
        try:
            import ssl
            try:
                ctx = ssl.create_default_context()
            except:
                ctx = ssl._create_unverified_context()

            if method == 'GET' and data:
                params = '&'.join([f"{k}={urllib.parse.quote(str(v))}" for k, v in data.items()])
                url = f"{url}?{params}"
                req = urllib.request.Request(url, headers=headers)
            elif method in ['POST', 'PUT', 'DELETE']:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(data).encode('utf-8'),
                    headers=headers,
                    method=method
                )
            else:
                req = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result

        except urllib.error.HTTPError as e:
            try:
                error_body = e.read().decode('utf-8')
                error_data = json.loads(error_body)
                return error_data
            except:
                return {'error': f'HTTP Error {e.code}: {e.reason}', 'code': 'HTTP_ERROR'}
        except urllib.error.URLError as e:
            return {'error': f'URL Error: {e.reason}', 'code': 'URL_ERROR'}
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
        """دریافت اطلاعات ظرفیت: کل، استفاده شده، باقیمانده"""
        cache_key = "capacity_info"
        cached = cls._get_cached(cache_key)
        if cached:
            return cached

        result = cls._make_request('/api/subs/capacity')
        cls._set_cached(cache_key, result)
        return result

    @classmethod
    def get_my_subscription(cls, account_id=None):
        """دریافت اشتراک متصل شده کاربر"""
        if not account_id:
            account_id = cls._get_account_id()

        result = cls._make_request('/api/subs/my', {'account_id': account_id})
        return result

    @classmethod
    def connect_to_subscription(cls, special_name, account_id=None, nickname=None, client_id=None):
        """اتصال به یک اشتراک خالی"""
        if not account_id:
            account_id = cls._get_account_id()
        if not nickname:
            nickname = cls._get_nickname()
        if not client_id:
            client_id = cls._get_client_id()

        result = cls._make_request(
            '/api/subs/connect',
            {
                'account_id': account_id,
                'nickname': nickname,
                'special_name': special_name,
                'client_id': client_id
            },
            'POST'
        )

        cls._cache = {}
        return result

    @classmethod
    def disconnect_subscription(cls, account_id=None):
        """قطع اتصال از اشتراک"""
        if not account_id:
            account_id = cls._get_account_id()

        result = cls._make_request(
            '/api/subs/disconnect',
            {'account_id': account_id},
            'POST'
        )

        cls._cache = {}
        return result

    @classmethod
    def get_chat_messages(cls, account_id=None, limit=50):
        if not account_id:
            account_id = cls._get_account_id()

        result = cls._make_request(
            '/api/subs/chat/get',
            {'account_id': account_id, 'limit': limit}
        )
        return result

    @classmethod
    def send_chat_message(cls, message, account_id=None):
        if not account_id:
            account_id = cls._get_account_id()

        result = cls._make_request(
            '/api/subs/chat/send',
            {
                'account_id': account_id,
                'message': message
            },
            'POST'
        )
        return result

    @classmethod
    def update_online_status(cls, is_online=True, account_id=None):
        if not account_id:
            account_id = cls._get_account_id()

        result = cls._make_request(
            '/api/subs/status',
            {
                'account_id': account_id,
                'is_online': is_online
            },
            'POST'
        )
        return result

# ============================================
# بخش 3: کلاس‌های UI
# ============================================

class SubUI:
    @staticmethod
    def UIS():
        i = APP.ui_v1.uiscale
        if i == 0:
            return 1.5
        elif i == 1:
            return 1.1
        else:
            return 0.8

    @staticmethod
    def bw(**k):
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

    @staticmethod
    def cw(source, ps=0, **k):
        o = source.get_screen_space_center() if source else None
        kwargs = dict(k)
        filtered_kwargs = {}
        for key, value in kwargs.items():
            if key not in ['parent', 'scale_origin_stack_offset', 'scale', 'transition', 'color']:
                filtered_kwargs[key] = value

        r = cw(
            parent=gsw('overlay_stack'),
            scale_origin_stack_offset=o,
            scale=SubUI.UIS() + ps,
            transition='in_scale',
            color=(0.18, 0.18, 0.18),
            **filtered_kwargs
        )
        cw(r, on_outside_click_call=CallPartial(SubUI.swish, t=r))
        return r

    @staticmethod
    def swish(t=None):
        gs('swish').play()
        if t:
            cw(t, transition='out_scale')

    @staticmethod
    def err(t):
        gs('block').play()
        push(t, color=(1, 1, 0))

    @staticmethod
    def ok():
        gs('dingSmallHigh').play()
        push('Success!', color=(0, 1, 0))

# ============================================
# بخش 4: پنل‌ها
# ============================================

class MainPanel:
    def __init__(self, source):
        if hasattr(self, 'w') and self.w:
            try:
                SubUI.swish(self.w)
            except:
                pass

        self.source = source
        self.account_id = SubscriptionManager._get_account_id()
        self.nickname = SubscriptionManager._get_nickname()
        self.special_name = SubscriptionManager._get_special_name()

        self.capacity_info = SubscriptionManager.get_capacity_info()
        self.my_sub = SubscriptionManager.get_my_subscription(self.account_id)

        total = self.capacity_info.get('total_subscriptions', 0)
        used = self.capacity_info.get('used_capacity', 0)
        remaining = self.capacity_info.get('remaining_capacity', 0)

        has_subscription = 'subscription' in self.my_sub and 'error' not in self.my_sub

        w = self.w = SubUI.cw(
            source=source,
            size=(450, 520) if has_subscription else (420, 480),
            ps=SubUI.UIS() * 0.8
        )

        tw(
            parent=w,
            text=f'🔑 {SYSTEM_NAME}',
            scale=1.2,
            position=(225, 490),
            h_align='center',
            color=(0.8, 0.6, 0.2)
        )

        tw(
            parent=w,
            text=f'🆔 آیدی: {self.account_id}',
            position=(20, 460),
            scale=0.8,
            color=(0.6, 0.8, 1)
        )

        tw(
            parent=w,
            text=f'👤 اسم خاص: {self.special_name}',
            position=(20, 435),
            scale=0.8,
            color=(0.8, 0.8, 1)
        )

        capacity_y = 390

        capacity_bg = cw(
            parent=w,
            size=(410, 80),
            position=(20, capacity_y),
            color=(0.12, 0.15, 0.2),
            border=2,
            border_color=(0.3, 0.5, 0.8)
        )

        tw(
            parent=capacity_bg,
            text='📊 وضعیت ظرفیت اشتراک‌ها',
            position=(205, 55),
            h_align='center',
            scale=0.75,
            color=(0.6, 0.8, 1)
        )

        tw(
            parent=capacity_bg,
            text=f'📦 کل: {total}',
            position=(20, 25),
            scale=0.7,
            color=(0.8, 0.8, 0.8)
        )

        tw(
            parent=capacity_bg,
            text=f'🔴 استفاده: {used}',
            position=(140, 25),
            scale=0.7,
            color=(1, 0.5, 0.5)
        )

        remain_color = (0.5, 1, 0.5) if remaining > 0 else (1, 0.3, 0.3)
        tw(
            parent=capacity_bg,
            text=f'🟢 باقی: {remaining}',
            position=(270, 25),
            scale=0.7,
            color=remain_color
        )

        scroll_y = 70
        scroll_h = 300 if has_subscription else 260
        scroll = sw(
            parent=w,
            size=(410, scroll_h),
            position=(20, scroll_y),
            color=(0.1, 0.1, 0.1),
            highlight=False
        )
        column = clw(
            parent=scroll,
            left_border=10,
            top_border=10,
            bottom_border=10
        )

        btn_y = 10
        btn_h = 45

        if not has_subscription:
            tw(
                parent=w,
                text='❌ شما به اشتراکی متصل نیستید',
                position=(225, 355),
                h_align='center',
                scale=0.75,
                color=(1, 0.5, 0)
            )

            if remaining > 0:
                SubUI.bw(
                    parent=column,
                    label='🔗 اتصال به اشتراک',
                    size=(370, btn_h),
                    position=(10, btn_y),
                    on_activate_call=CallStrict(self._show_connect_panel),
                    color=(0.1, 0.4, 0.1)
                )
                btn_y += btn_h + 5
            else:
                tw(
                    parent=column,
                    text='⛔ ظرفیت تکمیل است!',
                    position=(185, btn_y + 10),
                    h_align='center',
                    color=(1, 0.3, 0.3)
                )
                btn_y += btn_h + 5
        else:
            sub_data = self.my_sub.get('subscription', {})
            sub_name = sub_data.get('name', 'Unknown')
            sub_remaining = sub_data.get('remaining', {})

            tw(
                parent=w,
                text=f'✅ متصل به: {sub_name}',
                position=(225, 355),
                h_align='center',
                scale=0.8,
                color=(0, 1, 0.5)
            )

            remain_text = MainPanel.format_remaining(sub_remaining)
            tw(
                parent=w,
                text=f'⏱️ {remain_text}',
                position=(225, 330),
                h_align='center',
                scale=0.7,
                color=(1, 0.8, 0.2)
            )

            SubUI.bw(
                parent=column,
                label='💬 چت اشتراک',
                size=(370, btn_h),
                position=(10, btn_y),
                on_activate_call=CallStrict(self._show_chat),
                color=(0.1, 0.3, 0.2)
            )
            btn_y += btn_h + 5

            SubUI.bw(
                parent=column,
                label='🚪 قطع اتصال',
                size=(370, btn_h),
                position=(10, btn_y),
                on_activate_call=CallStrict(self._disconnect),
                color=(0.3, 0.1, 0.1)
            )
            btn_y += btn_h + 5

        SubUI.bw(
            parent=column,
            label='⚙️ پنل مدیریت (نیاز به رمز)',
            size=(370, btn_h),
            position=(10, btn_y),
            on_activate_call=CallStrict(self._show_admin_login),
            color=(0.2, 0.1, 0.3)
        )
        btn_y += btn_h + 5

        SubUI.bw(
            parent=w,
            label='✖ بستن',
            size=(80, 30),
            position=(350, 10),
            on_activate_call=CallPartial(SubUI.swish, w),
            color=(0.3, 0.1, 0.1)
        )

        SubUI.swish()

    @staticmethod
    def format_remaining(remaining):
        if not remaining or remaining.get('totalSeconds', 0) <= 0:
            return 'منقضی شده'
        parts = []
        if remaining.get('days', 0) > 0:
            parts.append(f'{remaining["days"]} روز')
        if remaining.get('hours', 0) > 0:
            parts.append(f'{remaining["hours"]} ساعت')
        if remaining.get('minutes', 0) > 0:
            parts.append(f'{remaining["minutes"]} دقیقه')
        return ' '.join(parts) if parts else 'کمتر از یک دقیقه'

    def _show_connect_panel(self):
        SubUI.swish(self.w)
        teck(0.1, CallStrict(ConnectPanel, self.source))

    def _show_admin_login(self):
        SubUI.swish(self.w)
        teck(0.1, CallStrict(AdminLoginPanel, self.source))

    def _show_chat(self):
        SubUI.swish(self.w)
        teck(0.1, CallStrict(ChatPanel, self.source))

    def _disconnect(self):
        result = SubscriptionManager.disconnect_subscription()
        if 'error' in result:
            SubUI.err(f'❌ {result["error"]}')
            return
        SubUI.ok()
        push('✅ اتصال شما قطع شد', color=(1, 0.5, 0))
        if hasattr(self, 'w') and self.w:
            SubUI.swish(self.w)
            teck(0.3, CallStrict(MainPanel, self.source))


class ConnectPanel:
    def __init__(self, source):
        if hasattr(self, 'w') and self.w:
            try:
                SubUI.swish(self.w)
            except:
                pass

        self.source = source
        self.account_id = SubscriptionManager._get_account_id()
        self.nickname = SubscriptionManager._get_nickname()

        w = self.w = SubUI.cw(
            source=source,
            size=(420, 280),
            ps=SubUI.UIS() * 0.8
        )

        tw(
            parent=w,
            text='🔗 اتصال به اشتراک',
            scale=1.2,
            position=(210, 255),
            h_align='center',
            color=(0.8, 0.6, 0.2)
        )

        tw(
            parent=w,
            text=f'🆔 آیدی شما: {self.account_id}',
            position=(20, 225),
            scale=0.8,
            color=(0.6, 0.8, 1)
        )

        tw(
            parent=w,
            text='اسم خاص خود را وارد کنید:',
            position=(20, 190),
            color=(0.8, 0.8, 1)
        )

        self.special_input = tw(
            parent=w,
            maxwidth=260,
            size=(260, 30),
            editable=True,
            v_align='center',
            color=(0.75, 0.75, 0.75),
            position=(20, 155),
            allow_clear_button=False,
            text=SubscriptionManager._get_special_name()
        )

        SubUI.bw(
            parent=w,
            label='✅ اتصال',
            size=(110, 35),
            position=(290, 150),
            on_activate_call=CallStrict(self._connect),
            color=(0.1, 0.4, 0.1)
        )

        tw(
            parent=w,
            text='⚠️ بعد از اتصال، اشتراک به نام شما ثبت می‌شود',
            position=(210, 110),
            h_align='center',
            scale=0.65,
            color=(0.8, 0.6, 0.3)
        )

        tw(
            parent=w,
            text='⚠️ و کسی دیگر نمی‌تواند به آن وصل شود',
            position=(210, 85),
            h_align='center',
            scale=0.65,
            color=(0.8, 0.6, 0.3)
        )

        SubUI.bw(
            parent=w,
            label='↩ بازگشت',
            size=(100, 30),
            position=(20, 15),
            on_activate_call=CallPartial(self._close),
            color=(0.2, 0.2, 0.3)
        )

        SubUI.swish()

    def _connect(self):
        special_name = tw(query=self.special_input).strip()

        if not special_name:
            SubUI.err('⚠️ لطفاً اسم خاص را وارد کنید!')
            return

        result = SubscriptionManager.connect_to_subscription(special_name)

        if 'error' in result:
            SubUI.err(f'❌ {result["error"]}')
            return

        sub_name = result.get('subscription_name', 'اشتراک')
        SubUI.ok()
        push(f'✅ به "{sub_name}" متصل شدید!', color=(0, 1, 0))
        push('🔒 اشتراک به نام شما ثبت شد', color=(0.5, 0.8, 1))

        self._close()
        teck(0.5, CallStrict(MainPanel, self.source))

    def _close(self):
        if hasattr(self, 'w') and self.w:
            SubUI.swish(self.w)


class AdminLoginPanel:
    def __init__(self, source):
        if hasattr(self, 'w') and self.w:
            try:
                SubUI.swish(self.w)
            except:
                pass

        self.source = source

        w = self.w = SubUI.cw(
            source=source,
            size=(350, 220),
            ps=SubUI.UIS() * 0.8
        )

        tw(
            parent=w,
            text='⚙️ ورود به پنل مدیریت',
            scale=1.1,
            position=(175, 200),
            h_align='center',
            color=(0.8, 0.6, 0.2)
        )

        tw(
            parent=w,
            text='رمز مدیریت را وارد کنید:',
            position=(20, 160),
            color=(0.8, 0.8, 1)
        )

        self.password_input = tw(
            parent=w,
            maxwidth=250,
            size=(250, 30),
            editable=True,
            v_align='center',
            color=(0.75, 0.75, 0.75),
            position=(20, 130),
            allow_clear_button=False,
            text=''
        )

        SubUI.bw(
            parent=w,
            label='✅ ورود',
            size=(100, 35),
            position=(220, 125),
            on_activate_call=CallStrict(self._check_password),
            color=(0.1, 0.3, 0.1)
        )

        SubUI.bw(
            parent=w,
            label='↩ بازگشت',
            size=(100, 30),
            position=(20, 15),
            on_activate_call=CallPartial(self._close),
            color=(0.2, 0.2, 0.3)
        )

        SubUI.swish()

    def _check_password(self):
        password = tw(query=self.password_input).strip()

        if not password:
            SubUI.err('⚠️ رمز را وارد کنید!')
            return

        if password == ADMIN_PASSWORD:
            SubUI.ok()
            push('✅ رمز صحیح!', color=(0, 1, 0))
            self._close()
            teck(0.5, CallStrict(AdminPanel, self.source))
        else:
            SubUI.err('❌ رمز اشتباه!')

    def _close(self):
        if hasattr(self, 'w') and self.w:
            SubUI.swish(self.w)


class ChatPanel:
    def __init__(self, source):
        if hasattr(self, 'w') and self.w:
            try:
                SubUI.swish(self.w)
            except:
                pass

        self.source = source
        self.account_id = SubscriptionManager._get_account_id()
        self.special_name = SubscriptionManager._get_special_name()

        w = self.w = SubUI.cw(
            source=source,
            size=(500, 450),
            ps=SubUI.UIS() * 0.8
        )

        tw(
            parent=w,
            text='💬 چت اشتراک',
            scale=1.2,
            position=(250, 420),
            h_align='center',
            color=(0.8, 0.6, 0.2)
        )

        self.chat_data = SubscriptionManager.get_chat_messages(self.account_id)

        self.scroll = sw(
            parent=w,
            size=(460, 280),
            position=(20, 100),
            color=(0.05, 0.05, 0.05),
            highlight=False
        )
        self.chat_container = cw(
            parent=self.scroll,
            size=(440, 260),
            background=False
        )
        self._display_messages()

        self.input_field = tw(
            parent=w,
            maxwidth=320,
            size=(320, 30),
            editable=True,
            v_align='center',
            color=(0.75, 0.75, 0.75),
            position=(20, 55),
            allow_clear_button=False,
            text='پیام...'
        )

        SubUI.bw(
            parent=w,
            label='📤 ارسال',
            size=(80, 30),
            position=(350, 55),
            on_activate_call=CallStrict(self._send_message),
            color=(0.1, 0.3, 0.1)
        )

        SubUI.bw(
            parent=w,
            label='↩ بازگشت',
            size=(100, 30),
            position=(20, 15),
            on_activate_call=CallPartial(self._close),
            color=(0.2, 0.2, 0.3)
        )

        self.update_timer = AppTimer(3, CallStrict(self._auto_refresh), repeat=True)
        SubUI.swish()

    def _display_messages(self):
        for child in self.chat_container.get_children():
            child.delete()

        if not self.chat_data or 'error' in self.chat_data:
            tw(
                parent=self.chat_container,
                text='❌ خطا در دریافت پیام‌ها',
                position=(220, 120),
                h_align='center',
                color=(1, 0.5, 0)
            )
            return

        chat_list = self.chat_data.get('chat', [])
        if not chat_list:
            tw(
                parent=self.chat_container,
                text='💬 پیامی نیست',
                position=(220, 120),
                h_align='center',
                color=(0.5, 0.5, 0.5)
            )
            return

        y_pos = len(chat_list) * 25 + 10
        for msg in reversed(chat_list):
            sender = msg.get('sender_special_name', msg.get('sender_nickname', 'Unknown'))
            message = msg.get('message', '')
            timestamp = msg.get('timestamp', 0)
            time_str = time.strftime('%H:%M', time.localtime(timestamp / 1000))

            color = (0.6, 1, 0.6) if sender == self.special_name else (0.8, 0.8, 1)

            tw(
                parent=self.chat_container,
                text=f'{sender} [{time_str}]:',
                position=(10, y_pos),
                scale=0.7,
                color=color
            )
            tw(
                parent=self.chat_container,
                text=message,
                position=(120, y_pos),
                scale=0.7,
                color=(0.9, 0.9, 0.9),
                maxwidth=310
            )
            y_pos -= 25

        cw(self.chat_container, size=(440, max(260, y_pos + 20)))
        sw(self.scroll, position=(0, 0))

    def _send_message(self):
        message = tw(query=self.input_field).strip()
        if not message or message == 'پیام...':
            SubUI.err('⚠️ پیام را وارد کنید!')
            return

        result = SubscriptionManager.send_chat_message(message, self.account_id)
        if 'error' in result:
            SubUI.err(f'❌ {result["error"]}')
            return

        SubUI.ok()
        tw(self.input_field, text='')
        self.chat_data = SubscriptionManager.get_chat_messages(self.account_id)
        self._display_messages()

    def _auto_refresh(self):
        if not hasattr(self, 'w') or not self.w:
            if hasattr(self, 'update_timer'):
                self.update_timer = None
            return
        try:
            new_chat = SubscriptionManager.get_chat_messages(self.account_id)
            if new_chat != self.chat_data:
                self.chat_data = new_chat
                self._display_messages()
        except:
            pass

    def _close(self):
        if hasattr(self, 'update_timer'):
            self.update_timer = None
        SubUI.swish(self.w)


class AdminPanel:
    def __init__(self, source):
        if hasattr(self, 'w') and self.w:
            try:
                SubUI.swish(self.w)
            except:
                pass

        self.source = source
        self.account_id = SubscriptionManager._get_account_id()

        w = self.w = SubUI.cw(
            source=source,
            size=(500, 480),
            ps=SubUI.UIS() * 0.8
        )

        tw(
            parent=w,
            text='⚙️ پنل مدیریت اشتراک‌ها',
            scale=1.2,
            position=(250, 450),
            h_align='center',
            color=(0.8, 0.6, 0.2)
        )

        tw(
            parent=w,
            text='🔒 دسترسی با رمز تایید شد',
            position=(250, 425),
            h_align='center',
            scale=0.7,
            color=(0, 1, 0)
        )

        self.subs_data = SubscriptionManager._make_request(
            '/api/subs',
            {'account_id': self.account_id, 'password': ADMIN_PASSWORD}
        )

        total = self.subs_data.get('total', 0) if 'total' in self.subs_data else 0
        used = self.subs_data.get('used', 0) if 'used' in self.subs_data else 0
        free = self.subs_data.get('free', 0) if 'free' in self.subs_data else 0

        tw(
            parent=w,
            text=f'📦 کل: {total} | 🔴 استفاده: {used} | 🟢 خالی: {free}',
            position=(250, 395),
            h_align='center',
            scale=0.75,
            color=(0.8, 0.8, 1)
        )

        scroll = sw(
            parent=w,
            size=(460, 310),
            position=(20, 65),
            color=(0.1, 0.1, 0.1),
            highlight=False
        )
        column = clw(
            parent=scroll,
            left_border=10,
            top_border=10,
            bottom_border=10
        )

        if 'subscriptions' in self.subs_data:
            for sub in self.subs_data['subscriptions']:
                row = cw(
                    parent=column,
                    size=(440, 50),
                    background=False
                )

                sub_name = sub.get('name', 'Unknown')
                is_active = sub.get('isActive', False)
                connected_to = sub.get('connected_to', None)
                remaining = sub.get('remaining', {})

                status_color = (0, 1, 0.5) if is_active else (0.5, 0.5, 0.5)
                status_text = '✅ فعال' if is_active else '⏰ منقضی'

                if connected_to:
                    status_text = f'🔒 {connected_to.get("special_name", "Unknown")}'
                    status_color = (1, 0.5, 0.5)

                tw(
                    parent=row,
                    text=f'📋 {sub_name}',
                    position=(10, 20),
                    color=(0.8, 0.8, 1)
                )

                tw(
                    parent=row,
                    text=status_text,
                    position=(200, 20),
                    scale=0.75,
                    color=status_color
                )

                remain_text = MainPanel.format_remaining(remaining)
                tw(
                    parent=row,
                    text=f'⏱️ {remain_text}',
                    position=(340, 20),
                    scale=0.65,
                    color=(0.8, 0.8, 0.5)
                )
        else:
            tw(
                parent=column,
                text='❌ خطا در دریافت اشتراک‌ها',
                position=(230, 20),
                h_align='center',
                color=(1, 0.5, 0)
            )

        SubUI.bw(
            parent=w,
            label='↩ بازگشت',
            size=(100, 30),
            position=(20, 15),
            on_activate_call=CallPartial(SubUI.swish, w),
            color=(0.2, 0.2, 0.3)
        )

        SubUI.swish()

# ============================================
# بخش 5: پلاگین اصلی
# ============================================

# ba_meta require api 9
# ba_meta export babase.Plugin

class SosooliPlusPlugin(Plugin):
    """پلاگین سوسولی پلاس - سیستم اشتراک‌گذاری ظرفیت‌محور"""

    def __init__(self):
        print(f"🔑 {SYSTEM_NAME} - Plugin Activated!")
        print(f"📡 Worker URL: {WORKER_URL}")

        self._start_status_updater()
        self._inject_party_button()

    def _start_status_updater(self):
        def update_status():
            try:
                account_id = SubscriptionManager._get_account_id()
                my_sub = SubscriptionManager.get_my_subscription(account_id)
                if 'subscription' in my_sub:
                    SubscriptionManager.update_online_status(True, account_id)
            except:
                pass
            teck(30, CallStrict(update_status))

        teck(5, CallStrict(update_status))

    def _inject_party_button(self):
        try:
            from bauiv1lib import party
            original_init = party.PartyWindow.__init__

            def new_init(self, *args, **kwargs):
                result = original_init(self, *args, **kwargs)
                try:
                    btn_x = self._width - 530
                    btn_y = self._height - 260

                    sub_btn = SubUI.bw(
                        icon=gt('achievementCrossHair'),
                        position=(btn_x, btn_y),
                        parent=self._root_widget,
                        iconscale=1.2,
                        size=(30, 30),
                        label='',
                        color=(0.3, 0.2, 0.1)
                    )

                    bw(sub_btn, on_activate_call=CallPartial(MainPanel, self._root_widget))
                except Exception as e:
                    print(f"Error adding button: {e}")
                return result

            party.PartyWindow.__init__ = new_init
            print(f"🔑 {SYSTEM_NAME} button injected!")
        except Exception as e:
            print(f"Error injecting button: {e}")

    def __del__(self):
        print(f"🔑 {SYSTEM_NAME} - Plugin Deactivated!")
