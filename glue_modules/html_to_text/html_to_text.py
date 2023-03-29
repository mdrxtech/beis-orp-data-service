import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from htmldate import find_date

def get_title_and_text(URL):
    '''
    params: req: request URL
    returns: title, text: Str
    '''
    req = requests.get(URL)
    soup = BeautifulSoup(req.text, 'html.parser')

    title = str(soup.head.title.get_text())
    text = re.sub('\\s+', ' ', str(soup.get_text()).replace('\n', ' '))

    return title, text


def get_publication_modification_date(URL):
    '''
    params: URL: Str
    returns: publication_date, modification_date: Str
    '''
    # Initally disable extensive search
    publication_date = str(
        find_date(URL, original_date=True, extensive_search=False))
    modification_date = str(find_date(URL, extensive_search=False))

    # If no concrete date is found, do extensive search
    if publication_date == 'None':
        publication_date = str(find_date(URL, original_date=True))

    if modification_date == 'None':
        modification_date = str(find_date(URL))

    publication_date = pd.to_datetime(publication_date).isoformat()
    modification_date = pd.to_datetime(modification_date).isoformat()

    return publication_date



def html_converter(url):

    title, text = get_title_and_text(url)
    date_published = get_publication_modification_date(url)

    return text, title, date_published