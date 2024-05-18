import os
import time

import requests
import datetime as dt
import dotenv
import logging
import sys
import json

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)

dotenv.load_dotenv()

#######################
# Set these variables #
#######################
FROM_EMAIL = ""  # must be a registered from email in sendgrid
TO_EMAILS = []  # where to send notifications. I used my email and  <phone>@vtext.com for a text
BOOKING_CODE = ""  # the booking code from the URL of the ticketing site, a uuid
TICKET_URL = ""  # the URL you got for tickets
PARTY_SIZE = 6  # the number of people in your party


unavailable_dates = [
    dt.date(2024, 2, 26),
    dt.date(2024, 2, 27),
    dt.date(2024, 2, 28),
    dt.date(2024, 2, 29),
    dt.date(2024, 3, 1),
]

####################
# End of variables #
####################

def send_message(msg):
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=TO_EMAILS,
        subject='Date Available at Casa Bonita',
        html_content=msg + f"<br /><br />{TICKET_URL}"
    )
    sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
    response = sg.send(message)
    print(response.status_code)
    print(response.body)
    print(response.headers)


def check_dates():
    url = "https://casatix-api.casabonitadenver.com/api/v2/search"
    headers = {
        "Accept":"*/*",
        "User-Agent":"Mozilla/5.0"
    }
    params = {
        "booking_code": BOOKING_CODE,
        "party_size": PARTY_SIZE,
        "res_date": "",
        "service": "dinner"
    }

    session = requests.Session()

    date = dt.date.today()
    messages = []
    while True:
        # print(date)
        logger.info(f"Checking date {date}")
        date += dt.timedelta(days=1)
        if date in unavailable_dates:
            continue
        params["res_date"] = date.isoformat()
        res = session.get(url, headers=headers,params=params, timeout=10)
        if res.status_code == 400:
            if "Unable to search date" in res.json().get("display_error", ""):
                print(f"{date} is not available yet.")
                break
            if "This code cannot be used for visits after" in res.json().get("display_error", ""):
                print(f"No more dates after {date}.")
                break
        if res.status_code != 200:
            print(f"Error: {res.status_code}\n{res.text}")
            continue
        try:
            data = res.json()
            # print(json.dumps(data,indent=2))
            if 'times_by_table_type' in data:
                if len(data['times_by_table_type']['default'])>0:
                    print(f"{date} has Traditional Dining available for {PARTY_SIZE} people.")
                    messages.append(f"{date} has Traditional Dining available for {PARTY_SIZE} people.")
                if len(data['times_by_table_type']['counter'])>0:
                    print(f"{date} has Cliffside Dining available for {PARTY_SIZE} people.")
                    messages.append(f"{date} has Cliffside Dining available for {PARTY_SIZE} people.")
        except json.decoder.JSONDecodeError:
            print("You might need to solve a captcha.")
            messages.append("You might need to solve a captcha through the url below.")

    if messages:
        send_message("<br />".join(messages))
        # print()


if __name__ == '__main__':
    while True:
        print(f"### {dt.datetime.now()} ###")
        logger.info(f"Checking dates")
        check_dates()
        time.sleep(900)
