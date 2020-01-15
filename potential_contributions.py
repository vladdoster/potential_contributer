import configparser
import random
import smtplib
from time import sleep

import httpx as httpx


def main():
    cfg = configparser.ConfigParser(allow_no_value=True)
    cfg.read('config.ini')
    interests, labels = get_section(cfg, section='Interests'), get_section(cfg, section='Labels')
    links = get_html_links(get_github_projects(cfg, interests=interests, labels=labels))
    send_email(cfg, links)


def get_github_projects(cfg, interests, labels):
    projects_limit = cfg['User']['projects_limit']
    links = []
    for x in range(int(projects_limit)):
        interest, label = random.choice(interests), random.choice(labels)
        links.append(
            f"https://api.github.com/search/issues?q={interest}+label:{label}+state:open&sort=created&order=desc")
    return links


def get_html_links(links):
    html_links = []
    for link in links:
        sleep(1)
        try:
            r = httpx.get(link)
            r.raise_for_status()
            r = r.json()
            # TODO: Implement pagination using modulo math to get older issues
            html_link = r.get('items')[random.randrange(0, len(r.get('items')), 1)]
            html_links.append(html_link.get('html_url'))
            print(html_link.get('html_url'))
        except httpx.exceptions.HTTPError as e:
            print(f"Requesting from Github too often\n{e}")
        except Exception as e:
            print(f"{e}")
    return html_links


def get_section(cfg, section):
    entries = []
    try:
        # Normalize interests strings
        entries = cfg.items(section)
    except configparser.NoSectionError as e:
        print(f"Error: Add a [{section}] section to your config.ini")
        exit(1)
    except OSError as e:
        print("Error: No config.ini found.")
        exit(1)

    entries = [str(x[0]).lower() for x in entries]
    # Make sure user provides >= 1 interest
    # I learned that you should do len(entries)==0, but just not. Python will return false if len == 0
    if not entries:
        print(f"Add at least one {section[:-1]} in your config.ini")
        exit(1)
    return entries


def send_email(cfg, links):
    email, name, password = cfg["User"]["email"], cfg["User"]["name"], cfg["User"]["Email_Pass"]
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    # If using Gmail, generate an app password @ https://myaccount.google.com/apppasswords
    server.login(email, password)
    links = '\n'.join(links)
    server.sendmail(
        email,
        email,
        f"""Subject: Potential Contributor\n\nHi {name},\nWe found the following projects you might be interested in contributing too.\n\n{links}""")
    server.quit()
    print("Successfully sent Github repos to your email!")



if __name__ == '__main__':
    main()
