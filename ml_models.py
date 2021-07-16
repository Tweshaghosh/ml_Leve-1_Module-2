#!/usr/local/bin/python3


import time
from datetime import datetime
import os
from selenium import webdriver
import pandas as pd
import json
from collections import Counter
import re
import nltk
from nltk.corpus import stopwords

import seaborn as sns
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import logging
import numpy as np
from numpy import random
import gensim
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.metrics.pairwise import cosine_similarity
from rake_nltk import Rake


class mlModels:
    def __init__(self, fname):
        with open(fname, "r+") as fp:
            self.data = json.load(fp)

    def createDF(self):
        # Convert it into Panda Dataframe
        df_dict = {}
        for topic in self.data["Car Talk Community"]["topics"]:
            for k, v in topic.items():
                # if "sentences" in k:
                #     continue
                if k not in df_dict:
                    df_dict[k] = []
                df_dict[k].append(v)
        self.df = pd.DataFrame(df_dict)
        self.df["bag_of_words"] = ""
        print(self.df.info())
        self.r = Rake()

    def cleanData(self):
        return

    def word_count(self):
        self.df["word_count"] = self.df["sentences"].apply(
            lambda x: len((" ".join(x)).split(" "))
        )
        self.df[["name", "word_count"]].head()

    def stop_words(self):
        stop = stopwords.words("english")
        self.df["stop_words"] = self.df["sentences"].apply(
            lambda x: len([j for j in ((" ".join(x)).split(" ")) if j in stop])
        )
        # print(self.df[["name", "stop_words"]].head())

    def plot_word_cloud(self, text):
        wordcloud_instance = WordCloud(
            width=800,
            height=800,
            background_color="black",
            stopwords=None,
            min_font_size=10,
        ).generate(text)

        plt.figure(figsize=(8, 8), facecolor=None)
        plt.imshow(wordcloud_instance)
        plt.axis("off")
        plt.tight_layout(pad=0)
        plt.show()

    def plot_word_cloud_for_category(self, category):
        text_df = self.df.loc[self.df["category"] == str(category)]
        # print(text_df.head())
        texts = ""
        for index, item in text_df.iterrows():
            # print(item["sentences"])
            texts = texts + " " + " ".join(item["sentences"])
        self.plot_word_cloud(texts)

    def getrakeyw(self, lw):
        self.r.extract_keywords_from_text(lw)
        key_words_dict_scores = self.r.get_word_degrees()
        abc = list(key_words_dict_scores.keys())
        return abc

    def create_key_words(self):
        self.df["key_words_posts"] = self.df.apply(
            lambda row: self.getrakeyw(" ".join(row["sentences"]) + row["name"]), axis=1
        )

    def create_bag_of_words(self):
        self.df["bag_of_words"] = self.df.apply(
            lambda row: " "
            + row["category"]
            + " "
            + " ".join(row["tags"])
            + " "
            + " ".join(row["key_words_posts"])
            + " ",
            axis=1,
        )
        print(self.df.info)

    def similarity(self):
        count = CountVectorizer()
        count_matrix = count.fit_transform(self.df["bag_of_words"])
        self.cosine_sim = cosine_similarity(count_matrix, count_matrix)
        print(self.cosine_sim)

    def recommend(self, name):
        indices = pd.Series(self.df["name"])
        recommended_post = []
        idx = indices[indices == name].index[0]
        score_series = pd.Series(self.cosine_sim[idx]).sort_values(ascending=False)
        top_10_indices = list(score_series.iloc[1:11].index)

        for i in top_10_indices:
            abc = list(self.df["name"])[i]
            recommended_post.append(abc)
        return recommended_post


def Main():
    fname = "sa_l2m2_6298.json"
    mlm = mlModels(fname)
    mlm.createDF()
    print("created Dataframe")
    # print(mlm.df[["name", "tags"]].head())
    mlm.word_count()
    print("Completed Word Count")
    """ Stopwords filtering is not needed because
        it has aready been done when preparing and cleaning the data
    """
    # mlm.stop_words()
    mlm.create_key_words()
    print("Completed Key Words")
    mlm.create_bag_of_words()
    print("Completed Bag of Words")
    mlm.similarity()
    print("Computed Similarity")
    print("Topic - " + "Clutch Cylinder Question")
    print("Suggested topics:")
    print(mlm.recommend("Clutch Cylinder Question"))
    print("Topic - " + "Volvo s40 2005 power failure")
    print("Suggested topics:")
    print(mlm.recommend("Volvo s40 2005 power failure"))
    print("Topic - " + "Python alarm system")
    print("Suggested topics:")
    print(mlm.recommend("Python alarm system"))
    # set_cat = set(mlm.df["category"])
    # for c in list(set_cat):
    #     print(c)
    #     mlm.plot_word_cloud_for_category(c)
    # # print(mlm.df)
    print("Complete")


if __name__ == "__main__":
    Main()
