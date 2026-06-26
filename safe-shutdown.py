"""
obs-safe-shutdown
OBSを安全に終了させ、設定を確実に保存するスクリプト。
PCシャットダウン時にマイクが次回起動時に認識されない問題を解消します。
"""

import sys
import obspython as obs

SCRIPT_VERSION = "0.1.0"
_LOG = "[obs-safe-shutdown]"

# --- Windows 専用のシャットダウン検知 ---
_orig_wndproc = None   # 元の WndProc (整数)
_new_wndproc_ref = None  # GC 防止用の参照
_main_hwnd = None

if sys.platform == "win32":
    import ctypes
    import ctypes.wintypes as wt

    WM_QUERYENDSESSION = 0x0011
    WM_ENDSESSION = 0x0016
    GWL_WNDPROC = -4

    _u32 = ctypes.windll.user32

    # 戻り値・引数型を明示（64bit 対応）
    _u32.SetWindowLongPtrW.restype = ctypes.c_ssize_t
    _u32.SetWindowLongPtrW.argtypes = [wt.HWND, ctypes.c_int, ctypes.c_ssize_t]
    _u32.CallWindowProcW.restype = ctypes.c_ssize_t
    _u32.CallWindowProcW.argtypes = [
        ctypes.c_ssize_t, wt.HWND, ctypes.c_uint, wt.WPARAM, wt.LPARAM
    ]

    _WNDPROC = ctypes.WINFUNCTYPE(
        ctypes.c_ssize_t,
        wt.HWND, ctypes.c_uint, wt.WPARAM, wt.LPARAM
    )


# ---------------------------------------------------------------------------
# OBS スクリプト必須関数
# ---------------------------------------------------------------------------

def script_description():
    return (
        "<b>OBS Safe Shutdown v{ver}</b><br><br>"
        "PCシャットダウン時に OBS の設定を自動保存します。<br>"
        "次回起動でマイクが認識されない問題を解消します。<br><br>"
        "<i>Windows: シャットダウン通知を直接検知して保存します。<br>"
        "その他 OS: OBS 終了イベントで保存します。</i>"
    ).format(ver=SCRIPT_VERSION)


def script_load(settings):
    obs.obs_frontend_add_event_callback(_on_frontend_event)

    if sys.platform == "win32":
        _install_win_handler()

    obs.script_log(obs.LOG_INFO, "{} Loaded (v{})".format(_LOG, SCRIPT_VERSION))


def script_unload():
    if sys.platform == "win32":
        _remove_win_handler()

    obs.obs_frontend_remove_event_callback(_on_frontend_event)
    obs.script_log(obs.LOG_INFO, "{} Unloaded".format(_LOG))


# ---------------------------------------------------------------------------
# 設定保存
# ---------------------------------------------------------------------------

def _save():
    obs.script_log(obs.LOG_INFO, "{} Saving OBS settings...".format(_LOG))
    obs.obs_frontend_save()
    obs.script_log(obs.LOG_INFO, "{} Settings saved successfully.".format(_LOG))


# ---------------------------------------------------------------------------
# OBS フロントエンドイベント（OBS 正常終了時に必ず呼ばれる）
# ---------------------------------------------------------------------------

def _on_frontend_event(event):
    if event == obs.OBS_FRONTEND_EVENT_EXIT:
        obs.script_log(obs.LOG_INFO, "{} OBS exit event detected".format(_LOG))
        _save()


# ---------------------------------------------------------------------------
# Windows: WM_QUERYENDSESSION / WM_ENDSESSION を直接検知
# シャットダウン開始の通知を受け取り次第、OBS が強制終了される前に保存する
# ---------------------------------------------------------------------------

def _install_win_handler():
    """OBS メインウィンドウの WndProc をサブクラス化してシャットダウン通知を横取りする。"""
    global _orig_wndproc, _new_wndproc_ref, _main_hwnd

    try:
        hwnd = obs.obs_frontend_get_main_window_handle()
    except Exception as e:
        obs.script_log(
            obs.LOG_WARNING,
            "{} Could not get main window handle: {} — exit event only".format(_LOG, e),
        )
        return

    if not hwnd:
        obs.script_log(
            obs.LOG_WARNING,
            "{} Main window handle is null — exit event only".format(_LOG),
        )
        return

    _main_hwnd = hwnd

    def _wndproc(h, msg, wparam, lparam):
        if msg == WM_QUERYENDSESSION:
            # シャットダウン / ログオフ / 再起動の通知
            obs.script_log(
                obs.LOG_INFO,
                "{} WM_QUERYENDSESSION — saving before shutdown".format(_LOG),
            )
            _save()
            # 元の WndProc に処理を渡す（TRUE を返してシャットダウンを許可）
            return _u32.CallWindowProcW(_orig_wndproc, h, msg, wparam, lparam)

        if msg == WM_ENDSESSION and wparam:
            # セッション終了確定（最終保存）
            obs.script_log(
                obs.LOG_INFO,
                "{} WM_ENDSESSION — final save".format(_LOG),
            )
            _save()
            return _u32.CallWindowProcW(_orig_wndproc, h, msg, wparam, lparam)

        return _u32.CallWindowProcW(_orig_wndproc, h, msg, wparam, lparam)

    _new_wndproc_ref = _WNDPROC(_wndproc)

    _orig_wndproc = _u32.SetWindowLongPtrW(
        hwnd,
        GWL_WNDPROC,
        ctypes.cast(_new_wndproc_ref, ctypes.c_void_p).value,
    )

    obs.script_log(
        obs.LOG_INFO,
        "{} Windows shutdown handler installed (HWND=0x{:X})".format(_LOG, hwnd),
    )


def _remove_win_handler():
    """サブクラス化を解除して元の WndProc を復元する。"""
    global _orig_wndproc, _new_wndproc_ref

    if _main_hwnd and _orig_wndproc:
        _u32.SetWindowLongPtrW(_main_hwnd, GWL_WNDPROC, _orig_wndproc)
        obs.script_log(obs.LOG_INFO, "{} Windows shutdown handler removed".format(_LOG))

    _orig_wndproc = None
    _new_wndproc_ref = None
