# REQUIREMENTS ------------
# pip install requests
# -------------------------

# TODO:
# No validation done by assume everything is ok,
# But better to write validation logic too

import requests
import json
import os
from datetime import date, datetime

from utility import getStudent
from utility import getStaff
from utility import strip_strings

# Use SL timezone
os.environ["TZ"] = "Asia/Colombo"

# Where the API is available
apiBase = "https://api.ce.pdn.ac.lk"

# Where this API locates
apiIndex = "https://api.ce.pdn.ac.lk/publications/v1"
# apiIndex = 'http://localhost:4001/publications/v1'

# Where the student data available
studentSource = "../people/v1/students/all/index.json"

# Where the staff data available
staffSource = "../people/v1/staff/all/index.json"

DEFAULT_PROFILE_IMAGE = "https://people.ce.pdn.ac.lk/images/students/default.jpg"

# Gather Student API data
student_file = open(studentSource)
students = json.load(student_file)

# Gather Staff API data
staff_file = open(staffSource)
staff = json.load(staff_file)


# ------------------------------------------------------------------------------


# Get a unique identifier for each publication from the DOI link
def get_id_from_doi(doi):
    doi_id = doi.replace("http://", "").replace("https://", "")
    doi_id = doi_id.replace("doi.org/", "")
    doi_id = doi_id.replace("doi:", "")
    return doi_id.strip()


# Write individual files for each publication


def write_publication(data):
    doi_id = get_id_from_doi(data["doi"])

    if doi_id != "#":
        filename = "../publications/v1/{0}/index.json".format(doi_id)
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as f:
            f.write(json.dumps(data, indent=4))

        # Debug:
        print("{}\n  > {}, {}\n".format(data["title"], data["venue"], data["year"]))


# ------------------------------------------------------------------------------


google_form_link = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQkkmY3EMIGJamXqsR0eSku9hGxrVcq_5R1EdY_laqhajwsHkROj9XWYxUbNcM4yYjw4nrcRr5XpSZY/pub?output=tsv"

pub_raw = requests.get(
    google_form_link, headers={"Cache-Control": "no-cache"}
).text.split("\n")
publications = []

# Source file index
TIMESTAMP = 0
EMAIL = 1
TITLE = 2
VENUE = 3
YEAR = 4
DOI = 5
ABSTRACT = 6
AUTHORS = 7
AUTHOR_IDS = 8
PREPRINT = 9
PRESENTATION = 10
CODEBASE = 11
RESEARCH_GROUPS = 12
TAGS = 13
FUNDING = 14
PDF = 15
BIB = 16
PROJECT_URL = 17
DEPT_AFFILIATION = 18

FIELD_COUNT = 19


# Skip the header line
for line in pub_raw[1:]:
    try:
        # TODO: Allow to edit the JSON file
        # TODO: Wrap with try catch block, and error notification via Discord

        pub_raw_data = line.replace("\r", "").split("\t")

        if len(pub_raw_data) != FIELD_COUNT:
            print("Not supported: (", len(pub_raw_data), ")")
            continue

        dept_affiliation = True if pub_raw_data[DEPT_AFFILIATION] == "Yes" else False

        submitted_on = datetime.strptime(pub_raw_data[TIMESTAMP], "%m/%d/%Y %H:%M:%S")
        authors = [x.strip() for x in pub_raw_data[AUTHORS].split(",")]
        author_ids = [x.strip() for x in pub_raw_data[AUTHOR_IDS].split(",")]

        research_groups = [x.strip() for x in pub_raw_data[RESEARCH_GROUPS].split(",")]
        if len(research_groups) == 1 and research_groups[0] == "":
            research_groups = []

        tags = [x.strip() for x in pub_raw_data[TAGS].split(",")]
        if len(tags) == 1 and tags[0] == "":
            tags = []

        author_info = []

        for author in author_ids:
            author_id = author.split("@")[0]

            if author_id in students:
                person_card = getStudent(apiBase, students, author_id)
                if person_card != None:
                    author_info.append(person_card)
            elif author_id in staff:
                person_card = getStaff(apiBase, staff, author_id)
                if person_card != None:
                    author_info.append(person_card)
            else:
                author_info.append(
                    {
                        "type": "OUTSIDER",
                        "id": author_id,
                        "name": "",
                        "email": "",
                        "profile_image": "#",
                        "profile_url": "#",
                    }
                )

        author_cards = []
        if len(authors) != len(author_info):
            for aIdx in range(len(authors)):
                author_cards.append(
                    {
                        "name": authors[aIdx],
                        "type": "UNDETERMINED",
                        "id": author_id,
                        "email": "",
                        "profile_image": "#",
                        "profile_url": "#",
                    }
                )
        else:
            for aIdx in range(len(authors)):
                if author_info[aIdx]["type"] == "OUTSIDER":
                    author_cards.append(
                        {
                            "name": authors[aIdx],
                            "profile": "#",
                            "type": "OUTSIDER",
                            "id": "",
                            "email": "",
                            "profile_image": "#",
                            "profile_url": "#",
                        }
                    )
                else:
                    author_cards.append(
                        {
                            "name": authors[aIdx],
                            "profile": author_info[aIdx]["profile_url"],
                            "type": author_info[aIdx]["type"],
                            "id": author_info[aIdx]["id"],
                            "email": author_info[aIdx]["email"],
                            "profile_image": author_info[aIdx]["profile_image"],
                            "profile_url": author_info[aIdx]["profile_url"],
                        }
                    )

        api_url = "{0}/publications/v1/{1}/".format(
            apiBase, get_id_from_doi(pub_raw_data[DOI])
        )

        edit_url = (
            api_url.replace(
                "https://api.ce.pdn.ac.lk/",
                "https://github.com/cepdnaclk/api.ce.pdn.ac.lk/blob/main/",
            )
            + "index.json"
        )

        pub_data = {
            "title": pub_raw_data[TITLE].strip(),
            "venue": pub_raw_data[VENUE].strip(),
            "year": pub_raw_data[YEAR].strip(),
            "abstract": pub_raw_data[ABSTRACT],
            "authors": authors,
            # "author_ids": author_ids,
            # "author_info": author_info,
            "author_info": author_cards,
            "doi": pub_raw_data[DOI],
            "is_dept_affiliated": dept_affiliation,
            "preprint_url": pub_raw_data[PREPRINT] or "#",
            "pdf_url": pub_raw_data[PDF] or "#",
            "presentation_url": pub_raw_data[PRESENTATION] or "#",
            "project_url": pub_raw_data[PROJECT_URL] or "#",
            "codebase": pub_raw_data[CODEBASE] or "#",
            "research_groups": research_groups,
            "tags": tags,
            "funding": pub_raw_data[FUNDING],
            "api_url": api_url,
            "edit_url": edit_url,
            "submitted": datetime.strftime(submitted_on, "%Y/%m/%d %H:%M:%S"),
        }

        strip_strings(pub_data)

        # Write into an individual file
        write_publication(pub_data)

        # Append into all list
        publications.append(pub_data)

    except:
        print("Error occurred")
        print(pub_raw_data)

filename = "../publications/v1/all/index.json"
os.makedirs(os.path.dirname(filename), exist_ok=True)
with open(filename, "w") as f:
    f.write(json.dumps(publications, indent=4))
