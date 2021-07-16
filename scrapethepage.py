#!/usr/local/bin/python3

import time
from datetime import datetime
import os
from bs4 import BeautifulSoup
from selenium import webdriver
import pandas as pd
import json
from collections import Counter
import re
from nltk.corpus import stopwords
from selenium.webdriver.remote.utils import dump_json


class ScrapeThePage:
    def __init__(self):
        path = "/content/drive/MyDrive/stemaway/"
        print(path)
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # open it, go to a website, and get results
        self.driver = webdriver.Chrome(options=options)
        now = datetime.now()
        date_time = now.strftime("%m_%d_%Y_%H_%M_%S")
        self.result_file_name = path + "/sa_l2m2_" + date_time + ".json"

    def close(self):
        self.driver.close()

    def load_page(self, url):
        self.driver.get(url)
        # Load the entire webage by scrolling to the bottom

        lastHeight = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            # Scroll to bottom of page
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )

            # Wait for new page segment to load
            time.sleep(0.5)

            # Calculate new scroll height and compare with last scroll height
            newHeight = self.driver.execute_script("return document.body.scrollHeight")
            if newHeight == lastHeight:
                break
            lastHeight = newHeight
        page_source = self.driver.page_source
        return page_source

    def getCommunities(self, url):
        dict_comm = {}
        page_source = self.load_page(url)
        l1_soup = BeautifulSoup(page_source, "html.parser")
        all_headers = l1_soup.find_all("h2")
        for h in all_headers:
            hdr = h.text
            hdr = hdr.strip(" –")
            dict_comm[hdr] = {}
            centries = (h.findNext("div")).find_all("div", "content-item community")
            for ce in centries:
                name = (ce.find("h3")).text
                dict_comm[hdr][name] = {}
                footer = ce.find_all("footer")
                fentries = footer[0].find_all("div")
                mem = fentries[0].span.text
                act = fentries[1].span.text
                lang = fentries[2].span.text
                link = (fentries[3].find("a")).attrs["href"]
                dict_comm[hdr][name]["members"] = mem
                dict_comm[hdr][name]["activity"] = act
                dict_comm[hdr][name]["language"] = lang
                dict_comm[hdr][name]["link"] = link
        return dict_comm

    def store_result(self):
        with open(self.result_file_name, "w+") as fp:
            json.dump(
                self.comm_dict["Automobiles"],
                fp,
                skipkeys=False,
                ensure_ascii=True,
                check_circular=True,
                allow_nan=True,
                cls=None,
                indent=4,
                separators=None,
                default=None,
                sort_keys=False,
            )

    def getCategory(self, cattaglist):
        c = {}
        c["category"] = ""
        c["tags"] = []
        if cattaglist is None:
            return c
        for v in cattaglist:
            if "category" in v:
                c["category"] = v.split("category-")[-1]
            if "tag" in v:
                c["tags"].append(v.split("tag-")[-1])
        return c

    # Build out the entire attribute map
    # Topic Title	Category	Tags	Leading Post	Post Replies	Created_at	Replies
    def getTopics(self, url):
        all_topics = []
        print(url)
        page_source = self.load_page(url)
        l2_soup = BeautifulSoup(page_source, "html.parser")
        all_headers = l2_soup.find_all("tr")
        count = 1
        for h in all_headers:
            if count > 2000:
                break
            if count % 20 == 0:
                self.comm_dict["Automobiles"]["Car Talk Community"][
                    "topics"
                ] = all_topics
                self.store_result()
            count += 1
            print(count)
            # Get Category and tags
            c = self.getCategory(h.get("class"))
            topicObj = {}
            topicObj["name"] = ""
            topicObj["category"] = c["category"]
            topicObj["tags"] = c["tags"]
            # get the rest like Title Post replies created
            all_d = h.find_all("td")
            for d in all_d:
                if "main-link" in d["class"]:
                    title = d.find(class_="link-top-line")
                    topicObj["name"] = title.text.strip()
                    topicObj["link"] = url + d.find("a").attrs["href"]
                if "posts" in d["class"]:
                    num_posts = d.find(class_="number")
                    topicObj["num_posts"] = num_posts.text
                if "views" in d["class"]:
                    num_views = d.find(class_="number")
                    nvt = num_views.text.strip()
                    if "k" in list(nvt):
                        nv = nvt.strip("k")
                        nvt = str(int(float(nv) * 1000))
                    topicObj["num_views"] = nvt
                if "age" in d["class"]:
                    post_age = d["title"].strip().split("\n")
                    topicObj["first_post"] = post_age[0].split(": ")[-1]
                    topicObj["last_post"] = post_age[1].split(": ")[-1]
                    datetime_object_f = datetime.strptime(
                        topicObj["first_post"], "%b %d, %Y %I:%M %p"
                    )
                    datetime_object_l = datetime.strptime(
                        topicObj["last_post"], "%b %d, %Y %I:%M %p"
                    )
                    diff = datetime.now() - datetime_object_f
                    topicObj["first_post_age"] = diff.days
                    diff = datetime.now() - datetime_object_l
                    topicObj["last_post_age"] = diff.days
            if topicObj["name"]:
                if topicObj["link"]:
                    topicObj["sentences"] = self.getPosts(topicObj["link"])
                all_topics.append(topicObj)
        return all_topics

    def getPosts(self, url):
        clean = re.compile("<.*?>")
        sentence_list = []
        count_words = Counter()

        page_source = self.load_page(url)
        l3_soup = BeautifulSoup(page_source, "html.parser")
        all_entries = l3_soup.find_all(class_="cooked")
        print(url)
        for e in all_entries:
            part = e.find("p")
            if part:
                sntnc = part.get_text()
                sntnc = sntnc.lower()
                sntnc = re.sub(clean, "", sntnc)
                wrdl = sntnc.split()
                new_l = []
                for w in wrdl:
                    if w.isascii():
                        new_l.append(w)
                sntnc = " ".join(new_l)
                sntnc = self.clean_text(sntnc)
                set_sntnc = set(sentence_list)
                if sntnc not in set_sntnc:
                    sentence_list.append(sntnc)
        return sentence_list

    def clean_text(self, text):
        REPLACE_BY_SPACE_RE = re.compile("[/(){}\[\]'\“\”\’\|@,;]")
        BAD_SYMBOLS_RE = re.compile("[^0-9a-z #+_]")
        STOPWORDS = set(stopwords.words("english"))
        NUM_RE = re.compile(" \d+")

        text = REPLACE_BY_SPACE_RE.sub(
            " ", text
        )  # replace REPLACE_BY_SPACE_RE symbols by space in text
        text = BAD_SYMBOLS_RE.sub(
            "", text
        )  # delete symbols which are in BAD_SYMBOLS_RE from text
        text = " ".join(
            word for word in text.split() if word not in STOPWORDS
        )  # delete stopwors from text
        text = NUM_RE.sub("", text)  # replace numbers with nothing in text
        return text

    def runApp(self, url):
        self.comm_dict = self.getCommunities(url)
        """
            Only looking at one area.
        """

        self.all_topics = self.getTopics(
            self.comm_dict["Automobiles"]["Car Talk Community"]["link"]
        )
        self.comm_dict["Automobiles"]["Car Talk Community"]["topics"] = self.all_topics
        self.store_result()


def Main():
    # url = "https://forums.tapas.io/t/post-the-last-sentence-you-wrote/29878"
    url = "https://www.discoursehub.com/communities/"
    stp = ScrapeThePage()
    stp.runApp(url)


if __name__ == "__main__":
    Main()
