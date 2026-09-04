# ba_meta require api 9
# ba_meta export babase.Plugin

import babase
import bascenev1 as bs
from babase import _math
from bauiv1lib import party
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

# ============================================
# کلاس‌های کمکی برای منو (مثل SC در zed2.py)
# ============================================
class UIHelper:
    @classmethod
    def UIS(cls):
        i = APP.ui_v1.uiscale
        if i == 0:
            return 1.5
        elif i == 1:
            return 1.1
        else:
            return 0.8
    
    @classmethod
    def bw(cls, **k):
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
    
    @classmethod
    def cw(cls, source, ps=0, **k):
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
            scale=cls.UIS() + ps,
            transition='in_scale',
            color=(0.18, 0.18, 0.18),
            **filtered_kwargs
        )
        cw(r, on_outside_click_call=CallPartial(cls.swish, t=r))
        return r
    
    @classmethod
    def swish(cls, t=None):
        gs('swish').play()
        if t:
            cw(t, transition='out_scale')
    
    @classmethod
    def err(cls, t):
        gs('block').play()
        push(t, color=(1, 1, 0))
    
    @classmethod
    def ok(cls):
        gs('dingSmallHigh').play()
        push('✅ Success!', color=(0, 1, 0))

# ============================================
# ذخیره و خواندن تنظیمات
# ============================================
PREFIX = 'autopunch_'

def var(s, v=None):
    c = APP.config
    s = PREFIX + s
    if v is None:
        return c.get(s, v)
    c[s] = v
    c.commit()

# تنظیمات پیش‌فرض
if var('enabled') is None:
    var('enabled', True)
if var('range') is None:
    var('range', 3.0)
if var('mode') is None:
    var('mode', 'punch')  # punch, bomb, kick
if var('cooldown') is None:
    var('cooldown', 0.5)

# ============================================
# منوی تنظیمات اصلی
# ============================================
class AutoPunchMenu:
    def __init__(self, source):
        if hasattr(self, 'w') and self.w:
            try:
                UIHelper.swish(self.w)
            except:
                pass
        
        w = self.w = UIHelper.cw(
            source=source,
            size=(300, 450),
        )
        
        tw(
            parent=w,
            text='🤜 Auto Punch',
            scale=1.2,
            position=(150, 420),
            h_align='center',
            color=(0.6, 0.8, 1)
        )
        
        # وضعیت روشن/خاموش
        enabled = var('enabled')
        self.toggle_btn = UIHelper.bw(
            parent=w,
            label=f'🟢 Status: {"ON" if enabled else "OFF"}',
            size=(200, 35),
            position=(50, 370),
            on_activate_call=CallStrict(self._toggle_enabled),
            color=(0.1, 0.4, 0.1) if enabled else (0.4, 0.1, 0.1)
        )
        
        # نمایش دامنه فعلی
        current_range = var('range')
        tw(
            parent=w,
            text=f'📏 Range: {current_range} meters',
            scale=0.9,
            position=(150, 325),
            h_align='center',
            color=(0.8, 1, 0.8)
        )
        
        # دکمه‌های تنظیم دامنه
        UIHelper.bw(
            parent=w,
            label='− 0.5',
            size=(60, 30),
            position=(70, 290),
            on_activate_call=CallStrict(self._change_range, -0.5),
            color=(0.2, 0.2, 0.4)
        )
        UIHelper.bw(
            parent=w,
            label='+ 0.5',
            size=(60, 30),
            position=(170, 290),
            on_activate_call=CallStrict(self._change_range, 0.5),
            color=(0.2, 0.2, 0.4)
        )
        
        # نمایش حالت فعلی
        current_mode = var('mode')
        mode_names = {
            'punch': '👊 Punch',
            'bomb': '💣 Bomb',
            'kick': '🦶 Kick'
        }
        tw(
            parent=w,
            text=f'Mode: {mode_names.get(current_mode, current_mode)}',
            scale=0.9,
            position=(150, 245),
            h_align='center',
            color=(1, 0.8, 0.6)
        )
        
        # دکمه‌های انتخاب حالت
        UIHelper.bw(
            parent=w,
            label='👊 Punch',
            size=(80, 30),
            position=(20, 210),
            on_activate_call=CallStrict(self._set_mode, 'punch'),
            color=(0.2, 0.2, 0.4)
        )
        UIHelper.bw(
            parent=w,
            label='💣 Bomb',
            size=(80, 30),
            position=(110, 210),
            on_activate_call=CallStrict(self._set_mode, 'bomb'),
            color=(0.2, 0.2, 0.4)
        )
        UIHelper.bw(
            parent=w,
            label='🦶 Kick',
            size=(80, 30),
            position=(200, 210),
            on_activate_call=CallStrict(self._set_mode, 'kick'),
            color=(0.2, 0.2, 0.4)
        )
        
        # نمایش کول‌داون
        cooldown = var('cooldown')
        tw(
            parent=w,
            text=f'⏱ Cooldown: {cooldown}s',
            scale=0.8,
            position=(150, 170),
            h_align='center',
            color=(0.8, 0.8, 1)
        )
        
        # دکمه‌های کول‌داون
        UIHelper.bw(
            parent=w,
            label='− 0.1',
            size=(60, 30),
            position=(70, 135),
            on_activate_call=CallStrict(self._change_cooldown, -0.1),
            color=(0.2, 0.2, 0.4)
        )
        UIHelper.bw(
            parent=w,
            label='+ 0.1',
            size=(60, 30),
            position=(170, 135),
            on_activate_call=CallStrict(self._change_cooldown, 0.1),
            color=(0.2, 0.2, 0.4)
        )
        
        # دکمه تست
        UIHelper.bw(
            parent=w,
            label='🔴 Test (Punch Now!)',
            size=(180, 35),
            position=(60, 85),
            on_activate_call=CallStrict(self._test_punch),
            color=(0.4, 0.1, 0.1)
        )
        
        UIHelper.swish()
    
    def _toggle_enabled(self):
        new_state = not var('enabled')
        var('enabled', new_state)
        UIHelper.ok()
        push(f'Auto Punch {"enabled" if new_state else "disabled"}', 
             color=(0, 1, 0) if new_state else (1, 0.5, 0))
        # رفرش منو
        if hasattr(self, 'w') and self.w:
            UIHelper.swish(self.w)
            teck(0.1, CallStrict(self.__init__, self.w))
    
    def _change_range(self, delta):
        new_range = var('range') + delta
        new_range = max(0.5, min(20.0, new_range))
        var('range', new_range)
        push(f'📏 Range set to {new_range:.1f}m', color=(0, 1, 0))
        if hasattr(self, 'w') and self.w:
            UIHelper.swish(self.w)
            teck(0.1, CallStrict(self.__init__, self.w))
    
    def _set_mode(self, mode):
        var('mode', mode)
        push(f'Mode set to: {mode}', color=(0, 1, 0))
        if hasattr(self, 'w') and self.w:
            UIHelper.swish(self.w)
            teck(0.1, CallStrict(self.__init__, self.w))
    
    def _change_cooldown(self, delta):
        new_cooldown = var('cooldown') + delta
        new_cooldown = max(0.1, min(3.0, new_cooldown))
        var('cooldown', new_cooldown)
        push(f'⏱ Cooldown set to {new_cooldown:.1f}s', color=(0, 1, 0))
        if hasattr(self, 'w') and self.w:
            UIHelper.swish(self.w)
            teck(0.1, CallStrict(self.__init__, self.w))
    
    def _test_punch(self):
        # پیدا کردن اسپاز خودمون
        my_spaz = self._get_my_spaz()
        if my_spaz:
            my_spaz.punch()
            push('🔴 Test punch sent!', color=(1, 0.5, 0))
        else:
            UIHelper.err('⚠️ No spaz found! Are you in a game?')
    
    def _get_my_spaz(self):
        activity = bs.get_foreground_host_activity()
        if not activity:
            return None
        for player in activity.players:
            if player.is_our_player:
                return player.spaz
        return None

# ============================================
# کلاس اصلی افزونه
# ============================================
class AutoPunchPlugin(babase.Plugin):
    def __init__(self):
        print("🤜 AutoPunch Plugin loaded!")
        self.last_punch_time = {}
        
        # اضافه کردن دکمه به صفحه چت (مثل zed2.py)
        self._patch_party_window()
        
        # شروع لوپ چک کردن
        teck(0.5, CallStrict(self._check_loop))
    
    def _patch_party_window(self):
        """اضافه کردن دکمه منو به صفحه چت (PartyWindow)"""
        original_init = party.PartyWindow.__init__
        
        def patched_init(self, *a, **k):
            r = original_init(self, *a, **k)
            
            # اضافه کردن دکمه Auto Punch
            btn = UIHelper.bw(
                icon=gt('achievementCrossHair'),
                position=(self._width - 495, self._height - 260),
                parent=self._root_widget,
                iconscale=1.2,
                size=(30, 30),
                label=''
            )
            bw(btn, on_activate_call=CallPartial(AutoPunchMenu, source=btn))
            return r
        
        party.PartyWindow.__init__ = patched_init
    
    def _check_loop(self):
        """بررسی مداوم بازیکنان نزدیک"""
        if var('enabled'):
            self._check_nearby_players()
        teck(0.1, CallStrict(self._check_loop))
    
    def _check_nearby_players(self):
        """بررسی بازیکنان در دامنه"""
        my_spaz = self._get_my_spaz()
        if not my_spaz:
            return
        
        my_pos = my_spaz.position
        range_limit = var('range')
        cooldown = var('cooldown')
        mode = var('mode')
        
        for spaz in bs.get_all_nodes_of_type(bs.Spaz):
            if spaz is my_spaz:
                continue
            if not spaz or spaz.is_dead:
                continue
            
            dist = _math.vector_distance(my_pos, spaz.position)
            if dist <= range_limit:
                now = babase.time()
                spaz_id = spaz.id
                
                if spaz_id not in self.last_punch_time or (now - self.last_punch_time[spaz_id]) > cooldown:
                    self._perform_action(my_spaz, mode)
                    self.last_punch_time[spaz_id] = now
                    break
    
    def _perform_action(self, spaz, mode):
        """انجام عمل مورد نظر"""
        if mode == 'punch':
            spaz.punch()
        elif mode == 'bomb':
            # پرتاب بمب (اگه بمب داشته باشی)
            try:
                spaz.drop_bomb()
            except:
                pass
        elif mode == 'kick':
            # لگد (اگه ممکن باشه)
            try:
                spaz.kick()
            except:
                pass
    
    def _get_my_spaz(self):
        """پیدا کردن اسپاز خودمون"""
        activity = bs.get_foreground_host_activity()
        if not activity:
            return None
        for player in activity.players:
            if player.is_our_player:
                return player.spaz
        return None
    
    def on_app_quit(self):
        print("🤜 AutoPunch Plugin unloaded!")

# ============================================
# ثبت کلاس اصلی
# ============================================
# ba_meta require api 9
# ba_meta export babase.Plugin
class Mod(AutoPunchPlugin):
    pass