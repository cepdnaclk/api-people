# TODO:
# No validation done by assume everything is ok,
# But better to write validation logic too

import json
import os
import requests
from datetime import date, datetime

os.environ['TZ'] = 'Asia/Colombo'
today = datetime.now()

# The time threshold considered for a notification generation
NOTIFICATION_THRESHOLD = 60*60*24

# Webhook URL is stored as a GitHub Secret, which will be loaded as a Environment Variable at runtime
# https://github.com/cepdnaclk/api.ce.pdn.ac.lk/settings/secrets/actions
ENDPOINT = os.environ['discord_webhook']

# ------------------------------------------------------------------------------

def publish_discord(title, venue, year, authors, doi, tags):
    data = {
        "content": "A new research publication !",
        "username": "CE Department Bot",
        "avatar_url": "https://api.ce.pdn.ac.lk/assets/img/bot_logo.png",
        "embeds": []
    }
    tag_string = ", ".join(tags)
    authors_string = ", ".join(authors)
    venue_string = venue + ", " + year

    embed = {"title": title, "color": "16735232", "fields": []}
    embed['fields'].append({"name": "Published at", "value": venue_string})
    embed['fields'].append({"name": "Authors", "value": authors_string})
    embed['fields'].append({"name": "DOI", "value": doi})
    embed['fields'].append({"name": "Tags", "value": tag_string})

    data['embeds'].append(embed)
    # print(json.dumps(data, indent = 4))
    response = requests.post(ENDPOINT, json=data)
    # print(response.status_code)
    # print(response.content)

    if (response.status_code == 204):
        print("\t Success")
    else:
        print("\t Error ! ", response.status_code, )
        print(response.content)

# ------------------------------------------------------------------------------

# Gather Publications API data
publications_url = '../publications/v1/all/index.json'

with open(publications_url, 'r') as f:
    publications = json.load(f)

    for pub in publications:

        created_time = datetime.strptime(pub['submitted'], "%Y/%m/%d %H:%M:%S")
        title = pub['title']
        venue = pub['venue']
        year = pub['year']
        authors = pub['authors']
        doi = pub['doi']
        tags = pub['tags']

        duration = today - created_time
        print("\n>> ", title, duration, duration.total_seconds())

        # This is a temp line for testing
        # publish_discord(title, venue, year, authors, doi, tags)
        # break; # Only one so far

        # The publication was submitted within last 24 hours, will send into the Discord Channel, 'publications'
        # TODO: Create a seperate Discord Channel
        if (duration.total_seconds() <= NOTIFICATION_THRESHOLD):
            publish_discord(title, venue, year, authors, doi, tags)
