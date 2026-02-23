import asyncio
from playwright.async_api import async_playwright
import requests
import time
import smtplib
from email.message import EmailMessage
import os

EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")
EMAIL_PASS = os.getenv("EMAIL_PASS")

TARGET_REP = "Embassy of the Republic of Estonia in New Delhi"
URL = "https://broneering.mfa.ee/en/"

last_state = set()

def send_email(subject, body):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_FROM, EMAIL_PASS)
        smtp.send_message(msg)

async def check_site():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        page = await browser.new_page()
        await page.goto(URL, wait_until="networkidle", timeout=60000)

        # Wait for dropdown to exist
        await page.wait_for_selector("select", timeout=60000)

        # Select by visible text instead of name attribute
        await page.select_option(
            "select",
            label=TARGET_REP
        )

        await page.wait_for_timeout(3000)

        options = await page.eval_on_selector_all(
            "select[name='service'] option",
            "els => els.map(e => e.textContent.trim()).filter(Boolean)"
        )

        await browser.close()
        return options

async def main_loop():
    global last_state
while True:
    try:
        print("Checking site... page load + dropdown select")
        options = await check_site()
        print("Current options:", options)
            state = set(options)

            trigger_1 = "Long-stay visa (D-visa) application" in state
            trigger_2 = len(state) > 1

            if (trigger_1 or trigger_2) and state != last_state:
                msg = f"Visa update detected\n\nRepresentation: {TARGET_REP}\nOptions now: {options}"
                send_email("Visa slot update", msg)
                last_state = state

            time.sleep(60)
        except Exception as e:
            send_email("Visa monitor error", str(e))
            time.sleep(60)

asyncio.run(main_loop())
