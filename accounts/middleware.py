from django.shortcuts import redirect
from django.conf import settings


ALLOWED_PUBLIC_URLS = ["/accounts/login/", "/accounts/login", "/accounts/logout/", "/accounts/logout", "/"]
DOWNLOAD_REQUIRED_PARAMS = ['filehash', 'filename', 'export_file']

class MenuPermissionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.process_request(request)
        if response:
            return response

        response = self.get_response(request)
        return response

    def process_request(self, request):

        # 放行靜態檔案和媒體檔案
        if request.path.startswith(settings.STATIC_URL) or request.path.startswith(settings.MEDIA_URL):
            return None

        # 如果在白名單內，直接放行
        if request.path in ALLOWED_PUBLIC_URLS:
            return None

        # 如果是 superuser 則直接放行
        if request.user.is_superuser:
            return None

        # 取出 session 中該名 user 有權限的網址
        allowed_urls = request.session.get('allowed_urls', [])

        matched_url = next((url for url in allowed_urls if request.path.startswith(url)), None)
        if matched_url:
            # 暫存該 user 最近一次進入的有權限的頁面 url 作為返回點
            request.session['pre_allowed_urls_temp'] = matched_url
            return None
        # 若 request.path 不在 allowed_urls 但該 request.path 是來自於 ajax 請求則放行
        elif request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return None
        # 若是下載請求，直接放行
        elif request.method == 'GET' and any(param in request.GET for param in DOWNLOAD_REQUIRED_PARAMS):
            return None
        else:
            # 如果沒有權限，返回來源頁面
            referer_url = request.session.get('pre_allowed_urls_temp', '/')
            try:
                del request.session['pre_allowed_urls_temp']
            except KeyError:
                pass
            return redirect(referer_url)