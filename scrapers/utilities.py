import os
import re
import pandas as pd
import numpy as np
from lda import LDA
from gensim.parsing.preprocessing import remove_stopwords
from sklearn.feature_extraction.text import CountVectorizer

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(ROOT_DIR)


def mkDir():
    os.makedirs(PARENT_DIR + "/data", exist_ok=True)


# Function that checks if a file exists
def fileExists(FILE):
    return os.path.exists(PARENT_DIR + "/data/" + FILE)


# Function that returns a file
def getFile(FILE):
    return pd.read_csv(PARENT_DIR + "/data/" + FILE)


# Function that checks latest data parsed, if any. If none, defaults to 20220201
def getDate(FILE):
    if FILE == "NYT.csv":
        if fileExists(FILE):
            check = pd.read_csv(PARENT_DIR + "/data/" + FILE)
            return re.match(r"^[^T]*", check.iloc[-1, 1]).group(0).replace("-", "")
        else:
            return "20220201"
    if FILE == "Guardian.csv":
        if fileExists(FILE):
            check = pd.read_csv(PARENT_DIR + "/data/" + FILE)
            return re.match(r"^[^T]*", check.iloc[-1, 1]).group(0)
        else:
            return "2022-02-01"


# Function that returns length of existing dataset
def getLen(FILE):
    if fileExists(FILE):
        check = pd.read_csv(PARENT_DIR + "/data/" + FILE)
        return len(check)
    else:
        return 0


# Function that returns the number of articles in the current API query page
def numArticlesInPage(json, FILE):
    if FILE == "Guardian.csv":
        if json["response"]["total"] - json["response"]["startIndex"] >= 200:
            return 200
        else:
            return json["response"]["total"] - json["response"]["startIndex"] + 1
    elif FILE == "NYT.csv":
        if json["response"]["meta"]["hits"] - json["response"]["meta"]["offset"] >= 10:
            return 10
        else:
            return json["response"]["meta"]["hits"] - json["response"]["meta"]["offset"]


# Function that clears text of a dict of substrings
def replaceAll(text, dic):
    for i, j in dic.items():
        text = text.replace(i, j)
    return text


# Saving function
def save(dataF, FILE):
    if fileExists(FILE):
        existingData = pd.read_csv(PARENT_DIR + "/data/" + FILE)
        data = pd.concat([existingData, dataF])
        data = data.drop_duplicates(keep="first")
        data.to_csv(PARENT_DIR + "/data/" + FILE, index=False)
        return data
    else:
        dataF.to_csv(PARENT_DIR + "/data/" + FILE, index=False)
        return dataF


####### LDA


def learn_topics(dataframe, topicnum, vocabsize, num_iter):

    # Removes stopwords
    texts = dataframe["Text"].tolist()
    texts_no_sw = []
    for text in texts:
        text_no_sw = remove_stopwords(text)
        texts_no_sw.append(text_no_sw)
    texts = texts_no_sw

    # Get vocabulary and word counts.  Use the top 10,000 most frequent
    # lowercase unigrams with at least 2 alphabetical, non-numeric characters,
    # punctuation treated as separators.
    CVzer = CountVectorizer(token_pattern=r"(?u)\b[^\W\d]{2,}\b", max_features=vocabsize, lowercase=True)
    doc_vcnts = CVzer.fit_transform(texts)
    vocabulary = CVzer.get_feature_names_out()

    # Learn topics.  Refresh conrols print frequency.
    lda_model = LDA(topicnum, n_iter=num_iter, refresh=100)
    doc_topic = lda_model.fit_transform(doc_vcnts)
    topic_word = lda_model.topic_word_

    return doc_topic, topic_word, vocabulary


def save_topicmodel(doc_topic, topic_word, vocabulary):

    ## Topic mixtures.
    topicmixture_outpath = PARENT_DIR + "/results/GuardianTopicMixtures.txt"
    np.savetxt(topicmixture_outpath, doc_topic)

    ## Topics.
    topic_outpath = PARENT_DIR + "/results/GuardianTopics.txt"
    np.savetxt(topic_outpath, topic_word)

    ## Vocabulary order.
    vocab_outpath = PARENT_DIR + "/results/GuardianVocab.txt"
    with open(vocab_outpath, mode="w", encoding="utf-8") as f:
        for v in vocabulary:
            f.write(v + "\n")

    return topicmixture_outpath, topic_outpath, vocab_outpath


def KLdivergence_from_probdist_arrays(pdists0, pdists1):
    """
    Calculate KL divergence between probability distributions held on the same
    rows of two arrays.

    NOTE: elements of pdist* are assumed to be positive (non-zero), a
    necessary condition for using Kullback-Leibler Divergence.

    Args:
      pdists* (numpy.ndarray): arrays, where rows for each constitute the two
      probability distributions from which to calculate divergence.  pdists1
      contains the distributions holding probabilities in the numerator of the
      KL divergence summand.

    Returns:
      numpy.ndarray: KL divergences, where the second array's rows are the
        distributions in the numerator of the log in KL divergence

    """

    assert pdists0.shape == pdists1.shape, "pdist* shapes must be identical"

    if len(pdists0.shape) == 1:
        KLdivs = (pdists1 * np.log2(pdists1 / pdists0)).sum()
    elif len(pdists0.shape) == 2:
        KLdivs = (pdists1 * np.log2(pdists1 / pdists0)).sum(axis=1)

    return KLdivs


def novelty_transience_resonance(thetas_arr, scale):
    """
    Calculate novelty, transience, and resonance for all center speeches with
    at least one scale of speeches in its past and its future.  Presidential
    speeches are excluded from the surrounding scales.

    Args:
      thetas_arr (numpy.ndarray): rows are topic mixtures
      scale (int): positive integer defining scale or scale size

    """

    # Find the first and last center speech offset, given scale size.
    speechstart = scale
    speechend = thetas_arr.shape[0] - scale

    # Calculate novelty, transience, resonance.
    novelties = []
    transiences = []
    resonances = []
    for j in range(speechstart, speechend, 1):

        center_theta = thetas_arr[j]

        # Define windows before and after center speech.
        after_boxend = j + scale + 1
        before_boxstart = j - scale

        before_theta_arr = thetas_arr[before_boxstart:j]
        beforenum = before_theta_arr.shape[0]
        before_centertheta_arr = np.tile(center_theta, reps=(beforenum, 1))

        after_theta_arr = thetas_arr[j + 1 : after_boxend]
        afternum = after_theta_arr.shape[0]
        after_centertheta_arr = np.tile(center_theta, reps=(afternum, 1))

        # Calculate KLDs.
        before_KLDs = KLdivergence_from_probdist_arrays(before_theta_arr, before_centertheta_arr)
        after_KLDs = KLdivergence_from_probdist_arrays(after_theta_arr, after_centertheta_arr)

        # Calculate means of KLD.
        novelty = np.mean(before_KLDs)
        transience = np.mean(after_KLDs)

        # Final measures for this center speech.
        novelties.append(novelty)
        transiences.append(transience)
        resonances.append(novelty - transience)

    return novelties, transiences, resonances


def save_novel_trans_reson(novelties, transiences, resonances):

    outpath = PARENT_DIR + "/results/GuardianNovelTransReson.txt"
    np.savetxt(outpath, np.vstack(zip(novelties, transiences, resonances)))
