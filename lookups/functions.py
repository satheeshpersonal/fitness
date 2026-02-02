from django.core.mail import EmailMessage, BadHeaderError
import smtplib
from decouple import config
import requests

def send_email(subject, body, to_email, cc_email=None):
    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=config('DEFAULT_FROM_EMAIL'),
        to=to_email,
    )
    # email.send()
    try:
        result = email.send(fail_silently=False)
        if result == 1:
            print("Email sent successfully ✅")
        else:
            print("Email not sent ❌")
    except BadHeaderError as e:
        print(f"Invalid header found: : {e}")
    except smtplib.SMTPException as e:
        print(f"SMTP error: {e}")
    except Exception as e:
        print(f"Other error: {e}")


def send_sms(otp, to_number):
    url = "https://www.fast2sms.com/dev/bulkV2"
    payload = {
        "route" : "otp",
        "variables_values" : otp, #only otp
        "numbers" : to_number,
    }

    headers = {
        "authorization":config('FAST2SMS_API_KEY'),
        "Content-Type":"application/json"
    }

    response = requests.post(url, data=payload, headers=headers)
    print("Status Code:", response.status_code)
    # print("Response Headers:", response.headers)
    print("Response Text:", response.text)
    print("Response JSON (if any):", response.json() if response.headers.get('Content-Type') == 'application/json' else "Not JSON")


def send_template_email(subject, body, to_email, cc_email=None, template_key = None):
    send_email(subject, body, to_email, cc_email)