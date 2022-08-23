import os
import re
import pandas as pd
import numpy as np
from lda import LDA
from gensim.parsing.preprocessing import remove_stopwords
from sklearn.feature_extraction.text import CountVectorizer
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(ROOT_DIR)

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


def save_topicmodel(doc_topic, topic_word, vocabulary, source):

    ## Topic mixtures.
    topicmixture_outpath = PARENT_DIR + "/results/" + source + "TopicMixtures.txt"
    np.savetxt(topicmixture_outpath, doc_topic)

    ## Topics.
    topic_outpath = PARENT_DIR + "/results/" + source + "Topics.txt"
    np.savetxt(topic_outpath, topic_word)

    ## Vocabulary order.
    vocab_outpath = PARENT_DIR + "/results/" + source + "Vocab.txt"
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


def save_novel_trans_reson(novelties, transiences, resonances, source):

    outpath = PARENT_DIR + "/results/" + source + "NovelTransReson.txt"
    np.savetxt(outpath, np.vstack(zip(novelties, transiences, resonances)))


def NTR_Routine(period,topicnum,vocabsize,num_iter):

    sources = ["Guardian", "Reuters"]
    dataG = [] # scrapers output here
    dataR = []
    sets = [dataG, dataR]
    print("")

    for i in range(0,len(sources)):
        data = sets[i]
        source = sources[i]
        data.to_csv(PARENT_DIR + "/data/" + source + ".csv", index=True)
        
        print(f"→ Starting {source} data LDA...")

        doc_topic, topic_word, vocabulary = learn_topics(data, topicnum, vocabsize, num_iter) 

        topics = []
        for i in range(len(data)):
            topics.append(doc_topic[i].argmax())

        save_topicmodel(doc_topic, topic_word, vocabulary, source)

        novelties, transiences, resonances = novelty_transience_resonance(doc_topic, period)

        for index in range(0,period):
            transiences.insert(0, 0)
            transiences.append(0)
            novelties.insert(0, 0)
            novelties.append(0)
            resonances.insert(0, 0)
            resonances.append(0)

        save_novel_trans_reson(novelties, transiences, resonances, source)

        ntr_data = data
        ntr_data['Novelty'] = novelties
        ntr_data['Transience'] = novelties
        ntr_data['Resonance'] = resonances
        ntr_data['Topic'] = topics

        ntr_data.to_csv(PARENT_DIR + "/data/"+ source + "_ntr.csv")

    print("→ All LDA data saved. Ready for plotting")
