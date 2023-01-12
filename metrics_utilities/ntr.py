import os
import regex as re
import numpy as np
import pandas as pd
from lda import LDA
from gensim.parsing.preprocessing import remove_stopwords
from sklearn.feature_extraction.text import CountVectorizer

ROOT_DIR = os.path.dirname(os.path.abspath("__file__"))

class NTR:
    def __init__(self) -> None:
        self.sources = [
            "AP",
            "Fox",
            "CNN",
            "ABC",
            "CBS",
            "NYT",
            "Mirror",
            "Reuters",
            "Express",
            "Guardian",
            "DailyMail",
            "All",
        ]
        self.data = [pd.read_csv(os.path.join(ROOT_DIR, "data", i + ".csv")) for i in self.sources]
        self.scale = 0

    def kld_window(self, dataframe, date_start, date_end, kld_days_window):
        data = dataframe
        data["Date"] = pd.to_datetime(data["Date"])
        df_split = data.loc[(data["Date"] >= date_start) & (data["Date"] < date_end)]
        df_count = df_split.resample("D", on="Date").apply({"URL": "count"})
        daily_count = int(sum(df_count["URL"].tolist()) / len(df_count["URL"].tolist()))
        print(f"-> This dataset has an average of {daily_count} daily stories from {date_start} to {date_end}.")
        print(f"-> KLD window will be of {kld_days_window}*{daily_count} = {kld_days_window*daily_count} articles.\n")
        return kld_days_window * daily_count

    def learn_topics(self, dataframe, topicnum, vocabsize, num_iter):
        # Removes stopwords
        texts = dataframe["Text"].tolist()
        texts_no_sw = []
        for text in texts:
            text_no_sw = remove_stopwords(text)
            texts_no_sw.append(text_no_sw)

        # Get vocab and word counts. Use the top 10k most frequent
        # lowercase unigrams with at least 2 alphabetical, non-numeric characters,
        # punctuation treated as separators.
        texts = texts_no_sw
        count_vectorizer = CountVectorizer(token_pattern=r"(?u)\b[^\W\d]{2,}\b", max_features=vocabsize, lowercase=True)
        doc_vcnts = count_vectorizer.fit_transform(texts)
        vocabulary = count_vectorizer.get_feature_names_out()

        # Learn topics.
        lda_model = LDA(topicnum, n_iter=num_iter, refresh=100)
        doc_topic = lda_model.fit_transform(doc_vcnts)
        topic_word = lda_model.topic_word_

        return doc_topic, topic_word, vocabulary

    def save_topicmodel(self, doc_topic, topic_word, vocabulary, source):

        if not os.path.exists(os.path.join(ROOT_DIR, f"results_{self.scale}")):
            os.makedirs((os.path.join(ROOT_DIR, f"results_{self.scale}")))

        topicmixture_outpath = os.path.join(ROOT_DIR, f"results_{self.scale}", source + "_TopicMixtures.txt")
        np.savetxt(topicmixture_outpath, doc_topic)
        topic_outpath = os.path.join(ROOT_DIR, f"results_{self.scale}", source + "_Topics.txt")
        np.savetxt(topic_outpath, topic_word)
        vocab_outpath = os.path.join(ROOT_DIR, f"results_{self.scale}", source + "_Vocab.txt")
        with open(vocab_outpath, mode="w", encoding="utf-8") as file:
            for word in vocabulary:
                file.write(word + "\n")

        return topicmixture_outpath, topic_outpath, vocab_outpath

    def kld_from_probdists(self, pdists0, pdists1):

        assert pdists0.shape == pdists1.shape, "pdist* shapes must be identical"
        if len(pdists0.shape) == 1:
            kl_divergences = (pdists1 * np.log2(pdists1 / pdists0)).sum()
        elif len(pdists0.shape) == 2:
            kl_divergences = (pdists1 * np.log2(pdists1 / pdists0)).sum(axis=1)

        return kl_divergences

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
            before_klds = self.kld_from_probdists(before_theta_arr, before_centertheta_arr)
            after_klds = self.kld_from_probdists(after_theta_arr, after_centertheta_arr)
            novelty = np.mean(before_klds)
            transience = np.mean(after_klds)
            novelties.append(novelty)
            transiences.append(transience)
            resonances.append(novelty - transience)
        for _ in range(0, scale):
            transiences.insert(0, 0)
            transiences.append(0)
            novelties.insert(0, 0)
            novelties.append(0)
            resonances.insert(0, 0)
            resonances.append(0)

        return novelties, transiences, resonances

    def lda_only(self,topicnum, vocabsize, num_iter):
        for i, source in enumerate(self.sources):
            data, source = self.data[i], self.sources[i]
            print(f"-> Starting {source} topic modeling (LDA)...")

            doc_topic, topic_word, vocabulary = self.learn_topics(data, topicnum, vocabsize, num_iter)

            # getting topic of each text
            topics = []
            for i in range(len(data)):
                topics.append(doc_topic[i].argmax())

            # self.save_topicmodel(doc_topic, topic_word, vocabulary, source)
            data["Topic"] = topics
            data.to_csv(os.path.join(ROOT_DIR, "results_0", source + "_Results.csv"), index=False)

            # geting words of each topic
            words = []
            for i, topic_dist in enumerate(topic_word):
                topic_words = np.array(vocabulary)[np.argsort(topic_dist)][:-21:-1]
                words.append(f"Topic {i}: {' '.join(topic_words)}")
            with open(os.path.join(ROOT_DIR, "results_0", source + "_TopicsWords.txt"), "w") as file:
                file.write("\n".join(map(str, words)))

            print("")

        print("-> All LDA data saved.\n")

    def routine(self, date_start, date_end, kld_days_window, topicnum, vocabsize, num_iter):

        for i, source in enumerate(self.sources):
            data, source = self.data[i], self.sources[i]
            self.scale = kld_days_window
            scale = self.kld_window(data, date_start, date_end, kld_days_window)
            print(f"-> Starting {source} topic modeling (LDA)...")

            doc_topic, topic_word, vocabulary = self.learn_topics(data, topicnum, vocabsize, num_iter)

            # getting topic of each text
            topics = []
            for i in range(len(data)):
                topics.append(doc_topic[i].argmax())

            # self.save_topicmodel(doc_topic, topic_word, vocabulary, source)
            novelties, transiences, resonances = self.novelty_transience_resonance(doc_topic, scale)
            ntr_data = data
            ntr_data["Novelty"] = novelties
            ntr_data["Transience"] = transiences
            ntr_data["Resonance"] = resonances
            ntr_data["Topic"] = topics

            path = os.path.join(ROOT_DIR, f"results_{self.scale}")
            if not os.path.exists(path):
                os.makedirs(path)
            ntr_data.to_csv(os.path.join(path, source + "_Results.csv"), index=False)

            # geting words of each topic
            words = []
            for i, topic_dist in enumerate(topic_word):
                topic_words = np.array(vocabulary)[np.argsort(topic_dist)][:-21:-1]
                words.append(f"Topic {i}: {' '.join(topic_words)}")
            

            with open(os.path.join(path, source + "_TopicsWords.txt"), "w") as file:
                file.write("\n".join(map(str, words)))

            print("")

        print("-> All LDA and NTR data saved.\n")
