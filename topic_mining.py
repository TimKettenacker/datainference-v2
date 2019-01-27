import string
import nltk
nltk.download('stopwords')
nltk.download('wordnet')
from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer
import gensim
from gensim import corpora
from gensim.models import Phrases


def clean(doc):
    stop_free = " ".join([i for i in doc.lower().split() if i not in stop])
    punc_free = ''.join(ch for ch in stop_free if ch not in exclude)
    normalized = " ".join(lemma.lemmatize(word) for word in punc_free.split())
    return normalized


def make_bigrams(texts):
    return [bigram_mod[doc] for doc in texts]


stop = set(stopwords.words(['english', 'german']))
exclude = set(string.punctuation)
lemma = WordNetLemmatizer()

for z in range(len(slides_df)):
    # conduct preprocessing and split into tokens
    content_clean = clean(slides_df.iloc[z,0]).split()
    content_clean = [x for x in content_clean if x not in ['responsible', 'role', 'industry', 'rolle', 'branche', 'industrie', 'aufgaben', 'verantwortlich']]
    col = len(content_clean)
    row = 1
    content_clean = [content_clean[col*i : col*(i+1)] for i in range(row)]

    # reflect significance of combined words like 'data science' by creating bigrams
    bigram = Phrases(content_clean, min_count = 1, threshold = 2)
    bigram_mod = gensim.models.phrases.Phraser(bigram)
    data_words_bigrams = make_bigrams(content_clean)

    # feed bigrams to LDA model
    id2word = corpora.Dictionary(data_words_bigrams)
    corpus = [id2word.doc2bow(text) for text in data_words_bigrams]
    lda_model = gensim.models.ldamodel.LdaModel(corpus=corpus,
                                               id2word=id2word,
                                               num_topics=4,
                                               update_every=1,
                                               chunksize=100,
                                               passes=1,
                                               alpha='auto')
    slides_df.loc[z].at['raw topics'] = str(lda_model.print_topics())