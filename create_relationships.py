import os
import re
import csv
import json
import requests


GITHUB = {}
GITHUB['USER'] = ''
GITHUB['TOKEN'] = ''


def get_issue_comments(comments_url):
    comments = requests.get(comments_url, auth=(
        GITHUB['USER'], GITHUB['TOKEN'])).json()
    if comments != []:
        comments_text = []
        for comment in comments:
            text = comment['body']
            comments_text.append(text)
        return ' '.join(comments_text)
    else:
        return ''


def get_ror_name(ror_id):
    url = 'https://api.ror.org/organizations/' + ror_id
    ror_data = requests.get(url).json()
    return ror_data['name']


def extract_relationships():
    pages = [1, 2, 3]
    issue_urls = []
    outfile = os.getcwd() + '/relationships.csv'
    header = ['Issue # from Github', 'Issue URL', 'Issue title from Github', 'Name of org in Record ID', 'Record ID',
              'Related ID', 'Name of org in Related ID', 'Relationship of Related ID to Record ID', 'Current location of Related ID']
    with open(outfile, 'w') as f_out:
        writer = csv.writer(f_out)
        writer.writerow(header)
    # approved column url
    url = 'https://api.github.com/projects/columns/13954326/cards'
    for page in pages:
        params = {'page': page, 'per_page': 100}
        cards = requests.get(url, auth=(
            GITHUB['USER'], GITHUB['TOKEN']), params=params).json()
        for card in cards:
            if 'content_url' in card:
                issue_urls.append(card['content_url'])
    for issue_url in issue_urls:
        issue_data = requests.get(issue_url, auth=(
            GITHUB['USER'], GITHUB['TOKEN'])).json()
        issue_number = issue_data['number']
        issue_title = issue_data['title']
        org_name, org_ror_id = '', ''
        issue_text = issue_data['body'] + \
            get_issue_comments(issue_url + '/comments')
        search_org_name = re.search(
            r'(?<=Name of organization\:)(.*)(?=\n)', issue_text)
        if search_org_name is not None:
            org_name = search_org_name.group(0).strip()
        search_ror_id = re.search(r'(?<=ROR ID\:)(.*)(?=\n)', issue_text)
        if search_ror_id is not None:
            org_ror_id = search_ror_id.group(0).strip()
        rel_pattern = re.compile(
            r'[https]{0,5}\:\/\/ror\.org\/[a-z0-9]{9}\s+\([a-zA-Z]{0,}\)')
        relationships = rel_pattern.findall(issue_text)
        for relationship in relationships:
            relationship = relationship.split(' ')
            relationships = [r.strip() for r in relationships if r != '']
            related_ror_id = relationship[0].strip()
            relationship_type = relationship[1].strip().lower()
            relationship_type = re.sub(r'[()]', '', relationship_type)
            related_name = get_ror_name(related_ror_id)
            with open(outfile, 'a') as f_out:
                rel_type_mappings = {'parent': 'child',
                                     'child': 'parent', 'related': 'related'}
                entry = [issue_number, issue_data['html_url'], issue_title, org_name,
                         org_ror_id, related_ror_id, related_name, relationship_type, 'Production']
                try:
                    inverted_entry = [issue_number, issue_data['html_url'], issue_title, related_name,
                                      related_ror_id, org_ror_id, org_name, rel_type_mappings[relationship_type], 'Production']
                except KeyError:
                    inverted_entry = [issue_number, issue_url, issue_title, related_name,
                                      related_ror_id, org_ror_id, org_name, 'Error', 'Production']
                writer = csv.writer(f_out)
                writer.writerow(entry)
                writer.writerow(inverted_entry)


if __name__ == '__main__':
    extract_relationships()
