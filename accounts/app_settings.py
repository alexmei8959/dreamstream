import sys
from django.conf import settings
from .exceptions import AuthenticationMethodEmpty


class AppSettings:
    class AuthenticationMethod:
        USERNAME = "username"
        EMAIL = "email"

    @property
    def AUTHENTICATION_METHODS(self):
        default = {
            self.AuthenticationMethod.USERNAME,
            self.AuthenticationMethod.EMAIL,
        }
        auth_methods = self._setting("AUTHENTICATION_METHODS", default)
        if not auth_methods:
            raise AuthenticationMethodEmpty
        return auth_methods

    @property
    def REGISTER_USERNAME_REQUIRED(self):
        default = True
        return self._setting("REGISTER_USERNAME_REQUIRED", default)

    @property
    def REGISTER_EMAIL_REQUIRED(self):
        default = True
        return self._setting("REGISTER_EMAIL_REQUIRED", default)

    @property
    def REGISTER_FNAME_REQUIRED(self):
        default = True
        return self._setting("REGISTER_FNAME_REQUIRED", default)

    @property
    def REGISTER_LNAME_REQUIRED(self):
        default = False
        return self._setting("REGISTER_LNAME_REQUIRED", default)

    @property
    def REGISTER_CONFIRM_PASSWORD_REQUIRED(self):
        default = True
        return self._setting("REGISTER_CONFIRM_PASSWORD_REQUIRED", default)

    @property
    def PASSWORD_RESET_EMAIL_EXPIRE_MIN(self):
        # 重設密碼驗證信件有效時間
        default = 30   #分鐘
        return self._setting("PASSWORD_RESET_EMAIL_EXPIRE_MIN", default)

    @property
    def LOGIN_REDIRECT_URL(self):
        default = "/index"
        return self._setting("LOGIN_REDIRECT_URL", default)

    @property
    def LOGOUT_REDIRECT_URL(self):
        default = "/"
        return self._setting("LOGOUT_REDIRECT_URL", default)

    @property
    def COUNTRY_CODE(self):
        default = '+886'
        return self._setting("COUNTRY_CODE", default)

    @property
    def ACCOUNT_LOCK_TIMES(self):
        """ 登入失敗幾次帳號就鎖定  """
        default = 5
        return self._setting("ACCOUNT_LOCK_TIMES", default)

    @property
    def ACCOUNT_LOCK_MIN(self):
        """ 帳號鎖定後要多久才解鎖  """
        default = 15
        return self._setting("ACCOUNT_LOCK_MIN", default)

    @staticmethod
    def _setting(name, default):
        ret = getattr(settings, name, default)
        return ret if ret is not None else default


app_settings = AppSettings()
app_settings.__name__ = __name__
# noinspection PyTypeChecker
sys.modules[__name__] = app_settings
