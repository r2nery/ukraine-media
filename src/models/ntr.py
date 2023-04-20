import os
import regex as re
import numpy as np
import pandas as pd
from lda import LDA
from gensim.parsing.preprocessing import remove_stopwords
from sklearn.feature_extraction.text import CountVectorizer

ROOT_DIR = os.path.dirname(os.path.abspath("__file__"))
DATA_DIR = os.path.join(ROOT_DIR, "data")


class NTR:
    def __init__(self, kld_days_window) -> None:

        if not os.path.exists(os.path.join(ROOT_DIR, "data", "raw", "All.parquet")):
            print("-> .parquet file not found!")
            print("-> Please run 'python src/scrapers/run_scrapers.py' first.")
            return
        self.data = pd.read_parquet(os.path.join(ROOT_DIR, "data", "raw", "All.parquet"))
        self.scale = kld_days_window

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
        count_vectorizer = CountVectorizer(
            token_pattern=r"(?u)\b[^\W\d]{2,}\b", max_features=vocabsize, lowercase=True
        )
        doc_vcnts = count_vectorizer.fit_transform(texts)
        vocabulary = count_vectorizer.get_feature_names_out()

        # Learn topics.
        lda_model = LDA(topicnum, n_iter=num_iter, refresh=100)
        doc_topic = lda_model.fit_transform(doc_vcnts)
        topic_word = lda_model.topic_word_

        return doc_topic, topic_word, vocabulary

    def save_topicmodel(self, doc_topic, topic_word, vocabulary, source="All"):

        topic_model_dir = os.path.join(DATA_DIR, f"topic_model_n{self.scale}")
        if not os.path.exists(topic_model_dir):
            os.makedirs(topic_model_dir)

        topicmixture_outpath = os.path.join(topic_model_dir, f"{source}_TopicMixtures.txt")
        topic_outpath = os.path.join(topic_model_dir, f"{source}_Topics.txt")
        vocab_outpath = os.path.join(topic_model_dir, f"{source}_Vocab.txt")
        topic_words_outpath = os.path.join(topic_model_dir, f"{source}_TopicWords.txt")
        np.savetxt(topicmixture_outpath, doc_topic)
        np.savetxt(topic_outpath, topic_word)
        with open(vocab_outpath, mode="w", encoding="utf-8") as file:
            for word in vocabulary:
                file.write(word + "\n")

        # geting words of each topic
        words = []
        for i, topic_dist in enumerate(topic_word):
            topic_words = np.array(vocabulary)[np.argsort(topic_dist)][:-21:-1]
            words.append(f"Topic {i}: {' '.join(topic_words)}")
        with open(topic_words_outpath, "w") as file:
            file.write("\n".join(map(str, words)))

        return topicmixture_outpath, topic_outpath, vocab_outpath

    def kld_from_probdists(self, pdists0, pdists1):

        assert pdists0.shape == pdists1.shape, "pdist* shapes must be identical"
        if len(pdists0.shape) == 1:
            kl_divergences = (pdists1 * np.log2(pdists1 / pdists0)).sum()
        elif len(pdists0.shape) == 2:
            kl_divergences = (pdists1 * np.log2(pdists1 / pdists0)).sum(axis=1)

        return kl_divergences

    def calculate_ntr(self, thetas_arr, scale):

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

    def routine(self, topicnum, vocabsize, num_iter):

        data, source = self.data, "All"
        print(f"-> Starting topic modeling (LDA) at scale {self.scale}...")

        doc_topic, topic_word, vocabulary = self.learn_topics(data, topicnum, vocabsize, num_iter)

        # getting topic of each text
        topics = []
        for i in range(len(data)):
            topics.append(doc_topic[i].argmax())

        self.save_topicmodel(doc_topic, topic_word, vocabulary, source)

        novelties, transiences, resonances = self.calculate_ntr(doc_topic, self.scale)
        ntr_data = data
        ntr_data["Novelty"] = novelties
        ntr_data["Transience"] = transiences
        ntr_data["Resonance"] = resonances
        ntr_data["Topic"] = topics

        result_path = os.path.join(DATA_DIR, "processed", f"All_n{self.scale}.csv")
        ntr_data.to_csv(result_path, index=False)

        print("\n-> All LDA and NTR data saved in CSV format.\n")

    def csv_to_parquet(self):
        csv_path = os.path.join(DATA_DIR, "processed", f"All_n{self.scale}.csv")
        parquet_path = os.path.join(DATA_DIR, "processed", f"All_n{self.scale}.parquet")
        print(f"-> Converting CSV to Parquet...")
        pd.read_csv(csv_path).to_parquet(parquet_path, compression="brotli", compression_level=11)
        print("\n-> All LDA and NTR data saved in Parquet format.\n")


if __name__ == "__main__":

    scales = [10]

    for scale in scales:
        NTR(scale).routine(topicnum=200, vocabsize=10000, num_iter=300)
        NTR(scale).csv_to_parquet()
