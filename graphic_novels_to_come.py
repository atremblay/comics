#! /Users/atremblay/anaconda/bin/python

import requests
from bs4 import BeautifulSoup
import datetime
import asyncio
import aiohttp
from itertools import groupby
import time
import re

format = '%m/%d/%Y'
today = datetime.datetime.today()
date = datetime.datetime.strftime(today, format)
date_end = datetime.datetime.strftime(
    today + datetime.timedelta(weeks=4), format)

base_url = "http://www.dccomics.com"


class Comic(object):
    """docstring for Comic"""
    def __init__(self):
        super(Comic, self).__init__()
        self.title = None
        self.url = None
        self.on_sale = None
        self.binding = None

    def set_on_sale(self, value):
        pattern = "On Sale ([\d]*)\/([\d]*)"
        m = re.match(pattern, value)
        if m is None:
            raise RuntimeError("Could not parse the provided date")
        year = datetime.datetime.now().year
        month = int(m.groups()[0])
        day = int(m.groups()[1])
        self.on_sale = datetime.date(year, month, day)

    def __repr__(self):
        r = "Title: {}\n\tURL: {}\n\tOn Sale: {}\n\tBinding: {}\n"
        r = r.format(self.title, self.url, self.on_sale, self.binding)
        return r


def get_comics(soup):
    div = soup.find('div', attrs={'class': "browse-results-wrapper"})
    lis = div.findAll('li')
    comics = []
    for li in lis:
        title_div = li.find('div', attrs={'class': 'title'})
        a = title_div.find('a')
        title = a.text
        on_sale = title_div.find('span').text

        comic = Comic()
        comic.title = title
        comic.url = base_url + "/" + a.attrs['href']
        comic.set_on_sale(on_sale)

        comics.append(comic)

    return comics


@asyncio.coroutine
def set_binding(comic):
    response = yield from aiohttp.request('GET', comic.url)
    content = yield from response.read_and_close()
    soup = BeautifulSoup(content)
    div = soup.find(
        'div',
        attrs={'class': "views-field views-field-field-binding"})
    binding = div.find(
        'div',
        attrs={"class": "field-content"}).text
    comic.binding = binding
    return comic


def main():
    params = {
        'content_type': 'graphic_novel',
        'date': date,
        'date_end': date_end
    }

    response = requests.get(base_url + '/browse', params=params)
    soup = BeautifulSoup(response.content)
    comics = get_comics(soup)

    loop = asyncio.get_event_loop()
    t = loop.run_until_complete(
        asyncio.wait([set_binding(comic) for comic in comics]))

    comics = [task.result() for task in t[0]]
    softcover = filter(lambda comic: comic.binding == 'Softcover', comics)
    softcover = sorted(softcover, key=lambda comic: comic.on_sale)

    for g in groupby(softcover, key=lambda comic: comic.on_sale):

        print(g[0])
        for comic in sorted(g[1], key=lambda x: x.title):
            print("\t{}".format(comic.title.lower()))


if __name__ == '__main__':
    main()
