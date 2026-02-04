# myapp/utils/request_user.py (或放在你項目的通用 utils.py 中)
import threading

_thread_locals = threading.local()


def get_current_user():
    """獲取存儲在線程局部變量中的當前用戶"""
    return getattr(_thread_locals, 'user', None)


def set_current_user(user):
    """將當前用戶存儲在線程局部變量中"""
    _thread_locals.user = user


def clear_current_user():
    """清除線程局部變量中的用戶信息"""
    if hasattr(_thread_locals, 'user'):
        del _thread_locals.user


# --- 針對異步環境 (如果你使用了 ASGI 且有異步操作保存模型) ---
try:
    from asgiref.local import Local
except ImportError:
    _async_locals = None
else:
    _async_locals = Local()


def get_current_user_async():
    if _async_locals is None:
        return get_current_user()
    return getattr(_async_locals, 'user', None)


def set_current_user_async(user):
    if _async_locals is None:
        set_current_user(user)
        return
    _async_locals.user = user


def clear_current_user_async():
    if _async_locals is None:
        clear_current_user()
        return
    if hasattr(_async_locals, 'user'):
        del _async_locals.user
