import pandas
from random import randint

job_posts_df = pandas.read_csv("dice_com-job_us_sample.csv")
job_listing_nr = randint(0, len(job_posts_df))
job_inquiry = job_posts_df["jobdescription"][job_listing_nr]

job_clean = clean(job_inquiry.decode( 'unicode-escape' )).split()
col = len(job_clean)
row = 1
job_clean = [job_clean[col * i: col * (i + 1)] for i in range(row)]

bigram = Phrases(job_clean, min_count=1, threshold=2)
bigram_mod = gensim.models.phrases.Phraser(bigram)
job_inquiry_bigrams = make_bigrams(job_clean)

id2word = corpora.Dictionary(job_inquiry_bigrams)
corpus = [id2word.doc2bow(text) for text in job_inquiry_bigrams]
lda_model = gensim.models.ldamodel.LdaModel(corpus=corpus,
                                           id2word=id2word,
                                           num_topics=4,
                                           update_every=1,
                                           chunksize=100,
                                           passes=1,
                                           alpha='auto')

job_topics = str(lda_model.print_topics())