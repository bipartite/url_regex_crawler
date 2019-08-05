#!/usr/bin/env python3

import sys
import getopt
import re
import asyncio
import urllib
import datetime
import aiohttp
import sqlite3
import os

urls_to_check = {}

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), 'url_crawl.sqlite3')


def db_connect(db_path=DEFAULT_PATH):
    con = sqlite3.connect(db_path)
    return con


class RegSearch:
    def __init__(self, num_found, pattern, found_regex):
        self.num_found = num_found
        self.pattern = pattern
        self.found_regex = found_regex

    def __repr__(self):
        return f'RegSearch({self.num_found!r}, {self.pattern!r}, {self.found_regex!r}'


def main(argv):
    inputfile = ''
    try:
        opts, args = getopt.getopt(argv, "hi:", ["ifile="])
    except getopt.GetoptError:
        print("test.py -i <inputfile>")
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print("test.py -i <inputfile>")
            print("<inputfile> format must be lines consisting of url with its corresponding regex(s) all separated by whitespace")
            print("url1 regex1 regex2 ... etc")
            print("url2 regex1 regex2 ... etc")
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        else:
            print("test.py -i <inputfile>")
            sys.exit(2)

    return inputfile


def parse_file(file):
    try:
        with open(file, mode='r') as f:
            for line in f:
                urls_to_check[line.split()[0]] = line.split()[1:]
                # print(urls_to_check)
        return urls_to_check
    except (IOError, IndexError):
        print("File not found or invalid")
        sys.exit(2)


async def call_url(url):
    print('Starting {}'.format(url))
    try:
        response = await aiohttp.ClientSession().get(url)
        data = await response.text()
        print('URL: {} Bytes received: {}'.format(url, len(data)))
        if data is not None:
            await crawl_content(data, url)

        aiohttp.ClientSession().close()
    except (Exception) as err:
        print("Error", err)
        pass


async def crawl_content(content, url):
    regexs = urls_to_check[url]
    for pattern in regexs:
        try:
            prog = re.compile(pattern)

            # Do complete regex search
            found_regex = re.findall(prog, content)

            reg_object = RegSearch(len(found_regex), pattern, found_regex)
            with open("output-{0}.txt".format(urllib.parse.quote(url, '')), mode="a+") as f:
                f.write(str(datetime.datetime.now()))
                f.write('\n')
                f.write(repr(reg_object))
                f.write('\n')

        except re.error as err:
            print("regex error ", repr(err))
            pass


if __name__ == "__main__":
    import time
    s = time.perf_counter()
    if sys.version_info[0] < 3:
        raise Exception("Python 3 or a more recent version is required.")
    inputfile = main(sys.argv[1:])
    parse_file(inputfile)

    tasks = [call_url(url) for url, regexs in urls_to_check.items()]
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()
