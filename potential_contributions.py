import configparser
import smtplib
import sys
from multiprocessing.pool import ThreadPool as Pool
from random import *
from time import sleep

import httpx
from httpx import get



def main():
    cfg = configparser.ConfigParser(allow_no_value=True)
    cfg.read('config.ini')
    interests, labels = get_section(cfg, section='Interests'), get_section(cfg, section='Labels')
    links = multiprocess_links(gen_gh_interests_urls(cfg=cfg, interests=interests, labels=labels))
    send_email(cfg, links)


def gen_gh_interests_urls(cfg, interests, labels):
    projects_limit = cfg['User']['projects_limit']
    if projects_limit == "":
        print("Set a project limit in config")
        sys.exit(1)
    links = []
    for x in range(int(projects_limit)):
        interest, label = choice(interests), choice(labels)
        links.append(
            "https://api.github.com/search/issues?q={}+label:{}+state:open&sort=created&order=desc".format(interest,
                                                                                                           label))
    return links


def multiprocess_links(urls):
    pool = Pool(10)
    results = [x for x in pool.imap_unordered(get_gh_link, urls) if x is not None]
    return results


def get_gh_link(url):
    sleep(randint(1, 2))
    try:
        r = get(url)
        r.raise_for_status()
        r = r.json()
        gh_link = choice(r.get('items')).get('html_url')
        return gh_link
    except httpx.exceptions.HTTPError:
        print("Requesting from Github too often")
    except Exception as error:
        print("Something unexpected occurred...\n{}".format(error))


def get_section(cfg, section):
    try:
        # Normalize interests strings
        entries = cfg.items(section)
        if not entries:
            print("Add at least one {} in your config.ini".format(section[:-1]))
            sys.exit(1)
    except configparser.NoSectionError:
        print("Error: Add a [{}] section to your config.ini".format(section))
        sys.exit(1)
    except OSError:
        print("Error: No config.ini found.")
        sys.exit(1)
    return [str(x[0]).lower() for x in entries]


def send_email(cfg, links):
    email, name, password = cfg["User"]["email"], cfg["User"]["name"], cfg["User"]["Email_Pass"]
    if email == "" or name == "" or password == "":
        print("Check that you set all the email options in config.ini!")
        sys.exit(1)
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    # If using Gmail, generate an app password @ https://myaccount.google.com/apppasswords
    server.login(user=email, password=password)
    links = '\n'.join(links)
    server.sendmail(
        from_addr=email,
        to_addrs=email,
        msg=f"""Subject: Potential Contributor\n\nHi {name},\nWe found the following projects you might be interested in contributing too.\n\n{links}""")
    server.quit()
    print("Successfully sent Github repos to your email!")


if __name__ == '__main__':
    main()
