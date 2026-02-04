import smtplib
from django.conf import settings
from django.template.loader import render_to_string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from commons.models import parameter


class SendEmail:
    """發送信件"""

    def __init__(self, mailType: str):
        """smtp初始化"""
        email_settings  = parameter.objects.filter(pa_type="EMAIL")
        self.config = {p.pa_key: p.pa_value for p in email_settings}
        self.smtp = smtplib.SMTP(host=self.config.get("HOST"), port=int(self.config.get("PORT")))
        self.smtp.ehlo()
        self.smtp.starttls()
        self.smtp.login(self.config.get("HOST_USER"), self.config.get("HOST_PASSWORD"))

        self.mailtype = mailType

    def send(self, **kwargs):
        """ 根據情境發送信件 """
        # 取得管理員信箱
        admin_email = self.config.get("admin_email")

        match self.mailtype:
            case "password_reset":
                user_email_content = self.__createEmail(
                    subject="密碼重設 - 醫療品質管理系統",
                    template_name="accounts/password_reset_email.html",
                    context=kwargs,
                )
                self.__sendEmail(user_email_content)
            case "not_report":
                # 未提報
                user_email_content = self.__createEmail(
                    subject="科室要素未提報提醒",
                    template_name="reminderletter/not_report.html",
                    context=kwargs,
                )
                self.__sendEmail(user_email_content)

                # 發送給管理員
                kwargs.update({"user_email": admin_email})
                admin_email_content = self.__createEmail(
                    subject="科室要素未提報提醒",
                    template_name="reminderletter/not_report.html",
                    context=kwargs,
                    bcc=True,  # 設定 BCC
                )
                self.__sendEmail(admin_email_content)
            case "abnormal":
                # 指標異常
                user_email_content = self.__createEmail(
                    subject="指標異常提醒",
                    template_name="reminderletter/abnormal.html",
                    context=kwargs,
                )
                self.__sendEmail(user_email_content)

                # 發送給管理員
                kwargs.update({"user_email": admin_email})
                admin_email_content = self.__createEmail(
                    subject="指標異常提醒",
                    template_name="reminderletter/abnormal.html",
                    context=kwargs,
                    bcc=True,  # 設定 BCC
                )
                self.__sendEmail(admin_email_content)


    def __createEmail(self, subject: str, template_name: str, context: dict, bcc: bool = False):
        """寄信內容資訊"""
        html_content = render_to_string(template_name, context=context)
        content = MIMEMultipart()
        content["subject"] = Header(subject, "utf-8")  # 標題
        content["from"] = formataddr((self.config.get("DEFAULT_FROM_NAME"), self.config.get("DEFAULT_FROM_EMAIL")))  # 寄件人
        if bcc:
            content["Bcc"] = context.get("user_email", "")  # BCC 用於管理員通知
        else:
            content["to"] = context.get("user_email", "")  # 收件人

        content.attach(MIMEText(html_content, "html", "utf-8"))
        return content

    def __sendEmail(self, content):
        """發送郵件"""
        try:
            self.smtp.send_message(content)
        except Exception as e:
            print(f"發送郵件時出錯: {e}")
