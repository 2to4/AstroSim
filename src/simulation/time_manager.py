"""
時間管理クラスの実装

シミュレーション時間の制御、ユリウス日の変換、
時間倍率の制御などを行います。
"""

import time
from datetime import datetime, timezone
from typing import Optional, Callable


class TimeManager:
    """
    シミュレーション時間を管理するクラス
    
    実時間とシミュレーション時間の対応、
    時間倍率制御、一時停止機能などを提供します。
    """
    
    def __init__(self):
        """時間管理システムの初期化"""
        self.current_julian_date: float = 0.0
        self.time_scale: float = 1.0  # 時間倍率（1.0 = 実時間）
        self.is_paused: bool = False
        self.epoch_j2000: float = 2451545.0  # J2000.0 epoch
        
        # 内部状態
        self._last_update_time: float = 0.0
        self._accumulated_time: float = 0.0
        self._start_time: float = 0.0
        
        # コールバック
        self._time_change_callbacks: list[Callable[[float], None]] = []
        
        # 初期時刻設定（現在時刻）
        self.set_date(datetime.now(timezone.utc))
    
    def set_date(self, date: datetime) -> None:
        """
        シミュレーション開始日時を設定
        
        Args:
            date: 設定する日時（UTCタイムゾーン推奨）
        """
        # タイムゾーン情報がない場合はUTCとして扱う
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        
        # UTCに変換
        utc_date = date.astimezone(timezone.utc)
        
        self.current_julian_date = self.datetime_to_julian(utc_date)
        self._reset_internal_timers()
        
        # コールバック呼び出し
        self._notify_time_change()
    
    def datetime_to_julian(self, dt: datetime) -> float:
        """
        datetime をユリウス日に変換
        
        Args:
            dt: datetime オブジェクト
            
        Returns:
            ユリウス日
        """
        # Julian Day Number の計算（標準的なアルゴリズム）
        year = dt.year
        month = dt.month
        day = dt.day
        
        # 1月と2月は前年の13月、14月として扱う
        if month <= 2:
            year -= 1
            month += 12
        
        # グレゴリオ暦の補正
        a = year // 100
        b = 2 - a + (a // 4)
        
        # ユリウス日の整数部分
        jd_int = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524
        
        # 時刻による小数部分
        time_fraction = (dt.hour + dt.minute / 60.0 + dt.second / 3600.0 + dt.microsecond / 3600000000.0) / 24.0
        
        return jd_int + time_fraction
    
    def julian_to_datetime(self, jd: float) -> datetime:
        """
        ユリウス日を datetime に変換
        
        Args:
            jd: ユリウス日
            
        Returns:
            datetime オブジェクト（UTC）
        """
        # ユリウス日からグレゴリオ暦への変換
        jd_int = int(jd + 0.5)
        jd_frac = jd + 0.5 - jd_int
        
        # アルゴリズムによる逆変換
        a = jd_int + 32044
        b = (4 * a + 3) // 146097
        c = a - (146097 * b) // 4
        d = (4 * c + 3) // 1461
        e = c - (1461 * d) // 4
        m = (5 * e + 2) // 153
        
        day = e - (153 * m + 2) // 5 + 1
        month = m + 3 - 12 * (m // 10)
        year = 100 * b + d - 4800 + m // 10
        
        # 時刻の計算
        total_seconds = jd_frac * 24 * 3600
        hour = int(total_seconds // 3600)
        minute = int((total_seconds % 3600) // 60)
        second = int(total_seconds % 60)
        microsecond = int((total_seconds % 1) * 1000000)
        
        return datetime(year, month, day, hour, minute, second, microsecond, timezone.utc)
    
    def update(self, real_dt: float) -> None:
        """
        時間を進める
        
        Args:
            real_dt: 実時間での経過時間 (秒)
        """
        if self.is_paused:
            return
        
        # シミュレーション時間での経過を計算
        sim_dt_seconds = real_dt * self.time_scale
        sim_dt_days = sim_dt_seconds / (24 * 3600)  # 秒を日に変換
        
        self.current_julian_date += sim_dt_days
        self._accumulated_time += sim_dt_seconds
        
        # コールバック呼び出し
        self._notify_time_change()
    
    def advance_by_days(self, days: float) -> None:
        """
        指定した日数だけ時間を進める
        
        Args:
            days: 進める日数
        """
        if not self.is_paused:
            self.current_julian_date += days
            self._notify_time_change()
    
    def advance_by_seconds(self, seconds: float) -> None:
        """
        指定した秒数だけ時間を進める
        
        Args:
            seconds: 進める秒数
        """
        days = seconds / (24 * 3600)
        self.advance_by_days(days)
    
    def set_time_scale(self, scale: float) -> None:
        """
        時間倍率を設定
        
        Args:
            scale: 時間倍率（1.0 = 実時間、>1.0 = 高速、<1.0 = 低速）
            
        Raises:
            ValueError: 負の値が指定された場合
        """
        if scale < 0:
            raise ValueError("時間倍率は0以上である必要があります")
        
        self.time_scale = scale
    
    def pause(self) -> None:
        """シミュレーションを一時停止"""
        self.is_paused = True
    
    def resume(self) -> None:
        """シミュレーションを再開"""
        self.is_paused = False
        self._reset_internal_timers()
    
    def toggle_pause(self) -> bool:
        """
        一時停止状態を切り替え
        
        Returns:
            新しい一時停止状態
        """
        if self.is_paused:
            self.resume()
        else:
            self.pause()
        return self.is_paused
    
    def get_current_datetime(self) -> datetime:
        """
        現在のシミュレーション時刻をdatetimeで取得
        
        Returns:
            現在のシミュレーション時刻（UTC）
        """
        return self.julian_to_datetime(self.current_julian_date)
    
    def get_j2000_days(self) -> float:
        """
        J2000.0 エポックからの経過日数を取得
        
        Returns:
            J2000.0からの経過日数
        """
        return self.current_julian_date - self.epoch_j2000
    
    def get_j2000_centuries(self) -> float:
        """
        J2000.0 エポックからの経過世紀数を取得
        
        Returns:
            J2000.0からの経過世紀数
        """
        return self.get_j2000_days() / 36525.0
    
    def get_sidereal_time_greenwich(self) -> float:
        """
        グリニッジ恒星時を計算
        
        Returns:
            グリニッジ恒星時 (度)
        """
        t = self.get_j2000_centuries()
        
        # グリニッジ恒星時の計算（IAU 2000A モデル）
        gst = 280.46061837 + 360.98564736629 * self.get_j2000_days() + \
              0.000387933 * t * t - t * t * t / 38710000.0
        
        # 0-360度の範囲に正規化
        return gst % 360.0
    
    def set_time_scale_preset(self, preset: str) -> None:
        """
        時間倍率のプリセットを設定
        
        Args:
            preset: プリセット名 ("real", "minute", "hour", "day", "week", "month", "year")
        """
        presets = {
            "real": 1.0,                    # 実時間
            "minute": 60.0,                 # 1秒 = 1分
            "hour": 3600.0,                 # 1秒 = 1時間
            "day": 86400.0,                 # 1秒 = 1日
            "week": 604800.0,               # 1秒 = 1週間
            "month": 2629746.0,             # 1秒 = 1ヶ月（平均）
            "year": 31556952.0              # 1秒 = 1年（平均）
        }
        
        if preset not in presets:
            raise ValueError(f"無効なプリセット: {preset}. 有効な値: {list(presets.keys())}")
        
        self.set_time_scale(presets[preset])
    
    def add_time_change_callback(self, callback: Callable[[float], None]) -> None:
        """
        時間変更時のコールバックを追加
        
        Args:
            callback: 時間変更時に呼び出される関数（引数: ユリウス日）
        """
        if callback not in self._time_change_callbacks:
            self._time_change_callbacks.append(callback)
    
    def remove_time_change_callback(self, callback: Callable[[float], None]) -> None:
        """
        時間変更コールバックを削除
        
        Args:
            callback: 削除する関数
        """
        if callback in self._time_change_callbacks:
            self._time_change_callbacks.remove(callback)
    
    def _reset_internal_timers(self) -> None:
        """内部タイマーをリセット"""
        current_time = time.time()
        self._last_update_time = current_time
        self._start_time = current_time
        self._accumulated_time = 0.0
    
    def _notify_time_change(self) -> None:
        """時間変更コールバックを呼び出し"""
        for callback in self._time_change_callbacks:
            try:
                callback(self.current_julian_date)
            except Exception as e:
                # コールバックエラーは無視して続行
                print(f"時間変更コールバックエラー: {e}")
    
    def get_time_info(self) -> dict:
        """
        時間管理の詳細情報を取得
        
        Returns:
            時間情報の辞書
        """
        return {
            "julian_date": self.current_julian_date,
            "datetime": self.get_current_datetime().isoformat(),
            "j2000_days": self.get_j2000_days(),
            "j2000_centuries": self.get_j2000_centuries(),
            "time_scale": self.time_scale,
            "is_paused": self.is_paused,
            "sidereal_time": self.get_sidereal_time_greenwich(),
            "accumulated_time": self._accumulated_time
        }
    
    def __str__(self) -> str:
        """文字列表現"""
        dt = self.get_current_datetime()
        status = "一時停止" if self.is_paused else "実行中"
        return f"TimeManager ({dt.strftime('%Y-%m-%d %H:%M:%S')} UTC, x{self.time_scale:.1f}, {status})"
    
    def __repr__(self) -> str:
        """デバッグ用文字列表現"""
        return (f"TimeManager(julian_date={self.current_julian_date}, "
                f"time_scale={self.time_scale}, paused={self.is_paused})")