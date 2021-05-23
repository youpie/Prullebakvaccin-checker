# coding: utf-8
from bs4 import BeautifulSoup
import requests
import re
import time
import datetime
import playsound
from email.message import EmailMessage
import smtplib
import Config2
import webbrowser
import cloudscraper

url = "https://www.prullenbakvaccin.nl/"
Beginspamfixer = True



def daytime():
    now = datetime.datetime.now()
    now_time = now.time()
    return now_time < datetime.time(23,00) and now_time >= datetime.time(7,00)
    

def send_email(message, sbjct, recipient, debug=True):
    print("email sturen")
    msg = EmailMessage()

    msg['Subject'] = sbjct
    msg["From"] = Config2.gmail_account
    msg["To"] = recipient
    msg.set_content(
        message
    )

    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(Config2.gmail_account, Config2.gmail_password)

    server.send_message(msg)
    server.quit()
    if debug:
        print(message)


def poll_site(location):
    """poll site for location and return list of locations"""
    
    try:
        r = requests.get(url + location)
        scraper = cloudscraper.create_scraper()
        r = scraper.get(url + location)
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(e.response.text)
        return None

    soup = BeautifulSoup(r.text, 'html.parser')
    return soup


def parse_priklocatie(s):
    """
    Locatie #95   Heeft geen vaccins
    
    return id 
    """
    m = re.match(r".*#(\d+)", s)
    if m:
        return int(m.groups()[0])
    return -999


priklocatie_status = {}

def Checken(locatie, email, email2):
    global Beginspamfixer
    soup = poll_site(locatie)
    if soup:

        priklocaties = soup.find_all("div", {"class": "card-body"})

        for priklocatie in priklocaties:
            # verwijder <span style='display:none'>scrapen heeft geen zin</span>
            for decoy in priklocatie.find_all('span', style="display:none"):
                decoy.decompose()
            priklocatie = priklocatie.text.replace('\n', ' ')
            priklocatie = priklocatie.replace('Gegevens pas beschikbaar tijdens prikmoment.', '')

            id = parse_priklocatie(priklocatie)
            #stuur een email als een priklocatie is gevonden
            if "heeftgeenvaccins" not in priklocatie.replace(' ', '').lower():
                print('Locatie heeft mogelijk vaccins!', priklocatie)
                playsound.playsound("alarm.mp3")
                send_email("GO GO GO GO GO ER IS EEN VACCIN GEVONDEN " + time.ctime() + priklocatie + url + locatie,
                           "MOGELIJK VACCIN GEVONDEN!!!!!", email)
                if (email2 != "" and Config2.send_emails_to_both == True):
                    send_email("GO GO GO GO GO ER IS EEN VACCIN GEVONDEN " + time.ctime() + priklocatie + url + locatie,
                               "MOGELIJK VACCIN GEVONDEN!!!!!", email2)
                webbrowser.open(url + locatie)

            hash = priklocatie.replace(' ', '')
            status = priklocatie_status.get(id, None)
            if status is None:
                print('Nieuwe locatie', id)
                if Beginspamfixer is False:
                    send_email('Nieuwe locatie: ' + priklocatie,
                               f"Mogelijke vaccinatielocatie gevonden in {locatie}",
                               "Nieuwe Locatie gevonden", email)
                    if (email2 != "" and Config2.send_emails_to_both == True):
                        send_email('Nieuwe locatie: ' + priklocatie,
                                   f"Mogelijke vaccinatielocatie gevonden in {locatie}",
                                   "Nieuwe Locatie gevonden", email2)
            elif status == hash:
                Beginspamfixer = False
                continue
            priklocatie_status[id] = hash

    print('In ' + locatie + ' volgen we %d priklocaties in de buurt...' % len(priklocatie_status))
    print(priklocatie_status)
    print()

print('Start...')
send_email('Prullenbakvaccin checker staat nu aan en werkt', 'Prullenbakvaccin checker staat nu aan', Config2.recipients)
if (Config2.recipients2 != ""):
    send_email('Prullenbakvaccin checker staat nu aan en werkt', 'Prullenbakvaccin checker staat nu aan',
               Config2.recipients2)

while True:

    if not daytime():
        print('geen vaccins in de nacht... morgen weer verder!')
        time.sleep(3600)
        continue

    Checken(Config2.search_domain, Config2.recipients, Config2.recipients2)
    priklocatie_status = {}
    if (Config2.search_domain2 != ""):
        Checken(Config2.search_domain2, Config2.recipients2, Config2.recipients)

    time.sleep(60)



    
