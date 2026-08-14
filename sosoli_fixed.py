# ============================================
# ارتش سوسولی - سیستم کامل با تشخیص آیدی و رمز ادمین
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

WORKER_URL = "https://summer-hall-b302.hamid1384rty.workers.dev"
ARMY_NAME = "ارتش سوسولی"
ADMIN_SPECIAL_NAME = "sosoliplus"
ADMIN_PASSWORD = "uagugauaa1384rty"  # رمز پنل ادمین

# ============================================
# بخش 1: تشخیص اسم خاص و آیدی بازی (مشابه BslifeMod)
# ============================================

class GameDetector:
    """تشخیص اطلاعات بازیکنان از بازی"""
    
    @staticmethod
    def get_account_id():
        """دریافت آیدی واقعی بازی (مثل dfg20ff)"""
        try:
            # روش 1: از plus
            if hasattr(APP, 'plus'):
                if hasattr(APP.plus, 'get_v1_account_state'):
                    account_state = APP.plus.get_v1_account_state()
                    if account_state == 'signed_in':
                        if hasattr(APP.plus, 'get_v1_account_id'):
                            account_id = APP.plus.get_v1_account_id()
                            if account_id:
                                print(f"✅ Account ID from plus: {account_id}")
                                return account_id
                        
                        # روش 2: از get_v1_account_name (برای نسخه‌های قدیمی)
                        if hasattr(APP.plus, 'get_v1_account_name'):
                            account_name = APP.plus.get_v1_account_name()
                            if account_name:
                                print(f"✅ Account ID from name: {account_name}")
                                return account_name
            
            # روش 3: از roster (دقیق‌ترین روش برای تشخیص)
            try:
                roster = get_game_roster()
                nickname = GameDetector.get_nickname()
                for client in roster:
                    if 'players' in client and client['players']:
                        for p in client['players']:
                            if p.get('name', '') == nickname:
                                account_id = client.get('account_id', '')
                                if account_id:
                                    print(f"✅ Account ID from roster: {account_id}")
                                    return account_id
                                # اگر account_id خالی بود، از client_id استفاده کن
                                client_id = client.get('client_id', -1)
                                if client_id != -1:
                                    print(f"⚠️ Using client_id: {client_id}")
                                    return str(client_id)
            except Exception as e:
                print(f"Error getting account from roster: {e}")
            
            # روش 4: از config
            account = APP.config.get('Player Name', 'Unknown')
            print(f"⚠️ Using config name: {account}")
            return account
        except Exception as e:
            print(f"❌ Error getting account id: {e}")
            return 'Unknown'
    
    @staticmethod
    def get_nickname():
        """دریافت نام نمایشی کاربر"""
        try:
            # روش 1: از config
            name = APP.config.get('Player Name', 'Unknown')
            if name:
                return name
            
            # روش 2: از roster
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
        """دریافت اسم خاص کاربر (مثل sosoliplus)"""
        try:
            # روش 1: از roster
            roster = get_game_roster()
            nickname = GameDetector.get_nickname()
            
            for client in roster:
                if 'players' in client and client['players']:
                    for p in client['players']:
                        if p.get('name', '') == nickname:
                            special = client.get('display_string', '')
                            if special:
                                print(f"✅ Special name found: {special}")
                                return special
                            else:
                                # اگر display_string خالی بود از nickname استفاده کن
                                return nickname
            
            # روش 2: اگر اسم خاص "sosoliplus" هست، برگردون
            if nickname.lower() == ADMIN_SPECIAL_NAME.lower():
                return ADMIN_SPECIAL_NAME
            
            return nickname
        except Exception as e:
            print(f"Error getting special name: {e}")
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
    
    @staticmethod
    def get_all_players():
        """دریافت اطلاعات تمام بازیکنان"""
        players = []
        try:
            roster = get_game_roster()
            for client in roster:
                if 'players' in client and client['players']:
                    for p in client['players']:
                        players.append({
                            'name': p.get('name', 'Unknown'),
                            'special_name': client.get('display_string', p.get('name', 'Unknown')),
                            'client_id': client.get('client_id', -1),
                            'account_id': client.get('account_id', ''),
                            'is_host': client.get('client_id', -1) == -1
                        })
        except:
            pass
        return players

# ============================================
# بخش 2: مدیریت ارتش
# ============================================

class ArmyManager:
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
        url = f"{ArmyManager.WORKER_URL}{endpoint}"

        # ✅ FIX 1: Add proper headers including User-Agent
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,fa;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Origin': 'https://summer-hall-b302.hamid1384rty.workers.dev',
            'Referer': 'https://summer-hall-b302.hamid1384rty.workers.dev/',
        }

        try:
            # ✅ FIX 2: Create SSL context for Android/Termux
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

            # ✅ FIX 3: Use SSL context
            with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
                result = json.loads(response.read().decode('utf-8'))
                print(f"📡 Response: {result}")
                return result

        except urllib.error.HTTPError as e:
            # ✅ FIX 4: Better error logging
            try:
                error_body = e.read().decode('utf-8')
                print(f"❌ HTTP Error {e.code}: {error_body}")
                error_data = json.loads(error_body)
                return error_data
            except:
                print(f"❌ HTTP Error {e.code}: {e.reason}")
                return {'error': f'HTTP Error {e.code}: {e.reason}', 'code': 'HTTP_ERROR'}
        except urllib.error.URLError as e:
            print(f"❌ URL Error: {e.reason}")
            return {'error': f'URL Error: {e.reason}', 'code': 'URL_ERROR'}
        except Exception as e:
            print(f"❌ Error: {e}")
            return {'error': str(e), 'code': 'CONNECTION_ERROR'}

    @staticmethod
    def _get_cached(key):
        if key in ArmyManager._cache:
            if time.time() - ArmyManager._cache_time.get(key, 0) < ArmyManager.CACHE_DURATION:
                return ArmyManager._cache[key]
        return None
    
    @staticmethod
    def _set_cached(key, value):
        ArmyManager._cache[key] = value
        ArmyManager._cache_time[key] = time.time()
    
    @classmethod
    def is_member(cls, account_id=None):
        if not account_id:
            account_id = cls._get_account_id()
        
        print(f"🔍 Checking membership for: {account_id}")
        
        cache_key = f"is_member_{account_id}"
        cached = cls._get_cached(cache_key)
        if cached is not None:
            return cached
        
        result = cls._make_request('/api/army/members', {'account_id': account_id})
        
        if 'error' in result:
            cls._set_cached(cache_key, False)
            return False
        
        cls._set_cached(cache_key, True)
        return True
    
    @classmethod
    def get_members(cls, account_id=None):
        if not account_id:
            account_id = cls._get_account_id()
        
        cache_key = f"members_{account_id}"
        cached = cls._get_cached(cache_key)
        if cached:
            return cached
        
        result = cls._make_request('/api/army/members', {'account_id': account_id})
        
        if 'error' in result:
            return None
        
        cls._set_cached(cache_key, result)
        return result
    
    @classmethod
    def get_member_count(cls):
        cache_key = "member_count"
        cached = cls._get_cached(cache_key)
        if cached:
            return cached
        
        result = cls._make_request('/api/army/count')
        
        if 'error' in result:
            return {'total_members': 0}
        
        cls._set_cached(cache_key, result)
        return result
    
    @classmethod
    def send_join_request(cls, special_name_input=None, nickname=None, account_id=None, client_id=None):
        if not account_id:
            account_id = cls._get_account_id()
        if not nickname:
            nickname = cls._get_nickname()
        if not client_id:
            client_id = cls._get_client_id()
        
        # اگر اسم خاص وارد شده، از اون استفاده کن، وگرنه از تشخیص خودکار
        special_name = special_name_input if special_name_input else cls._get_special_name()
        
        print(f"📝 Join Request: account={account_id}, special={special_name}, client={client_id}")
        
        result = cls._make_request(
            '/api/army/join',
            {
                'account_id': account_id,
                'nickname': nickname,
                'special_name': special_name,
                'client_id': client_id
            },
            'POST'
        )
        
        return result
    
    @classmethod
    def get_pending_requests(cls, account_id=None, password=None):
        if not account_id:
            account_id = cls._get_account_id()
        
        result = cls._make_request(
            '/api/army/requests',
            {'account_id': account_id, 'password': password}
        )
        
        return result
    
    @classmethod
    def respond_request(cls, request_id, action, admin_account_id=None, password=None):
        if not admin_account_id:
            admin_account_id = cls._get_account_id()
        
        result = cls._make_request(
            '/api/army/request/respond',
            {
                'admin_account_id': admin_account_id,
                'request_id': request_id,
                'action': action,
                'password': password
            },
            'POST'
        )
        
        return result
    
    @classmethod
    def send_chat_message(cls, message, account_id=None):
        if not account_id:
            account_id = cls._get_account_id()
        
        result = cls._make_request(
            '/api/army/chat/send',
            {
                'account_id': account_id,
                'message': message
            },
            'POST'
        )
        
        return result
    
    @classmethod
    def get_chat_messages(cls, account_id=None, limit=50):
        if not account_id:
            account_id = cls._get_account_id()
        
        result = cls._make_request(
            '/api/army/chat/get',
            {'account_id': account_id, 'limit': limit}
        )
        
        return result
    
    @classmethod
    def send_help_request(cls, server_info=None, account_id=None):
        if not account_id:
            account_id = cls._get_account_id()
        
        if not server_info:
            try:
                session = get_foreground_host_session()
                if session:
                    server_info = {
                        'name': session.get('name', 'Unknown'),
                        'map': session.get('map', 'Unknown'),
                        'mode': session.get('mode', 'Unknown'),
                        'players': len(get_game_roster())
                    }
                else:
                    server_info = {'name': 'Unknown', 'players': 0}
            except:
                server_info = {'name': 'Unknown', 'players': 0}
        
        result = cls._make_request(
            '/api/army/help',
            {
                'account_id': account_id,
                'server_info': server_info
            },
            'POST'
        )
        
        return result
    
    @classmethod
    def update_status(cls, is_online=True, server_info=None, account_id=None):
        if not account_id:
            account_id = cls._get_account_id()
        
        result = cls._make_request(
            '/api/army/status',
            {
                'account_id': account_id,
                'is_online': is_online,
                'server_info': server_info
            },
            'POST'
        )
        
        return result
    
    @classmethod
    def leave_army(cls, account_id=None):
        if not account_id:
            account_id = cls._get_account_id()
        
        result = cls._make_request(
            '/api/army/leave',
            {'account_id': account_id},
            'POST'
        )
        
        return result

# ============================================
# بخش 3: کلاس‌های UI
# ============================================

class ArmyUI:
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
            scale=ArmyUI.UIS() + ps,
            transition='in_scale',
            color=(0.18, 0.18, 0.18),
            **filtered_kwargs
        )
        cw(r, on_outside_click_call=CallPartial(ArmyUI.swish, t=r))
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

class ArmyPanel:
    def __init__(self, source):
        if hasattr(self, 'w') and self.w:
            try:
                ArmyUI.swish(self.w)
            except:
                pass
        
        self.source = source
        self.account_id = ArmyManager._get_account_id()
        self.nickname = ArmyManager._get_nickname()
        self.special_name = ArmyManager._get_special_name()
        
        print(f"🔍 Account ID: {self.account_id}")
        print(f"🔍 Special Name: {self.special_name}")
        
        self.is_member = ArmyManager.is_member(self.account_id)
        print(f"🔍 Is member: {self.is_member}")
        
        w = self.w = ArmyUI.cw(
            source=source,
            size=(420, 520) if self.is_member else (400, 500),
            ps=ArmyUI.UIS() * 0.8
        )
        
        tw(
            parent=w,
            text=f'🐜 {ARMY_NAME}',
            scale=1.2,
            position=(200, 490),
            h_align='center',
            color=(0.8, 0.6, 0.2)
        )
        
        # نمایش آیدی بازی
        tw(
            parent=w,
            text=f'🆔 آیدی بازی: {self.account_id}',
            position=(20, 460),
            color=(0.6, 0.8, 1)
        )
        
        # نمایش اسم خاص
        tw(
            parent=w,
            text=f'👤 اسم خاص: {self.special_name}',
            position=(20, 430),
            color=(0.8, 0.8, 1)
        )
        
        if self.is_member:
            tw(
                parent=w,
                text='✅ عضو ارتش',
                position=(320, 460),
                color=(0, 1, 0)
            )
        else:
            tw(
                parent=w,
                text='❌ غیرعضو',
                position=(320, 460),
                color=(1, 0.5, 0)
            )
        
        member_count = ArmyManager.get_member_count()
        tw(
            parent=w,
            text=f'👥 تعداد اعضا: {member_count.get("total_members", 0)} نفر',
            position=(20, 400),
            color=(0.8, 1, 0.8)
        )
        
        scroll_y = 60
        scroll_h = 350 if self.is_member else 300
        scroll = sw(
            parent=w,
            size=(380, scroll_h),
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
        
        if not self.is_member:
            # دکمه ثبت‌نام با ورودی اسم خاص
            ArmyUI.bw(
                parent=column,
                label='📝 ثبت نام در ارتش',
                size=(340, btn_h),
                position=(10, btn_y),
                on_activate_call=CallStrict(self._show_join_panel),
                color=(0.1, 0.3, 0.1)
            )
            btn_y += btn_h + 5
        
        if self.is_member:
            ArmyUI.bw(
                parent=column,
                label='👥 مشاهده اعضا',
                size=(340, btn_h),
                position=(10, btn_y),
                on_activate_call=CallStrict(self._show_members),
                color=(0.1, 0.2, 0.3)
            )
            btn_y += btn_h + 5
            
            ArmyUI.bw(
                parent=column,
                label='💬 چت ارتش',
                size=(340, btn_h),
                position=(10, btn_y),
                on_activate_call=CallStrict(self._show_chat),
                color=(0.1, 0.3, 0.2)
            )
            btn_y += btn_h + 5
            
            ArmyUI.bw(
                parent=column,
                label='🆘 درخواست کمک',
                size=(340, btn_h),
                position=(10, btn_y),
                on_activate_call=CallStrict(self._send_help),
                color=(0.3, 0.1, 0.1)
            )
            btn_y += btn_h + 5
            
            ArmyUI.bw(
                parent=column,
                label='🚪 خروج از ارتش',
                size=(340, btn_h),
                position=(10, btn_y),
                on_activate_call=CallStrict(self._leave_army),
                color=(0.3, 0.1, 0.1)
            )
            btn_y += btn_h + 5
        
        # دکمه مدیریت - با رمز (برای ادمین)
        ArmyUI.bw(
            parent=column,
            label='⚙️ پنل مدیریت (نیاز به رمز)',
            size=(340, btn_h),
            position=(10, btn_y),
            on_activate_call=CallStrict(self._show_admin_login),
            color=(0.2, 0.1, 0.3)
        )
        btn_y += btn_h + 5
        
        ArmyUI.bw(
            parent=w,
            label='✖ بستن',
            size=(80, 30),
            position=(320, 10),
            on_activate_call=CallPartial(ArmyUI.swish, w),
            color=(0.3, 0.1, 0.1)
        )
        
        ArmyUI.swish()
    
    def _show_join_panel(self):
        """نمایش پنل ثبت‌نام با ورودی اسم خاص"""
        ArmyUI.swish(self.w)
        teck(0.1, CallStrict(JoinPanel, self.source))
    
    def _show_admin_login(self):
        """نمایش پنل ورود رمز ادمین"""
        ArmyUI.swish(self.w)
        teck(0.1, CallStrict(AdminLoginPanel, self.source))
    
    def _show_members(self):
        ArmyUI.swish(self.w)
        teck(0.1, CallStrict(MembersPanel, self.source))
    
    def _show_chat(self):
        ArmyUI.swish(self.w)
        teck(0.1, CallStrict(ChatPanel, self.source))
    
    def _send_help(self):
        server_info = {}
        try:
            session = get_foreground_host_session()
            if session:
                server_info = {
                    'name': session.get('name', 'Unknown'),
                    'map': session.get('map', 'Unknown'),
                    'mode': session.get('mode', 'Unknown'),
                    'players': len(get_game_roster())
                }
        except:
            pass
        
        result = ArmyManager.send_help_request(server_info)
        
        if 'error' in result:
            ArmyUI.err(f'❌ {result["error"]}')
            return
        
        ArmyUI.ok()
        special_name = self.special_name
        server_name = server_info.get('name', 'Unknown')
        push(f'🆘 {special_name} در سرور {server_name} درخواست کمک دارد!', color=(1, 0.8, 0))
        gs('dingSmallHigh').play()
    
    def _leave_army(self):
        result = ArmyManager.leave_army()
        
        if 'error' in result:
            ArmyUI.err(f'❌ {result["error"]}')
            return
        
        ArmyUI.ok()
        push('✅ شما با موفقیت از ارتش خارج شدید!', color=(1, 0.5, 0))
        gs('dingSmallHigh').play()
        
        if hasattr(self, 'w') and self.w:
            ArmyUI.swish(self.w)
            teck(0.1, CallStrict(ArmyPanel, self.source))

# ============================================
# پنل ثبت‌نام با اسم خاص
# ============================================

class JoinPanel:
    def __init__(self, source):
        if hasattr(self, 'w') and self.w:
            try:
                ArmyUI.swish(self.w)
            except:
                pass
        
        self.source = source
        self.account_id = ArmyManager._get_account_id()
        self.nickname = ArmyManager._get_nickname()
        
        w = self.w = ArmyUI.cw(
            source=source,
            size=(400, 250),
            ps=ArmyUI.UIS() * 0.8
        )
        
        tw(
            parent=w,
            text='📝 ثبت نام در ارتش',
            scale=1.2,
            position=(200, 230),
            h_align='center',
            color=(0.8, 0.6, 0.2)
        )
        
        tw(
            parent=w,
            text=f'🆔 آیدی شما: {self.account_id}',
            position=(20, 200),
            color=(0.6, 0.8, 1)
        )
        
        tw(
            parent=w,
            text='اسم خاص خود را وارد کنید:',
            position=(20, 170),
            color=(0.8, 0.8, 1)
        )
        
        self.special_input = tw(
            parent=w,
            maxwidth=250,
            size=(250, 30),
            editable=True,
            v_align='center',
            color=(0.75, 0.75, 0.75),
            position=(20, 140),
            allow_clear_button=False,
            text=ArmyManager._get_special_name()
        )
        
        ArmyUI.bw(
            parent=w,
            label='✅ ثبت درخواست',
            size=(120, 35),
            position=(240, 135),
            on_activate_call=CallStrict(self._send_join_request),
            color=(0.1, 0.3, 0.1)
        )
        
        ArmyUI.bw(
            parent=w,
            label='↩ بازگشت',
            size=(100, 30),
            position=(20, 15),
            on_activate_call=CallPartial(self._close_panel),
            color=(0.2, 0.2, 0.3)
        )
        
        ArmyUI.swish()
    
    def _send_join_request(self):
        special_name = tw(query=self.special_input).strip()
        
        if not special_name:
            ArmyUI.err('⚠️ لطفاً اسم خاص خود را وارد کنید!')
            return
        
        result = ArmyManager.send_join_request(special_name)
        
        if 'error' in result:
            ArmyUI.err(f'❌ {result["error"]}')
            return
        
        ArmyUI.ok()
        push(f'✅ درخواست عضویت با اسم "{special_name}" ثبت شد!', color=(0, 1, 0))
        push('⏳ منتظر تایید ادمین باشید...', color=(1, 1, 0))
        gs('dingSmallHigh').play()
        
        self._close_panel()
        teck(0.5, CallStrict(ArmyPanel, self.source))
    
    def _close_panel(self):
        if hasattr(self, 'w') and self.w:
            ArmyUI.swish(self.w)

# ============================================
# پنل ورود رمز ادمین
# ============================================

class AdminLoginPanel:
    def __init__(self, source):
        if hasattr(self, 'w') and self.w:
            try:
                ArmyUI.swish(self.w)
            except:
                pass
        
        self.source = source
        
        w = self.w = ArmyUI.cw(
            source=source,
            size=(350, 220),
            ps=ArmyUI.UIS() * 0.8
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
            text='رمز ادمین را وارد کنید:',
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
        
        ArmyUI.bw(
            parent=w,
            label='✅ ورود',
            size=(100, 35),
            position=(220, 125),
            on_activate_call=CallStrict(self._check_password),
            color=(0.1, 0.3, 0.1)
        )
        
        ArmyUI.bw(
            parent=w,
            label='↩ بازگشت',
            size=(100, 30),
            position=(20, 15),
            on_activate_call=CallPartial(self._close_panel),
            color=(0.2, 0.2, 0.3)
        )
        
        ArmyUI.swish()
    
    def _check_password(self):
        password = tw(query=self.password_input).strip()
        
        if not password:
            ArmyUI.err('⚠️ لطفاً رمز را وارد کنید!')
            return
        
        if password == ADMIN_PASSWORD:
            ArmyUI.ok()
            push('✅ رمز صحیح است!', color=(0, 1, 0))
            self._close_panel()
            teck(0.5, CallStrict(AdminPanel, self.source))
        else:
            ArmyUI.err('❌ رمز اشتباه است!')
    
    def _close_panel(self):
        if hasattr(self, 'w') and self.w:
            ArmyUI.swish(self.w)

# ============================================
# پنل اعضا
# ============================================

class MembersPanel:
    def __init__(self, source):
        if hasattr(self, 'w') and self.w:
            try:
                ArmyUI.swish(self.w)
            except:
                pass
        
        self.source = source
        self.members_data = ArmyManager.get_members()
        
        w = self.w = ArmyUI.cw(
            source=source,
            size=(450, 450),
            ps=ArmyUI.UIS() * 0.8
        )
        
        tw(
            parent=w,
            text='👥 لیست اعضا',
            scale=1.2,
            position=(225, 420),
            h_align='center',
            color=(0.8, 0.6, 0.2)
        )
        
        if not self.members_data or 'error' in self.members_data:
            tw(
                parent=w,
                text=f'❌ {self.members_data.get("error", "خطا در دریافت اطلاعات")}',
                position=(225, 380),
                h_align='center',
                color=(1, 0.5, 0)
            )
        else:
            total = self.members_data.get('total', 0)
            tw(
                parent=w,
                text=f'تعداد کل: {total} نفر',
                position=(20, 380),
                color=(0.8, 1, 0.8)
            )
            
            scroll = sw(
                parent=w,
                size=(410, 310),
                position=(20, 55),
                color=(0.1, 0.1, 0.1),
                highlight=False
            )
            column = clw(
                parent=scroll,
                left_border=10,
                top_border=10,
                bottom_border=10
            )
            
            header_row = cw(
                parent=column,
                size=(390, 30),
                background=False
            )
            tw(
                parent=header_row,
                text='اسم خاص',
                position=(10, 5),
                color=(1, 1, 0.5),
                scale=0.8
            )
            tw(
                parent=header_row,
                text='وضعیت',
                position=(250, 5),
                color=(1, 1, 0.5),
                scale=0.8
            )
            
            for account_id, data in self.members_data.get('members', {}).items():
                row = cw(
                    parent=column,
                    size=(390, 30),
                    background=False
                )
                
                special_name = data.get('special_name', data.get('nickname', 'Unknown'))
                is_online = data.get('is_online', False)
                
                tw(
                    parent=row,
                    text=special_name,
                    position=(10, 5),
                    color=(0.8, 0.8, 1)
                )
                
                status_text = '🟢 آنلاین' if is_online else '⚫ آفلاین'
                status_color = (0, 1, 0) if is_online else (0.5, 0.5, 0.5)
                tw(
                    parent=row,
                    text=status_text,
                    position=(250, 5),
                    color=status_color
                )
        
        ArmyUI.bw(
            parent=w,
            label='↩ بازگشت',
            size=(100, 30),
            position=(20, 15),
            on_activate_call=CallPartial(ArmyUI.swish, w),
            color=(0.2, 0.2, 0.3)
        )
        
        ArmyUI.swish()

# ============================================
# پنل چت
# ============================================

class ChatPanel:
    def __init__(self, source):
        if hasattr(self, 'w') and self.w:
            try:
                ArmyUI.swish(self.w)
            except:
                pass
        
        self.source = source
        self.account_id = ArmyManager._get_account_id()
        self.special_name = ArmyManager._get_special_name()
        
        w = self.w = ArmyUI.cw(
            source=source,
            size=(500, 450),
            ps=ArmyUI.UIS() * 0.8
        )
        
        tw(
            parent=w,
            text='💬 چت ارتش',
            scale=1.2,
            position=(250, 420),
            h_align='center',
            color=(0.8, 0.6, 0.2)
        )
        
        tw(
            parent=w,
            text='🔄 پیام‌ها هر ۲۴ ساعت پاک می‌شوند',
            position=(250, 395),
            h_align='center',
            scale=0.7,
            color=(0.5, 0.5, 0.5)
        )
        
        self.chat_messages = ArmyManager.get_chat_messages(self.account_id)
        
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
            text='پیام خود را وارد کنید...'
        )
        
        ArmyUI.bw(
            parent=w,
            label='📤 ارسال',
            size=(80, 30),
            position=(350, 55),
            on_activate_call=CallStrict(self._send_message),
            color=(0.1, 0.3, 0.1)
        )
        
        ArmyUI.bw(
            parent=w,
            label='↩ بازگشت',
            size=(100, 30),
            position=(20, 15),
            on_activate_call=CallPartial(self._close_panel),
            color=(0.2, 0.2, 0.3)
        )
        
        self.update_timer = AppTimer(3, CallStrict(self._auto_refresh), repeat=True)
        
        ArmyUI.swish()
    
    def _display_messages(self):
        for child in self.chat_container.get_children():
            child.delete()
        
        if not self.chat_messages or 'error' in self.chat_messages:
            tw(
                parent=self.chat_container,
                text='❌ خطا در دریافت پیام‌ها',
                position=(220, 120),
                h_align='center',
                color=(1, 0.5, 0)
            )
            return
        
        chat_list = self.chat_messages.get('chat', [])
        if not chat_list:
            tw(
                parent=self.chat_container,
                text='💬 پیامی وجود ندارد',
                position=(220, 120),
                h_align='center',
                color=(0.5, 0.5, 0.5)
            )
            return
        
        y_pos = len(chat_list) * 25 + 10
        for msg in reversed(chat_list):
            sender_special = msg.get('sender_special_name', msg.get('sender_nickname', 'Unknown'))
            message = msg.get('message', '')
            timestamp = msg.get('timestamp', 0)
            
            time_str = time.strftime('%H:%M', time.localtime(timestamp / 1000))
            
            color = (0.8, 0.8, 1)
            if sender_special == self.special_name:
                color = (0.6, 1, 0.6)
            
            tw(
                parent=self.chat_container,
                text=f'{sender_special} [{time_str}]:',
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
        if not message or message == 'پیام خود را وارد کنید...':
            ArmyUI.err('⚠️ پیام را وارد کنید!')
            return
        
        result = ArmyManager.send_chat_message(message, self.account_id)
        
        if 'error' in result:
            ArmyUI.err(f'❌ {result["error"]}')
            return
        
        ArmyUI.ok()
        tw(self.input_field, text='')
        
        self.chat_messages = ArmyManager.get_chat_messages(self.account_id)
        self._display_messages()
    
    def _auto_refresh(self):
        if not hasattr(self, 'w') or not self.w:
            if hasattr(self, 'update_timer'):
                self.update_timer = None
            return
        
        try:
            new_chat = ArmyManager.get_chat_messages(self.account_id)
            if new_chat != self.chat_messages:
                self.chat_messages = new_chat
                self._display_messages()
        except:
            pass
    
    def _close_panel(self):
        if hasattr(self, 'update_timer'):
            self.update_timer = None
        ArmyUI.swish(self.w)

# ============================================
# پنل ادمین (با رمز)
# ============================================

class AdminPanel:
    def __init__(self, source):
        if hasattr(self, 'w') and self.w:
            try:
                ArmyUI.swish(self.w)
            except:
                pass
        
        self.source = source
        self.account_id = ArmyManager._get_account_id()
        
        w = self.w = ArmyUI.cw(
            source=source,
            size=(550, 450),
            ps=ArmyUI.UIS() * 0.8
        )
        
        tw(
            parent=w,
            text='⚙️ پنل مدیریت',
            scale=1.2,
            position=(275, 420),
            h_align='center',
            color=(0.8, 0.6, 0.2)
        )
        
        tw(
            parent=w,
            text=f'🔒 دسترسی با رمز تایید شد',
            position=(275, 395),
            h_align='center',
            scale=0.7,
            color=(0, 1, 0)
        )
        
        self.requests_data = ArmyManager.get_pending_requests(self.account_id, ADMIN_PASSWORD)
        
        if self.requests_data and 'total' in self.requests_data:
            tw(
                parent=w,
                text=f'📨 درخواست‌های جدید: {self.requests_data["total"]}',
                position=(20, 370),
                color=(1, 1, 0)
            )
        else:
            tw(
                parent=w,
                text='📨 هیچ درخواست جدیدی وجود ندارد',
                position=(20, 370),
                color=(0.5, 0.5, 0.5)
            )
        
        scroll = sw(
            parent=w,
            size=(510, 290),
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
        
        if self.requests_data and 'requests' in self.requests_data:
            requests = self.requests_data['requests']
            for req_id, data in requests.items():
                row = cw(
                    parent=column,
                    size=(490, 40),
                    background=False
                )
                
                special_name = data.get('special_name', data.get('nickname', 'Unknown'))
                client_id = data.get('client_id', -1)
                account_id = data.get('account_id', '')
                
                tw(
                    parent=row,
                    text=f'👤 {special_name}',
                    position=(10, 10),
                    color=(0.8, 0.8, 1)
                )
                
                tw(
                    parent=row,
                    text=f'ID: {client_id}',
                    position=(170, 10),
                    scale=0.7,
                    color=(0.5, 0.5, 0.5)
                )
                
                tw(
                    parent=row,
                    text=f'ACC: {account_id[:10]}...',
                    position=(250, 10),
                    scale=0.5,
                    color=(0.3, 0.3, 0.3)
                )
                
                ArmyUI.bw(
                    parent=row,
                    label='✅ قبول',
                    size=(60, 25),
                    position=(360, 8),
                    on_activate_call=CallStrict(self._respond, req_id, 'accept'),
                    color=(0.1, 0.3, 0.1)
                )
                
                ArmyUI.bw(
                    parent=row,
                    label='❌ رد',
                    size=(60, 25),
                    position=(430, 8),
                    on_activate_call=CallStrict(self._respond, req_id, 'reject'),
                    color=(0.3, 0.1, 0.1)
                )
        
        ArmyUI.bw(
            parent=w,
            label='↩ بازگشت',
            size=(100, 30),
            position=(20, 15),
            on_activate_call=CallPartial(ArmyUI.swish, w),
            color=(0.2, 0.2, 0.3)
        )
        
        ArmyUI.swish()
    
    def _respond(self, request_id, action):
        result = ArmyManager.respond_request(request_id, action, self.account_id, ADMIN_PASSWORD)
        
        if 'error' in result:
            ArmyUI.err(f'❌ {result["error"]}')
            return
        
        ArmyUI.ok()
        push(f'✅ {result.get("message", "عملیات با موفقیت انجام شد!")}', color=(0, 1, 0))
        gs('dingSmallHigh').play()
        
        if hasattr(self, 'w') and self.w:
            ArmyUI.swish(self.w)
            teck(0.1, CallStrict(AdminPanel, self.source))

# ============================================
# بخش 5: پلاگین اصلی
# ============================================

# ba_meta require api 9
# ba_meta export babase.Plugin

class SosooliArmyPlugin(Plugin):
    """پلاگین ارتش سوسولی - نسخه نهایی با تشخیص آیدی و رمز ادمین"""
    
    def __init__(self):
        print(f"🐜 {ARMY_NAME} - Plugin Activated!")
        print(f"🔑 Admin special name: {ADMIN_SPECIAL_NAME}")
        print(f"🔒 Admin password: {ADMIN_PASSWORD}")
        print(f"📡 Worker URL: {WORKER_URL}")
        
        # تست تشخیص آیدی
        test_account = GameDetector.get_account_id()
        test_special = GameDetector.get_special_name()
        print(f"🔍 Detected Account ID: {test_account}")
        print(f"🔍 Detected Special Name: {test_special}")
        
        self._start_status_updater()
        self._start_chat_listener()
        self._inject_party_button()
    
    def _start_status_updater(self):
        def update_status():
            try:
                account_id = ArmyManager._get_account_id()
                if ArmyManager.is_member(account_id):
                    server_info = {}
                    try:
                        session = get_foreground_host_session()
                        if session:
                            server_info = {
                                'name': session.get('name', 'Unknown'),
                                'map': session.get('map', 'Unknown'),
                                'mode': session.get('mode', 'Unknown'),
                                'players': len(get_game_roster())
                            }
                    except:
                        pass
                    
                    ArmyManager.update_status(True, server_info, account_id)
            except Exception as e:
                print(f"Status update error: {e}")
            
            teck(30, CallStrict(update_status))
        
        teck(2, CallStrict(update_status))
    
    def _start_chat_listener(self):
        self.last_messages = []
        self.ignore_messages = []
        
        def listen_chat():
            try:
                messages = GCM()
                if messages != self.last_messages:
                    new_msgs = messages[len(self.last_messages):]
                    for msg in new_msgs:
                        if ': ' in msg:
                            parts = msg.split(': ', 1)
                            if len(parts) >= 2:
                                sender, content = parts
                                self._process_command(sender.strip(), content.strip())
                    self.last_messages = messages
            except Exception as e:
                print(f"Chat listener error: {e}")
            
            teck(1, CallStrict(listen_chat))
        
        teck(1, CallStrict(listen_chat))
    
    def _process_command(self, sender, message):
        if not message.startswith('!'):
            return
        
        command = message[1:].strip().lower()
        
        if command == 'army':
            push('🐜 برای دسترسی به ارتش سوسولی، از دکمه 🐜 در پنل پارتی استفاده کنید!', color=(0.8, 0.6, 0.2))
        
        elif command.startswith('help'):
            account_id = ArmyManager._get_account_id()
            if not ArmyManager.is_member(account_id):
                push('❌ فقط اعضای ارتش می‌توانند درخواست کمک بفرستند!', color=(1, 0, 0))
                return
            
            result = ArmyManager.send_help_request()
            if 'error' not in result:
                push('🆘 درخواست کمک شما به تمام اعضا ارسال شد!', color=(0, 1, 0))
    
    def _inject_party_button(self):
        try:
            from bauiv1lib import party
            
            original_init = party.PartyWindow.__init__
            
            def new_init(self, *args, **kwargs):
                result = original_init(self, *args, **kwargs)
                
                try:
                    btn_x = self._width - 530
                    btn_y = self._height - 260
                    
                    army_btn = ArmyUI.bw(
                        icon=gt('achievementCrossHair'),
                        position=(btn_x, btn_y),
                        parent=self._root_widget,
                        iconscale=1.2,
                        size=(30, 30),
                        label='',
                        color=(0.3, 0.2, 0.1)
                    )
                    
                    bw(army_btn, on_activate_call=CallPartial(ArmyPanel, self._root_widget))
                    
                except Exception as e:
                    print(f"Error adding army button: {e}")
                
                return result
            
            party.PartyWindow.__init__ = new_init
            print("🐜 Army button injected into party panel!")
            
        except Exception as e:
            print(f"Error injecting party button: {e}")
    
    def __del__(self):
        print(f"🐜 {ARMY_NAME} - Plugin Deactivated!")