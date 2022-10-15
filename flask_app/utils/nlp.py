import numpy as np
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize


def process_text(text):
    """
    Returns list of stems of non-stopwords.
    """

    word_list = word_tokenize(str(text))

    filtered_words = [
        word for word in word_list if word not in stopwords.words("english")
    ]

    ps = PorterStemmer()
    return [ps.stem(word) for word in filtered_words]


def vectorize_processed_text(processed_text, id_to_word):
    """
    Returns vectors of processed text, using id_to_word.
    """

    dict_id_to_count = {i: 0 for i in range(len(id_to_word))}

    hits = id_to_word.doc2bow(processed_text)
    for hit in hits:
        dict_id_to_count[hit[0]] = hit[1]

    return np.array([v for v in dict_id_to_count.values()])
