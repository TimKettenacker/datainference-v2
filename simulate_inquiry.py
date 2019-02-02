import pandas
from random import randint

job_posts_df = pandas.read_csv("dice_com-job_us_sample.csv")
job_listing_nr = randint(0, len(job_posts_df))
job_inquiry = job_posts_df["jobdescription"][job_listing_nr]
