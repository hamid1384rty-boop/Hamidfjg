# ============================================
# ارتش سوسولی - سیستم مدیریت ارتش در بازی
# Bombsquad Mod - نسخه نهایی با رفع خطاها
# ============================================

import json
import time
import urllib.request
import urllib.error
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
    get_foreground_host_session
)

# ============================================
# تنظیمات
# ============================================

WORKER_URL = "https://summer-hall-b302.hamid1384rty.workers.dev"
ARMY_NAME = "ارتش سوسولی"
ADMIN_SPECIAL_NAME = "sosoliplus"

# ============================================
# کلاس مدیریت ارتش
# ============================================

class ArmyManager:
    _instance = None
    _cache = {}
    _cache_time = {}
    CACHE_DURATION = 30
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @staticmethod
    def _get_account_id():
        try:
            if hasattr(APP, 'plus'):
                account_name = APP.plus.get_v1_account_name()
                if account_name:
                    return account_name
            return APP.config.get('Player Name', 'Unknown')
        except:
            return 'Unknown'
    
    @staticmethod
    def _get_nickname():
        try:
            return APP.config.get('Player Name', 'Unknown')
        except:
            return 'Unknown'
    
    @staticmethod
    def _get_special_name():
        """دریافت اسم خاص با روش‌های مختلف"""
        try:
            # روش 1: از Roster
            roster = get_game_roster()
            nickname = ArmyManager._get_nickname()
            
            for client in roster:
                if 'players' in client and client['players']:
                    for player in client['players']:
                        if player.get('name', '') == nickname:
                            special = client.get('display_string', '')
                            if special:
                                print(f"✅ Special name from roster: {special}")
                                return special
                            else:
                                print("⚠️ Display string is empty, using nickname")
            
            # روش 2: از تنظیمات بازی
            special = APP.config.get('Player Name', '')
            if special:
                print(f"✅ Special name from config: {special}")
                return special
            
            # روش 3: از نام نمایشی
            return nickname
        except Exception as e:
            print(f"❌ Error getting special name: {e}")
            return ArmyManager._get_nickname()
    
    @staticmethod
    def _get_client_id():
        try:
            roster = get_game_roster()
            nickname = ArmyManager._get_nickname()
            for client in roster:
                if 'players' in client and client['players']:
                    for p in client['players']:
                        if p.get('name', '') == nickname:
                            return client.get('client_id', -1)
            return -1
        except:
            return -1
    
    @staticmethod
    def _make_request(endpoint, data=None, method='GET'):
        url = f"{WORKER_URL}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET' and data:
                params = '&'.join([f"{k}={v}" for k, v in data.items()])
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
            
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result
                
        except urllib.error.HTTPError as e:
            try:
                error_data = json.loads(e.read().decode('utf-8'))
                return error_data
            except:
                return {'error': f'HTTP Error: {e.code}', 'code': 'HTTP_ERROR'}
        except Exception as e:
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
    
    # ===== متدهای عمومی =====
    
    @classmethod
    def is_member(cls, account_id=None):
        if not account_id:
            account_id = cls._get_account_id()
        
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
    def send_join_request(cls, nickname=None, account_id=None, client_id=None):
        if not account_id:
            account_id = cls._get_account_id()
        if not nickname:
            nickname = cls._get_nickname()
        if not client_id:
            client_id = cls._get_client_id()
        
        special_name = cls._get_special_name()
        
        if not special_name or special_name == nickname:
            special_name = nickname
        
        # اگر اسم خاص sosoliplus هست، لاگ کن
        if special_name.lower() == 'sosoliplus':
            print(f"🔥 ADMIN DETECTED: {special_name}")
        
        print(f"📝 Sending join request: account={account_id}, special={special_name}")
        
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
        
        print(f"📝 Join response: {result}")
        return result
    
    @classmethod
    def get_pending_requests(cls, account_id=None):
        if not account_id:
            account_id = cls._get_account_id()
        
        result = cls._make_request(
            '/api/army/requests',
            {'account_id': account_id}
        )
        
        return result
    
    @classmethod
    def respond_request(cls, request_id, action, admin_account_id=None):
        if not admin_account_id:
            admin_account_id = cls._get_account_id()
        
        result = cls._make_request(
            '/api/army/request/respond',
            {
                'admin_account_id': admin_account_id,
                'request_id': request_id,
                'action': action
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
    
    @classmethod
    def get_user_info(cls, target_account, account_id=None):
        if not account_id:
            account_id = cls._get_account_id()
        
        result = cls._make_request(
            '/api/army/user-info',
            {
                'account_id': account_id,
                'target_account': target_account
            }
        )
        
        return result
    
    @classmethod
    def is_admin(cls, account_id=None):
        if not account_id:
            account_id = cls._get_account_id()
        
        result = cls._make_request(
            '/api/army/check-admin',
            {'account_id': account_id}
        )
        
        if result and result.get('is_admin'):
            return True
        
        return False

# ============================================
# کلاس‌های UI
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
# پنل اصلی ارتش
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
        
        self.is_member = ArmyManager.is_member(self.account_id)
        
        w = self.w = ArmyUI.cw(
            source=source,
            size=(400, 500) if self.is_member else (380, 450),
            ps=ArmyUI.UIS() * 0.8
        )
        
        tw(
            parent=w,
            text=f'🐜 {ARMY_NAME}',
            scale=1.2,
            position=(200, 470),
            h_align='center',
            color=(0.8, 0.6, 0.2)
        )
        
        tw(
            parent=w,
            text=f'👤 {self.special_name}',
            position=(20, 440),
            color=(0.8, 0.8, 1)
        )
        
        if self.is_member:
            tw(
                parent=w,
                text='✅ عضو ارتش',
                position=(300, 440),
                color=(0, 1, 0)
            )
        else:
            tw(
                parent=w,
                text='❌ غیرعضو',
                position=(300, 440),
                color=(1, 0.5, 0)
            )
        
        member_count = ArmyManager.get_member_count()
        tw(
            parent=w,
            text=f'👥 تعداد اعضا: {member_count.get("total_members", 0)} نفر',
            position=(20, 410),
            color=(0.8, 1, 0.8)
        )
        
        scroll_y = 60
        scroll_h = 340 if self.is_member else 290
        scroll = sw(
            parent=w,
            size=(360, scroll_h),
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
        btn_h = 40
        
        if not self.is_member:
            ArmyUI.bw(
                parent=column,
                label='📝 ثبت نام در ارتش',
                size=(340, btn_h),
                position=(10, btn_y),
                on_activate_call=CallStrict(self._join_request),
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
                color=(0.3, 0.1, 0.1