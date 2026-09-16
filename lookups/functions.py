from django.core.mail import EmailMessage, BadHeaderError
import smtplib
from decouple import config
import requests
from threading import Thread
import logging

logger = logging.getLogger(__name__)

# def send_email_smtp(subject, body, to_email, cc_email=None):
#     email = EmailMessage(
#         subject=subject,
#         body=body,
#         from_email=config('DEFAULT_FROM_EMAIL'),
#         to=to_email,
#     )
#     # email.send()
#     try:
#         result = email.send(fail_silently=False)
#         if result == 1:
#             print("Email sent successfully ")
#         else:
#             print("Email not sent ")
#     except BadHeaderError as e:
#         print(f"Invalid header found: : {e}")
#     except smtplib.SMTPException as e:
#         print(f"SMTP error: {e}")
#     except Exception as e:
#         print(f"Other error: {e}")

def send_email_api(to_email, param={}, template_id=0, cc_email=None):
    try:
        if isinstance(to_email, list): # if to email is list 
            to_list = [{"email": email} for email in to_email]
        else:
            to_list = [{"email": to_email}]
        
        if isinstance(cc_email, list): # if to email is list 
            cc_list = [{"email": email} for email in cc_email]
        elif cc_email:
            cc_list = [{"email": cc_email}]

        payload = {
            "sender": {
                "email": config("DEFAULT_FROM_EMAIL"),
                "name": "Fitzz"
            },
            "to": to_list,
            # "subject": subject,
            # "htmlContent": f"<p>{body}</p>"
            "templateId": template_id,
            "params": param
        }

        if cc_email:
            payload["cc"] = cc_list

            
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": config("EMAIL_HOST_API_KEY"),
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10  # prevents long hanging
        )

        if response.status_code != 201:
            logger.error("Brevo email failed [%s]: %s", response.status_code, response.text)

    except Exception:
        logger.exception("Email API request failed")


def send_sms(otp, to_number):
    url = "https://www.fast2sms.com/dev/bulkV2"
    payload = {
        # "route" : "otp",
        # "variables_values" : otp, #only otp
        "route": "q",   # transactional route
        "message": f"Fitzz: Your OTP is {otp}. Valid for 5 minutes. Do not share this code.",
        "numbers" : to_number,
    }

    headers = {
        "authorization":config('FAST2SMS_API_KEY'),
        "Content-Type":"application/json"
    }

    response = requests.post(url, data=payload, headers=headers)
    # print("Response Headers:", response.headers)


def client_ip(request):
    """Best-effort client IP, honouring the first proxy hop."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def send_admin_notification(subject, html_content, to_email=None):
    """
    Fire-and-forget plain (non-template) email to the Fitzz team. Used for
    website form submissions where a Brevo template would be overkill.
    """
    to_email = to_email or config("CONTACT_NOTIFY_EMAIL", default="admin@fitzz.in")
    to_list = to_email if isinstance(to_email, list) else [to_email]

    def _worker():
        try:
            response = requests.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={
                    "api-key": config("EMAIL_HOST_API_KEY"),
                    "Content-Type": "application/json",
                },
                json={
                    "sender": {"email": config("DEFAULT_FROM_EMAIL"), "name": "Fitzz"},
                    "to": [{"email": e} for e in to_list],
                    "subject": subject,
                    "htmlContent": html_content,
                },
                timeout=10,
            )
            if response.status_code not in (200, 201):
                logger.error(
                    "Admin notification email failed [%s]: %s",
                    response.status_code,
                    response.text,
                )
        except Exception:
            logger.exception("Admin notification email request failed")

    Thread(target=_worker, daemon=True).start()


def _rows(pairs):
    return "".join(
        f"<tr><td style='padding:4px 12px 4px 0;color:#666;white-space:nowrap;"
        f"vertical-align:top'>{label}</td><td style='padding:4px 0'>{value or '—'}</td></tr>"
        for label, value in pairs
    )


def notify_contact_message(obj):
    html = (
        f"<h2 style='margin:0 0 12px'>New contact message</h2>"
        f"<table style='border-collapse:collapse;font-family:sans-serif;font-size:14px'>"
        + _rows([
            ("Name", obj.name),
            ("Email", obj.email),
            ("Phone", obj.phone),
            ("Category", obj.get_category_display()),
            ("Message", obj.message.replace("\n", "<br>")),
            ("Received", obj.created_at.strftime("%d %b %Y, %H:%M")),
        ])
        + "</table>"
    )
    send_admin_notification(f"[Fitzz] Contact: {obj.get_category_display()} — {obj.name}", html)


def notify_partner_lead(obj):
    html = (
        f"<h2 style='margin:0 0 12px'>New partner lead</h2>"
        f"<table style='border-collapse:collapse;font-family:sans-serif;font-size:14px'>"
        + _rows([
            ("Gym", obj.gym_name),
            ("Owner", obj.owner_name),
            ("Mobile", obj.mobile),
            ("Email", obj.email),
            ("City", obj.city),
            ("Notes", obj.message.replace("\n", "<br>")),
            ("Received", obj.created_at.strftime("%d %b %Y, %H:%M")),
        ])
        + "</table>"
    )
    send_admin_notification(f"[Fitzz] Partner lead: {obj.gym_name} ({obj.city})", html)


def send_template_email(template_key, emails, param):
    # send_email_smtp(subject, body, to_email, cc_email)
    cc_email = None
    template_id = 0
    if template_key == "OTP":
        template_id = 1
    elif template_key == "Welcome":
        template_id = 2
    elif template_key == "register_gym":
        template_id = 3
        cc_email = ["admin@fitzz.in"]
    elif template_key == "subscription_plan":
        template_id = 5
        cc_email = ["admin@fitzz.in"]
    elif template_key == "access_session":
        template_id = 4
        cc_email = ["admin@fitzz.in"]
    elif template_key == "access_session_gym_owner":
        template_id = 6
        cc_email = ["admin@fitzz.in"]
    
    if template_id>0:
        Thread(
            target=send_email_api,
            args=(emails["to_email"], param, template_id, cc_email),
            daemon=True
        ).start()
    pass