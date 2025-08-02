from django.core.mail import EmailMessage
from decouple import config
import requests

def send_email(subject, body, to_email, cc_email=None):
    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=config('EMAIL_ADDRESS'),
        to=to_email,
    )
    email.send()


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