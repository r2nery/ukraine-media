import os
import warnings
import numpy as np
import pandas as pd
from lda import LDA
from alive_progress import alive_bar
from gensim.parsing.preprocessing import remove_stopwords
from sklearn.feature_extraction.text import CountVectorizer

warnings.simplefilter(action="ignore", category=FutureWarning)
warnings.simplefilter(action="ignore", category=RuntimeWarning)

ROOT_DIR = os.path.dirname(os.path.abspath("__file__"))
AP_DIR = os.path.join(ROOT_DIR, "data", "AP.csv")
EXPRESS_DIR = os.path.join(ROOT_DIR, "data", "Express.csv")
FOX_DIR = os.path.join(ROOT_DIR, "data", "Fox.csv")
DAILYMAIL_DIR = os.path.join(ROOT_DIR, "data", "DailyMail.csv")
GUARDIAN_DIR = os.path.join(ROOT_DIR, "data", "Guardian.csv")
HUFFPOST_DIR = os.path.join(ROOT_DIR, "data", "HuffPost.csv")
MIRROR_DIR = os.path.join(ROOT_DIR, "data", "Mirror.csv")
NBC_DIR = os.path.join(ROOT_DIR, "data", "NBC.csv")
REUTERS_DIR = os.path.join(ROOT_DIR, "data", "Reuters.csv")
RT_DIR = os.path.join(ROOT_DIR, "data", "RT.csv")
CNN_DIR = os.path.join(ROOT_DIR, "data", "CNN.csv")

class NTR:
    def __init__(self) -> None:
        self.data_guardian = pd.read_csv(GUARDIAN_DIR)
        self.data_reuters = pd.read_csv(REUTERS_DIR)
        self.data_cnn = pd.read_csv(CNN_DIR)
        self.data_dailymail = pd.read_csv(DAILYMAIL_DIR)
        self.data_ap = pd.read_csv(AP_DIR)
        self.data_fox = pd.read_csv(FOX_DIR)
        pass

    def learn_topics(self, dataframe, topicnum, vocabsize, num_iter):

        # Removes stopwords
        texts = dataframe["Text"].tolist()
        texts_no_sw = []
        for text in texts:
            text_no_sw = remove_stopwords(text)
            texts_no_sw.append(text_no_sw)
        texts = texts_no_sw
        CVzer = CountVectorizer(token_pattern=r"(?u)\b[^\W\d]{2,}\b", max_features=vocabsize, lowercase=True)
        doc_vcnts = CVzer.fit_transform(texts)
        vocabulary = CVzer.get_feature_names_out()
        lda_model = LDA(topicnum, n_iter=num_iter, refresh=100)
        doc_topic = lda_model.fit_transform(doc_vcnts)
        topic_word = lda_model.topic_word_

        return doc_topic, topic_word, vocabulary

    def save_topicmodel(self, doc_topic, topic_word, vocabulary, source):

        topicmixture_outpath = os.path.join(ROOT_DIR, "results", source + "_TopicMixtures.txt")
        np.savetxt(topicmixture_outpath, doc_topic)
        topic_outpath = os.path.join(ROOT_DIR, "results", source + "_Topics.txt")
        np.savetxt(topic_outpath, topic_word)
        vocab_outpath = os.path.join(ROOT_DIR, "results", source + "_Vocab.txt")
        with open(vocab_outpath, mode="w", encoding="utf-8") as f:
            for v in vocabulary:
                f.write(v + "\n")

        return topicmixture_outpath, topic_outpath, vocab_outpath

    def KLdivergence_from_probdist_arrays(self, pdists0, pdists1):

        assert pdists0.shape == pdists1.shape, "pdist* shapes must be identical"
        if len(pdists0.shape) == 1:
            KLdivs = (pdists1 * np.log2(pdists1 / pdists0)).sum()
        elif len(pdists0.shape) == 2:
            KLdivs = (pdists1 * np.log2(pdists1 / pdists0)).sum(axis=1)

        return KLdivs

    def novelty_transience_resonance(self, thetas_arr, scale):

        speechstart = scale
        speechend = thetas_arr.shape[0] - scale
        novelties = []
        transiences = []
        resonances = []
        for j in range(speechstart, speechend, 1):
            center_theta = thetas_arr[j]
            after_boxend = j + scale + 1
            before_boxstart = j - scale
            before_theta_arr = thetas_arr[before_boxstart:j]
            beforenum = before_theta_arr.shape[0]
            before_centertheta_arr = np.tile(center_theta, reps=(beforenum, 1))
            after_theta_arr = thetas_arr[j + 1 : after_boxend]
            afternum = after_theta_arr.shape[0]
            after_centertheta_arr = np.tile(center_theta, reps=(afternum, 1))
            before_KLDs = self.KLdivergence_from_probdist_arrays(before_theta_arr, before_centertheta_arr)
            after_KLDs = self.KLdivergence_from_probdist_arrays(after_theta_arr, after_centertheta_arr)
            novelty = np.mean(before_KLDs)
            transience = np.mean(after_KLDs)
            novelties.append(novelty)
            transiences.append(transience)
            resonances.append(novelty - transience)
        for index in range(0, scale):
            transiences.insert(0, 0)
            transiences.append(0)
            novelties.insert(0, 0)
            novelties.append(0)
            resonances.insert(0, 0)
            resonances.append(0)

        return novelties, transiences, resonances

    def save_novel_trans_reson(self, novelties, transiences, resonances, source):

        outpath = ROOT_DIR + "/results/" + source + "_NovelTransReson.txt"
        np.savetxt(outpath, np.vstack(zip(novelties, transiences, resonances)))

    def routine(self, period, topicnum, vocabsize, num_iter):

        sources = ["Guardian", "Reuters", "CNN", "DailyMail", "AssociatedPress", "Fox"]
        sets = [self.data_guardian, self.data_reuters, self.data_cnn, self.data_dailymail, self.data_ap, self.data_fox]
        for i in range(0, len(sources)):
            data, source = sets[i], sources[i]
            print(f"-> Starting {source} topic modeling (LDA)...")
            doc_topic, topic_word, vocabulary = self.learn_topics(data, topicnum, vocabsize, num_iter)
            topics = []
            for i in range(len(data)):
                topics.append(doc_topic[i].argmax())
            self.save_topicmodel(doc_topic, topic_word, vocabulary, source)
            novelties, transiences, resonances = self.novelty_transience_resonance(doc_topic, period)
            self.save_novel_trans_reson(novelties, transiences, resonances, source)
            ntr_data = data
            ntr_data["Novelty"] = novelties
            ntr_data["Transience"] = novelties
            ntr_data["Resonance"] = resonances
            ntr_data["Topic"] = topics
            ntr_data.to_csv(ROOT_DIR + "/results/" + source + "_Results.csv", index=False)
            print("")

        print("-> All LDA data saved.\n")