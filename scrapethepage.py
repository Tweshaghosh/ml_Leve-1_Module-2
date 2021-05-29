#!/usr/local/bin/python3


import time
from datetime import datetime
import os
from bs4 import BeautifulSoup
from selenium import webdriver
import pandas as pd
import json
from collections import Counter

# from nltk.corpus import stopwords


from selenium.webdriver.remote.utils import dump_json


class ScrapeThePage:
    def __init__(self):
        path = os.getcwd()
        print(path)
        webDriverWithPath = path + "/chromedriver"
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument(
            "--ignore-certificate-errors"
        )  # Ignore security certificates
        chrome_options.add_argument("--incognito")  # Use Chrome in Incognito mode
        chrome_options.add_argument("--headless")  # Run in background
        self.driver = webdriver.Chrome(
            executable_path=webDriverWithPath,
            options=chrome_options,
        )
        now = datetime.now()
        date_time = now.strftime("%m_%d_%Y_%H_%M_%S")
        self.result_file_name = path + "/sa_l2m2_" + date_time + ".json"
        st_list = [
            "i",
            "me",
            "my",
            "myself",
            "we",
            "our",
            "ours",
            "ourselves",
            "you",
            "you're",
        ]
        # self.stop = set(stopwords.words("english"))
        self.stop = set(st_list)

    def close(self):
        self.driver.close()

    def load_page(self, url):
        self.driver.get(url)
        # Load the entire webage by scrolling to the bottom
        lastHeight = self.driver.execute_script("return document.body.scrollHeight")
        while False:
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

    def getTopics(self, url):
        all_topics = []
        print(url)
        page_source = self.load_page(url)
        l2_soup = BeautifulSoup(page_source, "html.parser")
        all_headers = l2_soup.find_all("tr")
        for h in all_headers:
            all_d = h.find_all("td")
            c = self.getCategory(h.get("class"))
            for d in all_d:
                topic = d.find(class_="link-top-line").text
                topicObj = {}
                topicObj["name"] = topic.strip()
                topicObj["link"] = url + d.find("a").attrs["href"]
                topicObj["category"] = c["category"]
                topicObj["tags"] = c["tags"]
                (topicObj["sentences"], topicObj["count_words"]) = self.getPosts(
                    topicObj["link"]
                )
                all_topics.append(topicObj)
                break
        return all_topics

    def getPosts(self, url):
        sentence_list = []
        count_words = Counter()

        page_source = self.load_page(url)
        l3_soup = BeautifulSoup(page_source, "html.parser")
        all_entries = l3_soup.find_all(class_="cooked")
        print(url)
        for e in all_entries:
            part = e.find("p")
            if part:
                print("-----")
                print(e)
                print(part)
                sntnc = part.get_text()
                sntnc = sntnc.lower()
                sentence_list.append(sntnc)
                all_words = sntnc.split(" ")
                s_aw = set(all_words)
                all_words = list(s_aw - self.stop)
                count_words.update(all_words)
        return (sentence_list, count_words)

    def runApp(self, url):
        comm_dict = self.getCommunities(url)
        """
            Only looking at one area.
        """

        all_topics = self.getTopics(
            comm_dict["Automobiles"]["Car Talk Community"]["link"]
        )
        comm_dict["Automobiles"]["Car Talk Community"]["topics"] = all_topics
        with open(self.result_file_name, "w+") as fp:
            json.dump(
                comm_dict,
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


def Main():
    # url = "https://forums.tapas.io/t/post-the-last-sentence-you-wrote/29878"
    url = "https://www.discoursehub.com/communities/"
    stp = ScrapeThePage()
    stp.runApp(url)


if __name__ == "__main__":
    Main()
