# SinglCMD - Server Code System (نسخه دائمی با سیستم اشتراک آنلاین)
# Copyright 2025 - Modified from AutoRespond
import datetime
import time
import json
import urllib.request
import urllib.error
from base64 import b64encode
from babase import Plugin
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
    columnwidget as clw
)
from bascenev1 import (
    get_chat_messages as GCM,
    chatmessage as CM,
    get_game_roster,
    disconnect_client
)

# ============================================
# سیستم اشتراک - دریافت از Worker با کش ۱۲ ساعته
# ============================================
class SubscriptionManager:
    WORKER_URL = "https://square-cherry-6ae3.hamid1384rty.workers.dev/api/public/subs"
    CACHE_KEY = "scmd_sub_cache"
    CACHE_TIME_KEY = "scmd_sub_cache_time"
    CACHE_DURATION = 12 * 60 * 60  # 12 ساعت

    @staticmethod
    def _fetch_from_server():
        """دریافت مستقیم از سرور بدون احراز هویت"""
        try:
            req = urllib.request.Request(
                SubscriptionManager.WORKER_URL,
                headers={"User-Agent": "Bombsquad/1.0"}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = response.read().decode('utf-8')
                json_data = json.loads(data)
                
                # ذخیره در کش
                var(SubscriptionManager.CACHE_KEY, json.dumps(json_data))
                var(SubscriptionManager.CACHE_TIME_KEY, time.time())
                return json_data
                
        except Exception as e:
            print(f"Error fetching subscription: {e}")
            return None

    @staticmethod
    def _get_cached_data():
        """دریافت داده از کش"""
        cached = var(SubscriptionManager.CACHE_KEY)
        if cached:
            try:
                return json.loads(cached)
            except:
                return None
        return None

    @staticmethod
    def _is_cache_valid():
        """بررسی اعتبار کش"""
        cache_time = var(SubscriptionManager.CACHE_TIME_KEY)
        if not cache_time:
            return False
        return (time.time() - cache_time) < SubscriptionManager.CACHE_DURATION

    @staticmethod
    def get_subscription_data(sub_name):
        """دریافت اطلاعات یک اشتراک خاص با نام"""
        if SubscriptionManager._is_cache_valid():
            data = SubscriptionManager._get_cached_data()
            if data:
                for sub in data:
                    if sub.get('name', '').lower() == sub_name.lower():
                        return sub
                return None
        
        data = SubscriptionManager._fetch_from_server()
        if data:
            for sub in data:
                if sub.get('name', '').lower() == sub_name.lower():
                    return sub
            return None
        
        old_data = SubscriptionManager._get_cached_data()
        if old_data:
            for sub in old_data:
                if sub.get('name', '').lower() == sub_name.lower():
                    return sub
        
        return None

    @staticmethod
    def check_subscription(sub_name):
        """بررسی اعتبار یک اشتراک خاص"""
        sub_data = SubscriptionManager.get_subscription_data(sub_name)
        if sub_data:
            return sub_data.get('days', 0) > 0
        return False

    @staticmethod
    def get_remaining_days(sub_name):
        """دریافت تعداد روزهای باقی‌مانده یک اشتراک خاص"""
        sub_data = SubscriptionManager.get_subscription_data(sub_name)
        if sub_data:
            return sub_data.get('days', 0)
        return 0

    @staticmethod
    def get_all_subscriptions():
        """دریافت لیست تمام اشتراک‌ها"""
        if SubscriptionManager._is_cache_valid():
            data = SubscriptionManager._get_cached_data()
            if data:
                return data
        
        data = SubscriptionManager._fetch_from_server()
        if data:
            return data
        
        old_data = SubscriptionManager._get_cached_data()
        if old_data:
            return old_data
        
        return []

    @staticmethod
    def force_refresh():
        """اجبار به آپدیت کش"""
        var(SubscriptionManager.CACHE_TIME_KEY, 0)
        return SubscriptionManager._fetch_from_server() is not None

# ============================================
# کلاس پنل اشتراک (فقط یک اشتراک خاص با کلمه کلیدی)
# ============================================
class SubscriptionPanel:
    def __init__(s, t):
        if hasattr(s, 'w') and s.w:
            try:
                SC.swish(s.w)
            except:
                pass
        
        w = s.w = SC.cw(
            source=t,
            size=(380, 320),
            ps=SC.UIS()*0.8
        )
        
        tw(
            parent=w,
            text='📋 مدیریت اشتراک آنلاین',
            scale=1.1,
            position=(180, 290),
            h_align='center',
            color=(0.6, 1, 0.6)
        )
        
        # نمایش اشتراک فعال فعلی
        current_sub = var('current_subscription') or 'None'
        tw(
            parent=w,
            text=f'اشتراک فعلی: {current_sub}',
            position=(20, 250),
            color=(0.8, 1, 0.8) if current_sub != 'None' else (1, 0.6, 0.6)
        )
        
        # نمایش روزهای باقی‌مانده اشتراک فعلی
        if current_sub != 'None':
            remaining = SubscriptionManager.get_remaining_days(current_sub)
            sub_status = '✅ فعال' if remaining > 0 else '❌ منقضی'
            tw(
                parent=w,
                text=f'روز باقی‌مانده: {remaining}  |  وضعیت: {sub_status}',
                position=(20, 220),
                color=(0, 1, 0) if remaining > 0 else (1, 0.5, 0)
            )
        
        # فیلد ورود کلمه کلیدی اشتراک
        tw(
            parent=w,
            text='کلمه کلیدی اشتراک را وارد کنید:',
            position=(20, 180),
            color=(0.8, 0.8, 1)
        )
        s.sub_input = tw(
            parent=w,
            maxwidth=200,
            size=(200, 30),
            editable=True,
            v_align='center',
            color=(0.75, 0.75, 0.75),
            position=(20, 150),
            allow_clear_button=False,
            text=current_sub if current_sub != 'None' else ''
        )
        
        tw(
            parent=w,
            text='مثال: premium, vip, gold',
            position=(230, 155),
            scale=0.6,
            color=(0.5, 0.5, 0.5)
        )
        
        SC.bw(
            parent=w,
            label='✅ فعال‌سازی اشتراک',
            size=(150, 35),
            position=(230, 148),
            on_activate_call=CallStrict(s._activate_subscription),
            color=(0.1, 0.3, 0.1)
        )
        
        SC.bw(
            parent=w,
            label='🔄 بروزرسانی اشتراک‌ها',
            size=(170, 35),
            position=(20, 100),
            on_activate_call=CallStrict(s._refresh_subscriptions),
            color=(0.1, 0.3, 0.1)
        )
        
        SC.bw(
            parent=w,
            label='📊 وضعیت سرور',
            size=(150, 35),
            position=(200, 100),
            on_activate_call=CallStrict(s._check_server_status),
            color=(0.1, 0.1, 0.3)
        )
        
        SC.bw(
            parent=w,
            label='❌ حذف اشتراک',
            size=(150, 35),
            position=(20, 55),
            on_activate_call=CallStrict(s._clear_subscription),
            color=(0.3, 0.1, 0.1)
        )
        
        SC.swish()
    
    def _activate_subscription(s):
        """فعال‌سازی اشتراک با کلمه کلیدی"""
        sub_key = tw(query=s.sub_input).strip()
        if not sub_key:
            SC.err('⚠️ لطفاً کلمه کلیدی اشتراک را وارد کنید!')
            return
        
        # بررسی اینکه آیا اشتراک با این نام وجود دارد
        sub_data = SubscriptionManager.get_subscription_data(sub_key)
        if sub_data:
            remaining = sub_data.get('days', 0)
            if remaining > 0:
                var('current_subscription', sub_key)
                SC.ok()
                push(f'✅ اشتراک "{sub_key}" با {remaining} روز فعال شد', color=(0, 1, 0))
            else:
                SC.err(f'❌ اشتراک "{sub_key}" منقضی شده است!')
                return
        else:
            SC.err(f'❌ اشتراک "{sub_key}" یافت نشد!')
            return
        
        # رفرش پنل
        if hasattr(s, 'w') and s.w:
            SC.swish(s.w)
            teck(0.1, CallStrict(s.__init__, s.source))
    
    def _refresh_subscriptions(s):
        """بروزرسانی دستی اشتراک‌ها از سرور"""
        if SubscriptionManager.force_refresh():
            SC.ok()
            push('✅ اشتراک‌ها با موفقیت بروزرسانی شدند', color=(0, 1, 0))
            if hasattr(s, 'w') and s.w:
                SC.swish(s.w)
                teck(0.1, CallStrict(s.__init__, s.source))
        else:
            SC.err('❌ خطا در ارتباط با سرور!')
    
    def _check_server_status(s):
        """بررسی وضعیت سرور"""
        try:
            req = urllib.request.Request(
                SubscriptionManager.WORKER_URL,
                headers={"User-Agent": "Bombsquad/1.0"}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    push('✅ سرور آنلاین است', color=(0, 1, 0))
                else:
                    push(f'⚠️ سرور پاسخ داد اما با خطا: {response.status}', color=(1, 0.5, 0))
        except Exception as e:
            push('❌ سرور در دسترس نیست!', color=(1, 0, 0))
    
    def _clear_subscription(s):
        """حذف اشتراک فعال"""
        var('current_subscription', 'None')
        SC.ok()
        push('❌ اشتراک حذف شد', color=(1, 0.5, 0))
        if hasattr(s, 'w') and s.w:
            SC.swish(s.w)
            teck(0.1, CallStrict(s.__init__, s.source))

# ============================================
# کلاس‌های اصلی (با تغییرات برای اشتراک اختصاصی)
# ============================================
class Add:
    def __init__(s,t):
        if hasattr(s, 'w') and s.w:
            try:
                SC.swish(s.w)
            except:
                pass
        
        w = s.w = SC.cw(
            source=t,
            size=(320,230),
            ps=SC.UIS()*0.8
        )
        tw(
            parent=w,
            text='Input code:',
            position=(40,190)
        )
        s.inp = tw(
            parent=w,
            maxwidth=240,
            size=(240,30),
            editable=True,
            v_align='center',
            color=(0.75,0.75,0.75),
            position=(40,158),
            allow_clear_button=False
        )
        tw(
            parent=w,
            text='Output code:',
            position=(40,120)
        )
        s.out = tw(
            parent=w,
            maxwidth=240,
            size=(240,30),
            editable=True,
            v_align='center',
            color=(0.75,0.75,0.75),
            position=(40,88),
            allow_clear_button=False
        )
        tw(
            parent=w,
            text='Delay (0-2 seconds):',
            position=(40,50)
        )
        s.delay = tw(
            parent=w,
            maxwidth=100,
            size=(100,30),
            editable=True,
            v_align='center',
            color=(0.75,0.75,0.75),
            position=(40,18),
            allow_clear_button=False,
            text='0' 
        )
        SC.bw(
            parent=w,
            label='Add',
            size=(60,35),
            position=(240,15),
            on_activate_call=CallStrict(s._add)
        )
        SC.swish()
    
    def _add(s):
        # بررسی اشتراک اختصاصی
        current_sub = var('current_subscription')
        if not current_sub or current_sub == 'None':
            SC.err('⛔ ابتدا یک اشتراک را در پنل Subscription فعال کنید!')
            return
        
        if not SubscriptionManager.check_subscription(current_sub):
            SC.err(f'⛔ اشتراک "{current_sub}" منقضی شده است!')
            return
        
        inp = tw(query=s.inp).strip()
        out = tw(query=s.out).strip()
        delay_text = tw(query=s.delay).strip()
        
        if not inp or not out:
            SC.err('Enter both codes!')
            return
        try:
            delay = float(delay_text)
            if delay < 0 or delay > 2:
                SC.err('Delay must be between 0 and 2 seconds!')
                return
        except ValueError:
            SC.err('Enter a valid number for delay!')
            return
        cmds = var('cmds') or {}
        inp_key = inp.lower()
        if inp_key in cmds:
            SC.err('Input code already exists!')
            return
        cmds[inp_key] = {
            'out': out.lower(),
            'delay': delay
        }
        var('cmds', cmds)
        
        tw(s.inp, text='')
        tw(s.out, text='')
        tw(s.delay, text='0')
        SC.ok()

class List:
    def __init__(s,t):
        if hasattr(s, 'w') and s.w:
            try:
                SC.swish(s.w)
            except:
                pass
        
        cmds = var('cmds') or {}
        if not cmds:
            SC.err('Add some commands first!')
            return
        
        w = s.w = SC.cw(
            source=t,
            size=(420,400),
            ps=SC.UIS()*0.8
        )
        tw(
            parent=w,
            text='Registered Commands',
            scale=1.2,
            position=(190,370),
            h_align='center'
        )
        owner_account = var('owner_account') or 'Not set'
        owner_nickname = var('owner_nickname') or owner_account
        
        # نمایش اشتراک فعال فعلی
        current_sub = var('current_subscription') or 'None'
        remaining = SubscriptionManager.get_remaining_days(current_sub) if current_sub != 'None' else 0
        sub_status = f'✅ {current_sub} ({remaining}d)' if remaining > 0 else f'❌ {current_sub}' if current_sub != 'None' else 'No subscription'
        
        tw(
            parent=w,
            text=f'Owner: {owner_nickname}  |  Sub: {sub_status}',
            scale=0.7,
            position=(210,340),
            h_align='center',
            color=(0.8, 1, 0.8)
        )
        header_container = cw(
            parent=w,
            size=(380,30),
            position=(20,310),
            background=False
        )
        
        tw(
            parent=header_container,
            text='Input',
            position=(10, 0),
            color=(1, 1, 0.5)
        )
        tw(
            parent=header_container,
            text='Output',
            position=(130, 0),
            color=(1, 1, 0.5)
        )
        tw(
            parent=header_container,
            text='Delay',
            position=(280, 0),
            color=(1, 1, 0.5)
        )
        scroll_height = 270
        scroll_width = 380
        s.scroll = sw(
            parent=w,
            size=(scroll_width, scroll_height),
            position=(20, 40),
            color=(0.1, 0.1, 0.1),
            highlight=False
        )
        column = clw(
            parent=s.scroll,
            left_border=10,
            top_border=10,
            bottom_border=10
        )
        for inp, data in cmds.items():
            row = cw(
                parent=column,
                size=(360, 30),
                background=False
            )
            
            tw(
                parent=row,
                text=inp,
                position=(10, 0),
                color=(0.8, 0.8, 1)
            )
            tw(
                parent=row,
                text=data['out'],
                position=(130, 0),
                color=(0.8, 1, 0.8)
            )
            tw(
                parent=row,
                text=f"{data.get('delay', 0)}s",
                position=(280, 0),
                color=(1, 0.8, 0.8)
            )
        
        SC.swish()

class Delete:
    def __init__(s,t):
        if hasattr(s, 'w') and s.w:
            try:
                SC.swish(s.w)
            except:
                pass
        
        s.source = t
        cmds = var('cmds') or {}
        if not cmds:
            SC.err('No commands to delete!')
            return
        
        w = s.w = SC.cw(
            source=t,
            size=(420,400),
            ps=SC.UIS()*0.8
        )
        tw(
            parent=w,
            text='Delete Command',
            scale=1.2,
            position=(190,370),
            h_align='center'
        )
        owner_account = var('owner_account') or 'Not set'
        owner_nickname = var('owner_nickname') or owner_account
        tw(
            parent=w,
            text=f'Owner: {owner_nickname}',
            scale=0.8,
            position=(210,340),
            h_align='center',
            color=(0.8, 1, 0.8)
        )
        header_container = cw(
            parent=w,
            size=(380,30),
            position=(20,310),
            background=False
        )
        
        tw(
            parent=header_container,
            text='Input',
            position=(10, 0),
            color=(1, 1, 0.5)
        )
        tw(
            parent=header_container,
            text='Output',
            position=(130, 0),
            color=(1, 1, 0.5)
        )
        tw(
            parent=header_container,
            text='Delay',
            position=(240, 0),
            color=(1, 1, 0.5)
        )
        scroll_height = 270
        scroll_width = 380
        s.scroll = sw(
            parent=w,
            size=(scroll_width, scroll_height),
            position=(20, 40),
            color=(0.1, 0.1, 0.1),
            highlight=False
        )
        column = clw(
            parent=s.scroll,
            left_border=10,
            top_border=10,
            bottom_border=10
        )
        
        s.buttons = []
        s.commands = list(cmds.items())
        for i, (inp, data) in enumerate(s.commands):
            row = cw(
                parent=column,
                size=(360, 35),
                background=False
            )
            
            tw(
                parent=row,
                text=inp,
                position=(10, 5),
                color=(0.8, 0.8, 1)
            )
            tw(
                parent=row,
                text=data['out'],
                position=(130, 5),
                color=(0.8, 1, 0.8)
            )
            tw(
                parent=row,
                text=f"{data.get('delay', 0)}s",
                position=(240, 5),
                color=(1, 0.8, 0.8)
            )
            btn = SC.bw(
                parent=row,
                label='Delete',
                size=(60,25),
                position=(280,5),
                on_activate_call=CallStrict(s._delete, i)
            )
            s.buttons.append(btn)
        
        SC.swish()
    
    def _delete(s, index):
        # بررسی اشتراک اختصاصی
        current_sub = var('current_subscription')
        if not current_sub or current_sub == 'None':
            SC.err('⛔ ابتدا یک اشتراک را در پنل Subscription فعال کنید!')
            return
        
        if not SubscriptionManager.check_subscription(current_sub):
            SC.err(f'⛔ اشتراک "{current_sub}" منقضی شده است!')
            return
        
        cmds = var('cmds') or {}
        if index < len(s.commands):
            inp_key = s.commands[index][0]
            if inp_key in cmds:
                del cmds[inp_key]
                var('cmds', cmds)
                SC.ok()
                if hasattr(s, 'w') and s.w:
                    SC.swish(s.w)
                    teck(0.1, CallStrict(s.__init__, s.source))

class Edit:
    def __init__(s,t):
        if hasattr(s, 'w') and s.w:
            try:
                SC.swish(s.w)
            except:
                pass
        
        cmds = var('cmds') or {}
        if not cmds:
            SC.err('No commands to edit!')
            return
        
        w = s.w = SC.cw(
            source=t,
            size=(470,400),
            ps=SC.UIS()*0.8
        )
        tw(
            parent=w,
            text='Edit Commands',
            scale=1.2,
            position=(235,370),
            h_align='center'
        )
        owner_account = var('owner_account') or 'Not set'
        owner_nickname = var('owner_nickname') or owner_account
        tw(
            parent=w,
            text=f'Owner: {owner_nickname}',
            scale=0.8,
            position=(235,340),
            h_align='center',
            color=(0.8, 1, 0.8)
        )
        header_container = cw(
            parent=w,
            size=(430,30),
            position=(20,310),
            background=False
        )
        
        tw(
            parent=header_container,
            text='Input',
            position=(10, 0),
            color=(1, 1, 0.5)
        )
        tw(
            parent=header_container,
            text='Output',
            position=(120, 0),
            color=(1, 1, 0.5)
        )
        tw(
            parent=header_container,
            text='Delay',
            position=(240, 0),
            color=(1, 1, 0.5)
        )
        scroll_height = 270
        scroll_width = 430
        s.scroll = sw(
            parent=w,
            size=(scroll_width, scroll_height),
            position=(20, 40),
            color=(0.1, 0.1, 0.1),
            highlight=False
        )
        column = clw(
            parent=s.scroll,
            left_border=10,
            top_border=10,
            bottom_border=10
        )
        
        s.commands = list(cmds.items())
        s.out_fields = []
        s.delay_fields = []
        for i, (inp, data) in enumerate(s.commands):
            row = cw(
                parent=column,
                size=(410, 40),
                background=False
            )
            tw(
                parent=row,
                text=inp,
                position=(10, 10),
                color=(0.8, 0.8, 1)
            )
            out_field = tw(
                parent=row,
                text=data['out'],
                maxwidth=100,
                size=(100,30),
                editable=True,
                v_align='center',
                color=(0.8, 1, 0.8),
                position=(120, 5),
                allow_clear_button=False
            )
            s.out_fields.append(out_field)
            delay_field = tw(
                parent=row,
                text=str(data.get('delay', 0)),
                maxwidth=60,
                size=(60,30),
                editable=True,
                v_align='center',
                color=(1, 0.8, 0.8),
                position=(240, 5),
                allow_clear_button=False
            )
            s.delay_fields.append(delay_field)
            SC.bw(
                parent=row,
                label='Save',
                size=(60,30),
                position=(320, 5),
                on_activate_call=CallStrict(s._save, i)
            )
        
        SC.swish()
    
    def _save(s, index):
        # بررسی اشتراک اختصاصی
        current_sub = var('current_subscription')
        if not current_sub or current_sub == 'None':
            SC.err('⛔ ابتدا یک اشتراک را در پنل Subscription فعال کنید!')
            return
        
        if not SubscriptionManager.check_subscription(current_sub):
            SC.err(f'⛔ اشتراک "{current_sub}" منقضی شده است!')
            return
        
        if index < len(s.commands):
            inp_key = s.commands[index][0]
            new_out = tw(query=s.out_fields[index]).strip().lower()
            delay_text = tw(query=s.delay_fields[index]).strip()
            
            if not new_out:
                SC.err('Output cannot be empty!')
                return
            try:
                delay = float(delay_text)
                if delay < 0 or delay > 2:
                    SC.err('Delay must be between 0 and 2 seconds!')
                    return
            except ValueError:
                SC.err('Enter a valid number for delay!')
                return
            
            cmds = var('cmds') or {}
            if inp_key in cmds:
                cmds[inp_key]['out'] = new_out
                cmds[inp_key]['delay'] = delay
                var('cmds', cmds)
                SC.ok()
                push(f'Saved: {inp_key} → {new_out} ({delay}s)', color=(0, 1, 0))

class PlayerInfo:
    def __init__(s, source):
        if hasattr(s, 'w') and s.w:
            try:
                SC.swish(s.w)
            except:
                pass
        
        w = s.w = SC.cw(
            source=source,
            size=(600, 350),
            ps=SC.UIS()*0.7
        )

        tw(
            parent=w,
            text='By Bsrush',
            scale=1.1,
            position=(280, 320),  
            h_align='center',
        )
        owner_account = var('owner_account') or ''
        owner_nickname = var('owner_nickname') or ''
        
        if owner_account:
            tw(
                parent=w,
                text=f'Your account: {owner_account}',
                scale=0.7,
                position=(280, 290),
                h_align='center',
                color=(0.8, 1, 0.8)
            )
            
            if owner_nickname and owner_nickname != owner_account:
                tw(
                    parent=w,
                    text=f' Nickname: {owner_nickname}',
                    scale=0.7,
                    position=(280, 270),
                    h_align='center',
                    color=(1, 1, 0.8)
                )
        
        s.players = s.get_players()

        s.scroll = sw(
            parent=w,
            size=(560, 200),
            position=(20, 60),
            color=(0.1, 0.1, 0.1),
            highlight=False
        )

        s.container = cw(
            parent=s.scroll,
            size=(560, max(200, len(s.players) * 45)),
            background=False
        )
        SC.bw(
            parent=w,
            label='Auto-Detect Owner',
            size=(140, 30),
            position=(30, 25),
            on_activate_call=CallStrict(s.auto_detect_owner),
            icon=gt('replayIcon'),
            iconscale=0.8,
        )
        SC.bw(
            parent=w,
            label='Get Owner ID',
            size=(100, 30),
            position=(180, 25),
            on_activate_call=CallStrict(s.get_owner_id),
            icon=gt('replayIcon'),
            iconscale=0.8,
        )
        
        SC.bw(
            parent=w,
            label='Refresh',
            size=(80, 30),
            position=(290, 25),
            on_activate_call=CallStrict(s.refresh_players),
            icon=gt('replayIcon'),
            iconscale=0.8,
        )

        s.display_players()
        SC.swish()

    def get_players(s):
        players = []
        try:
            roster = get_game_roster()
            for client in roster:
                if 'players' in client and client['players']:
                    for p in client['players']:
                        device_name = client.get('display_string', 'Unknown device')
                        account_id = client.get('account_id', '')
                        
                        players.append({
                            'name': p.get('name', 'Unknown Player'),
                            'full_name': p.get('name_full', 'Unknown Player'),
                            'client_id': client.get('client_id', -1),
                            'is_host': client.get('client_id', -1) == -1,
                            'device': device_name,
                            'account_id': account_id,
                            'client_info': client
                        })
        except Exception as e:
            print(f"Error getting players: {e}")
        return players

    def display_players(s):
        for child in s.container.get_children():
            child.delete()

        if not s.players:
            tw(
                parent=s.container,
                text='⚠️ No players found',
                position=(280, 90),
                scale=0.8,
                color=(1, 0.5, 0),
                h_align='center'
            )
            cw(s.container, size=(560, 200))
            return

        headers = [
            ('Nickname', 30, 0.6, (1, 1, 1)),
            ('ID', 120, 0.6, (0.8, 0.8, 1)),
            ('Account', 170, 0.6, (0.6, 1, 0.6)),
            ('Status', 300, 0.6, (1, 1, 0.8)),
            ('Actions', 440, 0.6, (1, 1, 1))
        ]

        y_pos = len(s.players) * 40 + 20
        for text, x, scale, color in headers:
            tw(
                parent=s.container,
                text=text,
                position=(x, y_pos),
                scale=scale,
                color=color,
                h_align='center'
            )

        y_pos = len(s.players) * 40 - 15
        for i, player in enumerate(s.players):
            owner_account = var('owner_account') or ''
            owner_nickname = var('owner_nickname') or ''
            owner_client_id = var('owner_client_id') or ''
            
            is_owner = False
            if owner_account:
                if player.get('account_id') and owner_account in player.get('account_id', ''):
                    is_owner = True
                elif owner_account.lower() in player['device'].lower():
                    is_owner = True
                elif owner_nickname and player['name'] == owner_nickname:
                    is_owner = True
                elif owner_client_id and str(player['client_id']) == str(owner_client_id):
                    is_owner = True
            
            bg_color = (0.2, 0.2, 0.3) if i % 2 == 0 else (0.25, 0.25, 0.35)
            if is_owner:
                bg_color = (0.2, 0.4, 0.2) 
            bw(
                parent=s.container, 
                label='', 
                size=(540, 35),  
                position=(10, y_pos), 
                color=bg_color, 
                enable_sound=False
            )
            pname = player['name'][:18] + '...' if len(player['name']) > 18 else player['name']
            if player['is_host']:
                pname = f"👑 {pname}"
            if is_owner:
                pname = f"⭐ {pname}"
            
            tw(
                parent=s.container, 
                text=pname,
                position=(20, y_pos + 5), 
                scale=0.65,
                color=(1, 1, 1), 
                maxwidth=160,
                h_align='left'
            )
            tw(
                parent=s.container, 
                text=f"{player['client_id']}",
                position=(120, y_pos + 5), 
                scale=0.6,
                color=(0.8, 0.8, 1), 
                h_align='center'
            )
            device_text = player['device'][:18] + '...' if len(player['device']) > 18 else player['device']
            tw(
                parent=s.container, 
                text=device_text,
                position=(160, y_pos + 5), 
                scale=0.55,
                color=(0.6, 1, 0.6), 
                maxwidth=140, 
                h_align='left'
            )
            status_text = "Host" if player['is_host'] else "Player"
            if is_owner:
                status_text = "Owner"
            status_color = (1, 1, 0) if player['is_host'] else (0.8, 0.8, 1)
            if is_owner:
                status_color = (0, 1, 0)
            tw(
                parent=s.container, 
                text=status_text,
                position=(300, y_pos + 5), 
                scale=0.6,
                color=status_color, 
                h_align='center'
            )
            if not is_owner: 
                actions = [
                    ('Copy', s.copy_player_info, (400, y_pos + 5), player),
                    ('@', s.mention_player, (450, y_pos + 5), player),
                    ('Kick', s.kick_player, (500, y_pos + 5), player)
                ]
            else:
                actions = [
                    ('Copy', s.copy_player_info, (400, y_pos + 5), player),
                    ('@', s.mention_player, (450, y_pos + 5), player),
                    ('ID', s.set_owner_id, (500, y_pos + 5), player)
                ]
            
            for label, callback, pos, data in actions:
                SC.bw(
                    parent=s.container, 
                    label=label, 
                    size=(25, 25),
                    position=pos, 
                    on_activate_call=CallStrict(callback, data),
                    text_scale=0.6
                )

            y_pos -= 40

        cw(s.container, size=(560, len(s.players) * 40 + 50))

    def auto_detect_owner(s):
        owner_account = var('owner_account')
        if not owner_account:
            SC.err('No owner account set! Set owner first.')
            return
        s.players = s.get_players()
        
        found_owner = None
        for player in s.players:
            if owner_account.lower() in player['device'].lower():
                found_owner = player
                break
            if player.get('account_id') and owner_account in player.get('account_id', ''):
                found_owner = player
                break
        
        if found_owner:
            var('owner_nickname', found_owner['name'])
            var('owner_client_id', found_owner['client_id'])
            SC.ok()
            push(f'Owner detected: {found_owner["name"]} (ID: {found_owner["client_id"]})', color=(0, 1, 0))
            s.display_players()
        else:
            SC.err('Owner not found in player list!')

    def get_owner_id(s):
        """Get and set owner ID from current owner"""
        owner_account = var('owner_account')
        owner_nickname = var('owner_nickname')
        
        if not owner_account and not owner_nickname:
            SC.err('No owner set! Set owner first.')
            return
        s.players = s.get_players()
        
        found_owner = None
        for player in s.players:
            if owner_account and owner_account.lower() in player['device'].lower():
                found_owner = player
                break
            if owner_nickname and player['name'] == owner_nickname:
                found_owner = player
                break
        
        if found_owner:
            var('owner_client_id', found_owner['client_id'])
            SC.ok()
            push(f'Owner ID set to: {found_owner["client_id"]}', color=(0, 1, 0))
            s.display_players()
        else:
            SC.err('Owner not found in player list!')

    def set_owner_id(s, player):
        var('owner_client_id', player['client_id'])
        SC.ok()
        push(f'Owner ID set to: {player["client_id"]}', color=(0, 1, 0))
        s.display_players()

    def refresh_players(s):
        s.players = s.get_players()
        s.display_players()
        push('🔄 Player list updated.', color=(0, 1, 0))
        gs('dingSmall').play()

    def copy_player_info(s, player):
        info = (f"Nickname: {player['name']}\n"
                f"ID: {player['client_id']}\n"
                f"Account: {player['device']}\n"
                f"Status: {'Host' if player['is_host'] else 'Player'}")
        
        if has_clipboard():
            from babase import clipboard_set_text
            clipboard_set_text(info)
            push(f'📋 Information for {player["name"]} copied', color=(0, 1, 0))
            gs('dingSmall').play()
        else:
            SC.err('Clipboard not available!')

    def copy_all_info(s):
        if not s.players:
            SC.err('No players found')
            return
            
        all_info = "👥 List of players:\n\n"
        for player in s.players:
            status = "👑 Host" if player['is_host'] else "👤 Player"
            all_info += f"• {player['name']} (ID: {player['client_id']}) - {player['device']} - {status}\n"
        
        if has_clipboard():
            from babase import clipboard_set_text
            clipboard_set_text(all_info)
            push('📋 All players information copied.', color=(0, 1, 0))
            gs('dingSmallHigh').play()
        else:
            SC.err('Clipboard not available!')

    def mention_player(s, player):
        try:
            message = f"@{player['name']}"
            CM(message)
            push(f"📍 {player['name']} was mentioned", color=(0, 1, 1))
            gs('dingSmall').play()
        except Exception as e:
            SC.err(f"Error: {e}")

    def kick_player(s, player):
        if player['is_host']:
            SC.err('Cannot kick host!')
            return
        
        try:
            disconnect_client(player['client_id'])
            push(f"🚫 {player['name']} kicked", color=(1, 0.5, 0))
            gs('dingSmallLow').play()
            teck(1.0, CallStrict(s.refresh_players))
        except Exception as e:
            SC.err(f"Error: {e}")

    def kick_all(s):
        if not s.players:
            SC.err('There are no players to kick!')
            return
            
        try:
            kicked_count = 0
            
            for player in s.players:
                if not player['is_host']:
                    owner_nickname = var('owner_nickname')
                    if owner_nickname and player['name'] == owner_nickname:
                        continue
                    
                    try:
                        disconnect_client(player['client_id'])
                        kicked_count += 1
                    except:
                        continue
            
            if kicked_count > 0:
                push(f"🚫 {kicked_count} players kicked", color=(1, 0.5, 0))
                gs('dingSmallLow').play()
                teck(1.0, CallStrict(s.refresh_players))
            else:
                SC.err('There are no players to kick!')
                
        except Exception as e:
            SC.err(f"Error: {e}")

class OwnerSettings:
    def __init__(s,t):
        if hasattr(s, 'w') and s.w:
            try:
                SC.swish(s.w)
            except:
                pass
        
        s.source = t
        w = s.w = SC.cw(
            source=t,
            size=(350,320),
            ps=SC.UIS()*0.8
        )
        tw(
            parent=w,
            text='Owner Settings',
            scale=0.9,
            position=(155,290),
            h_align='center'
        )
        owner_account = var('owner_account') or ''
        owner_nickname = var('owner_nickname') or ''
        owner_client_id = var('owner_client_id') or ''
        
        tw(
            parent=w,
            text='Account:',
            scale=0.9,
            position=(10,270),
            color=(0.8, 1, 0)
        )
        
        tw(
            parent=w,
            text=owner_account if owner_account else 'Not set',
            scale=0.9,
            position=(100,270),
            color=(0.8, 1, 0.8) if owner_account else (1, 0.8, 0.8)
        )
        
        if owner_client_id:
            tw(
                parent=w,
                text=f'ID: {owner_client_id}',
                position=(10,250),
                scale=0.8,
                color=(1, 1, 0.8)
            )
        
        if owner_nickname and owner_nickname != owner_account:
            tw(
                parent=w,
                text=f'Nickname: {owner_nickname}',
                position=(10,230),
                scale=0.8,
                color=(1, 0.8, 0.8)
            )
        tw(
            parent=w,
            text='Auto Detection Methods:',
            position=(10,200),
            scale=0.9,
            color=(0.8, 0.8, 1)
        )
        y_pos = 150
        SC.bw(
            parent=w,
            label='Get My Account',
            size=(175,35),
            position=(0,y_pos),
            on_activate_call=CallStrict(s._get_game_account)
        )
        SC.bw(
            parent=w,
            label='Detect Nickname',
            size=(180,35),
            position=(180,y_pos),
            on_activate_call=CallStrict(s._detect_from_players)
        )
        y_pos =100
        SC.bw(
            parent=w,
            label='Detect from Chat',
            size=(180,35),
            position=(0,y_pos),
            on_activate_call=CallStrict(s._detect_from_chat)
        )
        tw(
            parent=w,
            text='• قبل استفاده از ابتدا يه پيام در چت ارسال کنيد. ',
            position=(10, y_pos-30),
            scale=0.6,
            color=(0.7, 0.9, 0.7)
        )
        y_pos -= 40
        tw(
            parent=w,
            text='set manually:',
            position=(10, y_pos-5),
            scale=0.8,
            color=(0, 0.9, 0.7)
        )
        s.manual_input = tw(
            parent=w,
            maxwidth=200,
            size=(200,30),
            editable=True,
            v_align='center',
            color=(0, 0.9, 0.7),
            position=(145,y_pos-10),
            allow_clear_button=False,
            text=owner_account if owner_account else ''
        )
        btn_y = y_pos - 60
        SC.bw(
            parent=w,
            label='Set Manually',
            size=(100,35),
            color=(0, 0.9, 0.7),
            position=(230,btn_y),
            on_activate_call=CallStrict(s._set_manual)
        )
        
        SC.bw(
            parent=w,
            label='Clear Owner',
            size=(100,35),
            color=(1, 0.0, 0.0),
            position=(30,btn_y),
            on_activate_call=CallStrict(s._clear_owner)
        )
        
        SC.swish()
    
    def _get_game_account(s):
        try:
            account_name = get_account_name_from_game()
            if account_name:
                var('owner_account', account_name)
                SC.ok()
                push(f'Owner account set to: {account_name}', color=(0, 1, 0))
                s._refresh_panel()
            else:
                SC.err('Could not get account name from game.')
            
        except Exception as e:
            SC.err(f'Error: {str(e)}')
    
    def _detect_from_players(s):
        try:
            temp_player_info = PlayerInfo.__new__(PlayerInfo)
            players = temp_player_info.get_players()
            owner_account = var('owner_account') or ''
            
            if not owner_account:
                SC.err('Set owner account first!')
                return
            
            found_owner = None
            for player in players:
                if owner_account.lower() in player['device'].lower():
                    found_owner = player
                    break
            
            if found_owner:
                var('owner_nickname', found_owner['name'])
                var('owner_client_id', found_owner['client_id'])
                SC.ok()
                push(f'Owner nickname detected: {found_owner["name"]}', color=(0, 1, 0))
                s._refresh_panel()
            else:
                SC.err('Owner not found in player list!')
                
        except Exception as e:
            SC.err(f'Error: {str(e)}')
    
    def _detect_from_chat(s):
        messages = GCM()
        if not messages:
            SC.err('No chat messages found! Type something in chat first.')
            return
        latest = messages[-1]
        parts = latest.split(': ', 1)
        if len(parts) < 2:
            SC.err('Could not detect sender. Try again.')
            return
        
        sender_name = parts[0].strip()
        var('owner_nickname', sender_name)
        SC.ok()
        push(f'Owner nickname set to: {sender_name}', color=(0, 1, 0))
        s._refresh_panel()
    
    def _set_manual(s):
        manual_name = tw(query=s.manual_input).strip()
        if not manual_name:
            SC.err('Enter a name!')
            return
        
        var('owner_account', manual_name)
        SC.ok()
        push(f'Owner account set to: {manual_name}', color=(0, 1, 0))
        s._refresh_panel()
    
    def _clear_owner(s):
        var('owner_account', '')
        var('owner_nickname', '')
        var('owner_client_id', '')
        SC.ok()
        push('Owner cleared! Plugin will respond to all players.', color=(1, 0.5, 0))
        s._refresh_panel()
    
    def _refresh_panel(s):
        if hasattr(s, 'w') and s.w:
            SC.swish(s.w)
            teck(0.1, CallStrict(s.__init__, s.source))

class AntiCodeAdd:
    def __init__(s,t):
        if hasattr(s, 'w') and s.w:
            try:
                SC.swish(s.w)
            except:
                pass
        
        w = s.w = SC.cw(
            source=t,
            size=(400,200),
            ps=SC.UIS()*0.8
        )
        owner_client_id = var('owner_client_id') or 'Not set'
        
        tw(
            parent=w,
            text='Anti Code System',
            scale=1.2,
            position=(175,190),
            h_align='center',
            color=(1, 0.5, 0.5)
        )
        
        tw(
            parent=w,
            text=f' ID: {owner_client_id}',
            position=(270,160),
            h_align='center',
            color=(0.8, 1, 0.8) if owner_client_id != 'Not set' else (1, 0.8, 0.8)
        )
        tw(
            parent=w,
            text='Code:',
            position=(40,150)
        )
        s.inp = tw(
            parent=w,
            maxwidth=200,
            size=(200,30),
            editable=True,
            v_align='center',
            color=(0.75,0.75,0.75),
            position=(40,128),
            allow_clear_button=False
        )
        tw(
            parent=w,
            text='Response:',
            position=(40,100)
        )
        s.out = tw(
            parent=w,
            maxwidth=200,
            size=(200,30),
            editable=True,
            v_align='center',
            color=(0.75,0.75,0.75),
            position=(40,68),
            allow_clear_button=False
        )
        tw(
            parent=w,
            text='Delay:',
            position=(40,40)
        )
        s.delay = tw(
            parent=w,
            maxwidth=100,
            size=(100,30),
            editable=True,
            v_align='center',
            color=(0.75,0.75,0.75),
            position=(40,12),
            allow_clear_button=False,
            text='0'
        )
        SC.bw(
            parent=w,
            label='Add Anti Code',
            size=(120,35),
            position=(260,12),
            on_activate_call=CallStrict(s._add)
        )
        
        SC.swish()
    
    def _add(s):
        # بررسی اشتراک اختصاصی
        current_sub = var('current_subscription')
        if not current_sub or current_sub == 'None':
            SC.err('⛔ ابتدا یک اشتراک را در پنل Subscription فعال کنید!')
            return
        
        if not SubscriptionManager.check_subscription(current_sub):
            SC.err(f'⛔ اشتراک "{current_sub}" منقضی شده است!')
            return
        
        inp = tw(query=s.inp).strip()
        out = tw(query=s.out).strip()
        delay_text = tw(query=s.delay).strip()
        owner_client_id = var('owner_client_id')
        
        if not owner_client_id or owner_client_id == 'Not set':
            SC.err('Set owner ID first in Player Info!')
            return
        
        if not inp or not out:
            SC.err('Enter both codes!')
            return
        try:
            delay = float(delay_text)
            if delay < 0 or delay > 2:
                SC.err('Delay must be between 0 and 2 seconds!')
                return
        except ValueError:
            SC.err('Enter a valid number for delay!')
            return
        anti_cmds = var('anti_cmds') or {}
        inp_key = inp.lower()
        if inp_key in anti_cmds:
            SC.err('Anti code already exists!')
            return
        anti_cmds[inp_key] = {
            'out': out.lower(),
            'delay': delay,
            'owner_id': owner_client_id
        }
        var('anti_cmds', anti_cmds)
        
        tw(s.inp, text='')
        tw(s.out, text='')
        tw(s.delay, text='0')
        SC.ok()
        push(f'Anti code added: %{inp} {owner_client_id} → %{out} {owner_client_id}', color=(1, 0.5, 0.5))

class AntiCodeList:
    def __init__(s,t):
        if hasattr(s, 'w') and s.w:
            try:
                SC.swish(s.w)
            except:
                pass
        
        anti_cmds = var('anti_cmds') or {}
        if not anti_cmds:
            SC.err('Add some anti codes first!')
            return
        
        owner_client_id = var('owner_client_id') or 'Not set'
        
        w = s.w = SC.cw(
            source=t,
            size=(450,400),
            ps=SC.UIS()*0.8
        )
        tw(
            parent=w,
            text='Anti Code System',
            scale=1.2,
            position=(215,370),
            h_align='center',
            color=(1, 0.5, 0.5)
        )
        tw(
            parent=w,
            text=f'Owner ID: {owner_client_id}',
            scale=0.8,
            position=(215,340),
            h_align='center',
            color=(0.8, 1, 0.8)
        )
        header_container = cw(
            parent=w,
            size=(410,30),
            position=(20,290),
            background=False
        )
        
        tw(
            parent=header_container,
            text='Code',
            position=(10, 0),
            color=(1, 0.8, 0.8)
        )
        tw(
            parent=header_container,
            text='Response',
            position=(120, 0),
            color=(0.8, 1, 0.8)
        )
        tw(
            parent=header_container,
            text='Delay',
            position=(240, 0),
            color=(1, 1, 0.8)
        )
        tw(
            parent=header_container,
            text='Example',
            position=(320, 0),
            color=(0.8, 0.8, 1)
        )
        scroll_height = 260
        scroll_width = 410
        s.scroll = sw(
            parent=w,
            size=(scroll_width, scroll_height),
            position=(20, 30),
            color=(0.1, 0.1, 0.1),
            highlight=False
        )
        column = clw(
            parent=s.scroll,
            left_border=10,
            top_border=10,
            bottom_border=10
        )
        for inp, data in anti_cmds.items():
            row = cw(
                parent=column,
                size=(390, 35),
                background=False
            )
            
            tw(
                parent=row,
                text=inp,
                position=(10, 5),
                color=(1, 0.8, 0.8)
            )
            tw(
                parent=row,
                text=data['out'],
                position=(120, 5),
                color=(0.8, 1, 0.8)
            )
            tw(
                parent=row,
                text=f"{data.get('delay', 0)}s",
                position=(240, 5),
                color=(1, 1, 0.8)
            )
            example_text = f"%{inp} {owner_client_id}"
            tw(
                parent=row,
                text=example_text,
                position=(310, 5),
                scale=0.6,
                color=(0.8, 0.8, 1),
                maxwidth=150
            )
        
        SC.swish()

class AntiCodeEdit:
    def __init__(s,t):
        if hasattr(s, 'w') and s.w:
            try:
                SC.swish(s.w)
            except:
                pass
        
        s.source = t
        anti_cmds = var('anti_cmds') or {}
        if not anti_cmds:
            SC.err('No anti codes to edit!')
            return
        
        owner_client_id = var('owner_client_id') or 'Not set'
        
        w = s.w = SC.cw(
            source=t,
            size=(500,400),
            ps=SC.UIS()*0.8
        )
        tw(
            parent=w,
            text='Edit Anti Codes',
            scale=1.2,
            position=(240,370),
            h_align='center',
            color=(1, 0.5, 0.5)
        )
        header_container = cw(
            parent=w,
            size=(460,30),
            position=(20,310),
            background=False
        )
        
        tw(
            parent=header_container,
            text='Code',
            position=(20, 0),
            color=(1, 0.8, 0.8)
        )
        tw(
            parent=header_container,
            text='Response',
            position=(155, 0),
            color=(0.8, 1, 0.8)
        )
        tw(
            parent=header_container,
            text='Delay',
            position=(275, 0),
            color=(1, 1, 0.8)
        )
        scroll_height = 270
        scroll_width = 460
        s.scroll = sw(
            parent=w,
            size=(scroll_width, scroll_height),
            position=(20, 40),
            color=(0.1, 0.1, 0.1),
            highlight=False
        )
        column = clw(
            parent=s.scroll,
            left_border=10,
            top_border=10,
            bottom_border=10
        )
        
        s.commands = list(anti_cmds.items())
        s.out_fields = []
        s.delay_fields = []
        for i, (inp, data) in enumerate(s.commands):
            row = cw(
                parent=column,
                size=(440, 40),
                background=False
            )
            tw(
                parent=row,
                text=inp,
                position=(10, 10),
                color=(1, 0.8, 0.8)
            )
            out_field = tw(
                parent=row,
                text=data['out'],
                maxwidth=100,
                size=(100,30),
                editable=True,
                v_align='center',
                color=(0.8, 1, 0.8),
                position=(130, 5),
                allow_clear_button=False
            )
            s.out_fields.append(out_field)
            delay_field = tw(
                parent=row,
                text=str(data.get('delay', 0)),
                maxwidth=60,
                size=(60,30),
                editable=True,
                v_align='center',
                color=(1, 1, 0.8),
                position=(250, 5),
                allow_clear_button=False
            )
            s.delay_fields.append(delay_field)
            SC.bw(
                parent=row,
                label='Save',
                size=(60,30),
                position=(330, 5),
                on_activate_call=CallStrict(s._save, i)
            )
        
        SC.swish()
    
    def _save(s, index):
        # بررسی اشتراک اختصاصی
        current_sub = var('current_subscription')
        if not current_sub or current_sub == 'None':
            SC.err('⛔ ابتدا یک اشتراک را در پنل Subscription فعال کنید!')
            return
        
        if not SubscriptionManager.check_subscription(current_sub):
            SC.err(f'⛔ اشتراک "{current_sub}" منقضی شده است!')
            return
        
        if index < len(s.commands):
            inp_key = s.commands[index][0]
            new_out = tw(query=s.out_fields[index]).strip().lower()
            delay_text = tw(query=s.delay_fields[index]).strip()
            
            if not new_out:
                SC.err('Response cannot be empty!')
                return
            try:
                delay = float(delay_text)
                if delay < 0 or delay > 2:
                    SC.err('Delay must be between 0 and 2 seconds!')
                    return
            except ValueError:
                SC.err('Enter a valid number for delay!')
                return
            
            anti_cmds = var('anti_cmds') or {}
            if inp_key in anti_cmds:
                anti_cmds[inp_key]['out'] = new_out
                anti_cmds[inp_key]['delay'] = delay
                var('anti_cmds', anti_cmds)
                SC.ok()
                owner_client_id = var('owner_client_id') or ''
                push(f'Saved: %{inp_key} {owner_client_id} → %{new_out} {owner_client_id} ({delay}s)', color=(0, 1, 0))
                if hasattr(s, 'w') and s.w:
                    SC.swish(s.w)
                    teck(0.1, CallStrict(s.__init__, s.source))

class AntiCodeDelete:
    def __init__(s,t):
        if hasattr(s, 'w') and s.w:
            try:
                SC.swish(s.w)
            except:
                pass
        
        s.source = t
        anti_cmds = var('anti_cmds') or {}
        if not anti_cmds:
            SC.err('No anti codes to delete!')
            return
        
        w = s.w = SC.cw(
            source=t,
            size=(450,400),
            ps=SC.UIS()*0.8
        )
        tw(
            parent=w,
            text='Delete Anti Code',
            scale=1.2,
            position=(215,370),
            h_align='center',
            color=(1, 0.5, 0.5)
        )
        header_container = cw(
            parent=w,
            size=(410,30),
            position=(20,310),
            background=False
        )
        
        tw(
            parent=header_container,
            text='Code',
            position=(20, 0),
            color=(1, 0.8, 0.8)
        )
        tw(
            parent=header_container,
            text='Response',
            position=(115, 0),
            color=(0.8, 1, 0.8)
        )
        tw(
            parent=header_container,
            text='Delay',
            position=(235, 0),
            color=(1, 1, 0.8)
        )
        scroll_height = 270
        scroll_width = 410
        s.scroll = sw(
            parent=w,
            size=(scroll_width, scroll_height),
            position=(20, 40),
            color=(0.1, 0.1, 0.1),
            highlight=False
        )
        column = clw(
            parent=s.scroll,
            left_border=10,
            top_border=10,
            bottom_border=10
        )
        
        s.buttons = []
        s.commands = list(anti_cmds.items())
        for i, (inp, data) in enumerate(s.commands):
            row = cw(
                parent=column,
                size=(390, 35),
                background=False
            )
            
            tw(
                parent=row,
                text=inp,
                position=(10, 5),
                color=(1, 0.8, 0.8)
            )
            tw(
                parent=row,
                text=data['out'],
                position=(130, 5),
                color=(0.8, 1, 0.8)
            )
            tw(
                parent=row,
                text=f"{data.get('delay', 0)}s",
                position=(220, 5),
                color=(1, 1, 0.8)
            )
            btn = SC.bw(
                parent=row,
                label='Delete',
                size=(60,25),
                position=(300, 10),
                on_activate_call=CallStrict(s._delete, i)
            )
            s.buttons.append(btn)
        
        SC.swish()
    
    def _delete(s, index):
        # بررسی اشتراک اختصاصی
        current_sub = var('current_subscription')
        if not current_sub or current_sub == 'None':
            SC.err('⛔ ابتدا یک اشتراک را در پنل Subscription فعال کنید!')
            return
        
        if not SubscriptionManager.check_subscription(current_sub):
            SC.err(f'⛔ اشتراک "{current_sub}" منقضی شده است!')
            return
        
        anti_cmds = var('anti_cmds') or {}
        if index < len(s.commands):
            inp_key = s.commands[index][0]
            if inp_key in anti_cmds:
                del anti_cmds[inp_key]
                var('anti_cmds', anti_cmds)
                SC.ok()
                if hasattr(s, 'w') and s.w:
                    SC.swish(s.w)
                    teck(0.1, CallStrict(s.__init__, s.source))
                
class AntiCodeMenu:
    def __init__(s, source):
        if hasattr(s, 'w') and s.w:
            try:
                SC.swish(s.w)
            except:
                pass
        
        w = s.w = SC.cw(
            source=source,
            size=(300, 450),
            ps=SC.UIS()*0.8
        )
        tw(
            scale=1.0,
            parent=w,
            text='Anti Code System',
            h_align='center',
            position=(135, 420),
            color=(1, 0.5, 0.5)
        )
        owner_client_id = var('owner_client_id') or 'Not set'
        tw(
            parent=w,
            text=f'Owner ID: {owner_client_id}',
            scale=0.8,
            position=(135, 390),
            h_align='center',
            color=(0.8, 1, 0.8) if owner_client_id != 'Not set' else (1, 0.8, 0.8)
        )
        
        # دکمه روشن/خاموش آنتی‌کد
        anti_enabled = var('anti_enabled') if var('anti_enabled') is not None else True
        s.anti_toggle_btn = SC.bw(
            parent=w,
            label=f'🛡️ Anti-Code: {"ON" if anti_enabled else "OFF"}',
            size=(180, 35),
            position=(60, 340),
            on_activate_call=CallStrict(s._toggle_anti),
            color=(0.2, 0.5, 0.2) if anti_enabled else (0.5, 0.2, 0.2)
        )
        bw(s.anti_toggle_btn, textcolor=(1, 1, 1) if anti_enabled else (1, 0.6, 0.6))
        
        scroll_height = 270
        scroll_width = 280
        scroll = sw(
            parent=w,
            size=(scroll_width, scroll_height),
            position=(10, 50),
            color=(0.1, 0.1, 0.1),
            highlight=False
        )
        column = clw(
            parent=scroll,
            left_border=0,
            top_border=10,
            bottom_border=10
        )
        buttons = [
            ('Add Anti Code', AntiCodeAdd),
            ('List Anti Codes', AntiCodeList),
            ('Edit Anti Codes', AntiCodeEdit),
            ('Delete Anti Code', AntiCodeDelete)
        ]
        
        button_height = 50
        start_y = 10
        
        for label, callback in buttons:
            SC.bw(
                label=label,
                parent=column,
                size=(240,45),
                position=(20, start_y),
                on_activate_call=CallPartial(callback, w)
            )
            start_y += button_height
        column_height = start_y + 10
        cw(column, size=(260, column_height))
        
        SC.swish()
    
    def _toggle_anti(s):
        current_state = var('anti_enabled')
        if current_state is None:
            current_state = True
        new_state = not current_state
        var('anti_enabled', new_state)
        
        # به‌روزرسانی دکمه
        if hasattr(s, 'anti_toggle_btn'):
            bw(s.anti_toggle_btn, label=f'🛡️ Anti-Code: {"ON" if new_state else "OFF"}')
            bw(s.anti_toggle_btn, color=(0.2, 0.5, 0.2) if new_state else (0.5, 0.2, 0.2))
            bw(s.anti_toggle_btn, textcolor=(1, 1, 1) if new_state else (1, 0.6, 0.6))
        
        push(f'🛡️ Anti-Code system {"enabled" if new_state else "disabled"}', 
             color=(0, 1, 0) if new_state else (1, 0.5, 0))
        gs('dingSmall').play()
        
class SC:
    @classmethod
    def UIS(c):
        i = APP.ui_v1.uiscale
        if i == 0:  
            return 1.5
        elif i == 1:  
            return 1.1
        else:  
            return 0.8
    
    @classmethod
    def bw(c,**k):
        kwargs = dict(k)
        if 'textcolor' not in kwargs:
            kwargs['textcolor'] = (1,1,1)
        if 'enable_sound' not in kwargs:
            kwargs['enable_sound'] = False
        if 'button_type' not in kwargs:
            kwargs['button_type'] = 'square'
        if 'color' not in kwargs:
            kwargs['color'] = (0.18,0.18,0.18)
        
        return bw(**kwargs)
    
    @classmethod
    def cw(c,source,ps=0,**k):
        from bauiv1 import get_special_widget as gsw
        o = source.get_screen_space_center() if source else None
        kwargs = dict(k)
        filtered_kwargs = {}
        for key, value in kwargs.items():
            if key not in ['parent', 'scale_origin_stack_offset', 'scale', 'transition', 'color']:
                filtered_kwargs[key] = value
        
        r = cw(
            parent=gsw('overlay_stack'),
            scale_origin_stack_offset=o,
            scale=c.UIS()+ps,
            transition='in_scale',
            color=(0.18,0.18,0.18),
            **filtered_kwargs
        )
        cw(r, on_outside_click_call=CallPartial(SC.swish, t=r))
        return r
    
    @classmethod
    def swish(cls, t=None):
        gs('swish').play()
        if t:
            cw(t, transition='out_scale')
    
    @classmethod
    def err(cls, t):
        gs('block').play()
        push(t, color=(1,1,0))
    
    @classmethod
    def ok(cls):
        gs('dingSmallHigh').play()
        push('Success!', color=(0,1,0))
    
    def __init__(s, source: bw = None) -> None:
        if hasattr(s, 'w') and s.w:
            try:
                SC.swish(s.w)
            except:
                pass
        
        w = s.w = SC.cw(
            source=source,
            size=(250, 580),
        )
        scroll_height = 490
        scroll_width = 230
        scroll = sw(
            parent=w,
            size=(scroll_width, scroll_height),
            position=(10, 50),
            color=(0.1, 0.1, 0.1),
            highlight=False
        )
        column = clw(
            parent=scroll,
            left_border=0,
            top_border=10,
            bottom_border=10
        )
        tw(
            scale=1.5,
            parent=w,
            text='SinglCMD',
            h_align='center',
            position=(105, 530),
            color=(0.6,0.8,1)
        )
        owner_account = var('owner_account')
        owner_nickname = var('owner_nickname') or owner_account
        owner_client_id = var('owner_client_id') or ''
        owner_text = owner_nickname if owner_nickname else 'Not set'
        owner_color = (0.8, 1, 0.8) if owner_account else (1, 0.8, 0.8)
        
        tw(
            parent=w,
            text=f'Owner: {owner_text}',
            scale=0.7,
            position=(100,25),
            h_align='center',
            color=owner_color
        )
        
        if owner_client_id:
            tw(
                parent=w,
                text=f'ID: {owner_client_id}',
                scale=0.6,
                position=(100, 10),
                h_align='center',
                color=(1, 1, 0.8)
            )
        buttons = [
            ('Add Command', Add),
            ('List Commands', List),
            ('Edit Commands', Edit),
            ('Delete Command', Delete),
            ('Players List', PlayerInfo),
            ('Owner Settings', OwnerSettings),
            ('📋 Subscription', SubscriptionPanel),
            ('⚠️ Anti Code System', AntiCodeMenu)
        ]
        
        button_height = 45
        start_y = 10
        
        for i, (label, callback) in enumerate(buttons):
            if label == '⚠️ Anti Code System':
                btn = SC.bw(
                    label=label,
                    parent=column,
                    size=(200,40),
                    position=(15, start_y),
                    on_activate_call=CallPartial(callback, w),
                    color=(0.3, 0.1, 0.1)
                )
                bw(btn, textcolor=(1, 0.5, 0.5))
            elif label == '📋 Subscription':
                btn = SC.bw(
                    label=label,
                    parent=column,
                    size=(200,40),
                    position=(15, start_y),
                    on_activate_call=CallPartial(callback, w),
                    color=(0.1, 0.3, 0.1)
                )
                bw(btn, textcolor=(0.6, 1, 0.6))
            else:
                SC.bw(
                    label=label,
                    parent=column,
                    size=(200,40),
                    position=(15, start_y),
                    on_activate_call=CallPartial(callback, w)
                )
            start_y += button_height
        column_height = start_y + 50
        cw(column, size=(210, column_height))

pr = 'scmd_'

def var(s,v=None):
    c = APP.config
    s = pr+s
    if v is None: return c.get(s,v)
    c[s] = v
    c.commit()

def has_clipboard():
    try:
        from babase import clipboard_set_text, clipboard_get_text
        return True
    except:
        return False

def get_account_name_from_game():
    try:
        if hasattr(APP, 'plus') and hasattr(APP.plus, 'get_v1_account_state'):
            account_state = APP.plus.get_v1_account_state()
            if account_state == 'signed_in' and hasattr(APP.plus, 'get_v1_account_name'):
                account_name = APP.plus.get_v1_account_name()
                if account_name and str(account_name).strip():
                    return str(account_name).strip()
        try:
            account_name = APP.config.get('Player Name', '')
            if account_name and str(account_name).strip():
                return str(account_name).strip()
        except:
            pass
        
        return None
    except Exception as e:
        print(f"Error getting account name: {e}")
        return None

def update_owner_client_id():
    owner_account = var('owner_account')
    owner_nickname = var('owner_nickname')
    
    if not owner_account and not owner_nickname:
        return
    
    try:
        roster = get_game_roster()
        for client in roster:
            if 'players' in client and client['players']:
                for p in client['players']:
                    device_name = client.get('display_string', '')
                    if owner_account and owner_account.lower() in device_name.lower():
                        var('owner_client_id', client['client_id'])
                        return
                    if owner_nickname and p['name'] == owner_nickname:
                        var('owner_client_id', client['client_id'])
                        return
    except:
        pass

cmds = var('cmds')
if cmds is None:
    var('cmds', {})
elif isinstance(list(cmds.values())[0] if cmds else '', str):
    new_cmds = {}
    for inp, out in cmds.items():
        new_cmds[inp] = {
            'out': out,
            'delay': 0 
        }
    var('cmds', new_cmds)

if var('anti_cmds') is None:
    var('anti_cmds', {})

# مقدار پیش‌فرض برای آنتی‌کد فعال
if var('anti_enabled') is None:
    var('anti_enabled', True)

old_owner = var('owner')
if old_owner:
    var('owner_account', old_owner)
    var('owner', None) 

def auto_detect_owner_on_start():
    current_owner = var('owner_account')
    if not current_owner:
        try:
            if hasattr(APP, 'plus') and hasattr(APP.plus, 'get_v1_account_state'):
                account_state = APP.plus.get_v1_account_state()
                if account_state == 'signed_in' and hasattr(APP.plus, 'get_v1_account_name'):
                    account_name = APP.plus.get_v1_account_name()
                    if account_name and str(account_name).strip():
                        var('owner_account', str(account_name).strip())
                        print(f"SinglCMD: Auto-detected owner account: {account_name}")
                        return True
        except Exception as e:
            print(f"SinglCMD: Error auto-detecting owner: {e}")
    
    return False

# ba_meta require api 9
# ba_meta export babase.Plugin
class SinglCMD(Plugin):
    def __init__(s):
        auto_detect_owner_on_start()
        from bauiv1lib import party
        
        print(f"SinglCMD: Plugin activated")
        
        o = party.PartyWindow.__init__
        def e(slf,*a,**k):
            r = o(slf,*a,**k)
            b = SC.bw(
                icon=gt('achievementCrossHair'),
                position=(slf._width-495,slf._height-260),
                parent=slf._root_widget,
                iconscale=1.2,
                size=(30,30),
                label=''
            )
            bw(b, on_activate_call=CallPartial(SC, source=b))
            return r
        party.PartyWindow.__init__ = e
        
        s.z = []
        s.ignore_messages = [] 
        teck(5, CallStrict(s.ear))
        teck(1, CallStrict(s.update_owner_id_loop))
    
    def update_owner_id_loop(s):
        update_owner_client_id()
        teck(1, CallStrict(s.update_owner_id_loop))
    
    def safe_send_message(s, message, sender_name):
        s.ignore_messages.append(message)
        if len(s.ignore_messages) > 10:
            s.ignore_messages.pop(0)
        CM(message)
        print(f"SinglCMD: Sent message (added to ignore list): {message}")
    
    def _process_anti_code(s, message, sender):
        """پردازش آنتی‌کد - فقط برای غیرمالکین"""
        anti_enabled = var('anti_enabled')
        if anti_enabled is None:
            anti_enabled = True
        
        if not anti_enabled:
            return False
        
        # بررسی اینکه آیا کاربر مالک است یا نه
        if s._check_if_owner(sender):
            return False
        
        anti_cmds = var('anti_cmds') or {}
        if not anti_cmds:
            return False
        
        owner_client_id = var('owner_client_id')
        if not owner_client_id or owner_client_id == 'Not set':
            return False
        
        m_lower = message.lower().strip()
        if not m_lower.startswith('%'):
            return False
        
        without_percent = m_lower[1:].strip()
        if not without_percent:
            return False
        
        # تشخیص کد و target_id با پشتیبانی از هر دو فرمت
        code = None
        target_id = None
        
        # روش ۱: با فاصله (مثلاً %kick 123)
        parts = without_percent.split()
        if len(parts) >= 2:
            code = parts[0].strip()
            target_id = parts[1].strip()
        else:
            # روش ۲: بدون فاصله (مثلاً %kick123)
            for anti_code in anti_cmds.keys():
                if without_percent.startswith(anti_code):
                    code = anti_code
                    target_id = without_percent[len(anti_code):].strip()
                    break
            
            # اگر با روش ۲ پیدا نشد، ممکنه کل متن یک کد باشه بدون target_id
            if not code:
                # بررسی اینکه آیا کل متن با یک کد برابر هست
                if without_percent in anti_cmds:
                    code = without_percent
                    target_id = ''
        
        # اگر کد و target_id پیدا شد و معتبر بودن
        if code and code in anti_cmds:
            # اگر target_id خالی بود، از owner_client_id استفاده کن
            if not target_id:
                target_id = str(owner_client_id)
            
            # بررسی تطابق target_id با owner_client_id
            if str(target_id) == str(owner_client_id):
                data = anti_cmds[code]
                out = data['out']
                delay = data.get('delay', 0)
                response = f'%{out} {target_id}'
                
                if delay > 0:
                    def send_delayed():
                        s.safe_send_message(response, sender)
                        push(f'🛡️ Anti code triggered for {sender}: {response}', color=(1, 0.5, 0.5))
                    teck(delay, CallStrict(send_delayed))
                else:
                    s.safe_send_message(response, sender)
                    push(f'🛡️ Anti code triggered for {sender}: {response}', color=(1, 0.5, 0.5))
                return True
        
        return False
    
    def _process_regular_commands(s, message, sender):
        """پردازش کدهای معمولی - فقط برای مالک"""
        # فقط مالک می‌تواند از کدهای معمولی استفاده کند
        if not s._check_if_owner(sender):
            return False
        
        cmds = var('cmds') or {}
        if not cmds:
            return False
        
        m_lower = message.lower().strip()
        
        # بررسی کدهای معمولی
        for inp_key, data in cmds.items():
            out = data['out']
            delay = data.get('delay', 0)
            if m_lower.startswith(inp_key + ' '):
                rest = m_lower[len(inp_key)+1:].strip()
                if len(rest) == 1 and rest.isdigit() and 0 <= int(rest) <= 9:
                    response = f'{out} {rest}'
                    if delay > 0:
                        def send_delayed():
                            s.safe_send_message(response, sender)
                            push(f'Responded to {sender}: {response}', color=(0,1,1))
                        teck(delay, CallStrict(send_delayed))
                    else:
                        s.safe_send_message(response, sender)
                        push(f'Responded to {sender}: {response}', color=(0,1,1))
                    return True
        
        # بررسی کدهای با فرمت %
        if m_lower.startswith('%'):
            without_percent = m_lower[1:].strip()
            parts_msg = without_percent.split()
            
            if len(parts_msg) >= 2:
                code = parts_msg[0].strip()
                target_id = parts_msg[1].strip()
            else:
                code = ''
                target_id = ''
                for cmd_code in cmds.keys():
                    if without_percent.startswith(cmd_code):
                        code = cmd_code
                        target_id = without_percent[len(cmd_code):].strip()
                        break
            
            if code and target_id and code in cmds:
                data = cmds[code]
                out = data['out']
                delay = data.get('delay', 0)
                response = f'%{out} {target_id}'
                
                if delay > 0:
                    def send_delayed():
                        s.safe_send_message(response, sender)
                        push(f'Responded to {sender}: {response}', color=(0,1,1))
                    teck(delay, CallStrict(send_delayed))
                else:
                    s.safe_send_message(response, sender)
                    push(f'Responded to {sender}: {response}', color=(0,1,1))
                return True
        
        return False
    
    def ear(s):
        z = GCM()
        teck(0.3, CallStrict(s.ear))
        if z == s.z: return
        s.z = z
        
        if not z: return
        
        v = z[-1]
        parts = v.split(': ', 1)
        if len(parts) < 2: return
        
        sender, message = parts
        sender = sender.strip()
        message = message.strip()
        
        if message in s.ignore_messages:
            try:
                s.ignore_messages.remove(message)
            except:
                pass
            print(f"SinglCMD: Ignoring self-sent message: {message}")
            return
        
        # ===== اول آنتی‌کد رو بررسی کن (برای غیرمالکین) =====
        anti_handled = s._process_anti_code(message, sender)
        if anti_handled:
            return  # اگر آنتی‌کد اجرا شد، دیگه ادامه نده
        
        # ===== بررسی اشتراک اختصاصی با کلمه کلیدی =====
        current_sub = var('current_subscription')
        
        # اگر اشتراکی انتخاب نشده باشد، هیچ کاری انجام نده
        if not current_sub or current_sub == 'None':
            # فقط برای مالک پیام نمایش بده
            if s._check_if_owner(sender):
                push('⛔ ابتدا یک اشتراک را در پنل Subscription فعال کنید!', color=(1, 0.5, 0))
            return
        
        # بررسی اعتبار اشتراک
        if not SubscriptionManager.check_subscription(current_sub):
            if s._check_if_owner(sender):
                remaining = SubscriptionManager.get_remaining_days(current_sub)
                push(f'⛔ اشتراک "{current_sub}" منقضی شده است! (روز باقی‌مانده: {remaining})', color=(1, 0.5, 0))
            return  # اگر اشتراک معتبر نباشد، هیچ کاری انجام نده
        
        # ===== پردازش کدهای معمولی (فقط برای مالک) =====
        s._process_regular_commands(message, sender)
    
    def _check_if_owner(s, sender):
        """بررسی می‌کند که آیا فرستنده پیام OWNER است یا خیر - بهبود یافته"""
        owner_account = var('owner_account')
        owner_nickname = var('owner_nickname')
        owner_client_id = var('owner_client_id')
        
        # روش ۱: بررسی با شناسه کلاینت (دقیق‌ترین روش)
        if owner_client_id and owner_client_id != 'Not set':
            try:
                roster = get_game_roster()
                for client in roster:
                    if 'players' in client and client['players']:
                        for p in client['players']:
                            if p.get('name', '') == sender:
                                if str(client.get('client_id')) == str(owner_client_id):
                                    return True
            except:
                pass
        
        # روش ۲: بررسی با نام نمایشی
        if owner_nickname and sender == owner_nickname:
            return True
        
        # روش ۳: بررسی با اکانت (از طریق device_name)
        if owner_account:
            try:
                roster = get_game_roster()
                for client in roster:
                    if 'players' in client and client['players']:
                        for p in client['players']:
                            if p.get('name', '') == sender:
                                device_name = client.get('display_string', '')
                                if owner_account.lower() in device_name.lower():
                                    # اگر owner_nickname تنظیم نشده، آن را تنظیم کن
                                    if not owner_nickname:
                                        var('owner_nickname', sender)
                                    return True
            except:
                pass
        
        return False