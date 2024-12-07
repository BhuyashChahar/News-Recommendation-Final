import pandas as pd
import numpy as np
np.random.seed(30)
from scipy import stats
import datetime as dt



def modify(corpus_df):
    corpus_df['Mean_Time']= 0
    artind=[]
    corpus_df['article_idx']= " "
    for i in corpus_df.index:
        corpus_df['Mean_Time'][i]= float(len(corpus_df['Summary'][i])/4)
        artind.append(str(corpus_df['Category'][i][:2])+'_'+str(i))
    corpus_df['article_idx']=artind
    (unique, counts) = np.unique(corpus_df['Category'], return_counts=True)
    if len(unique)>10:
        order=sorted(list(counts),reverse=True)
        merge=order[10:]
        for i in range(len(merge)):
            for j in range(len(counts)):
                if merge[i]==counts[j]:
                    corpus_df['Category']=corpus_df['Category'].replace([unique[j]],'Miscellaneous')
    return corpus_df


def bot1baseScoring(dt_corpus_df, user_rating_df):
    time_resol_set = 3600
    dt_wt = -0.5/time_resol_set
    rat_wt = 1.2
    avg_art_rat = user_rating_df[dt_corpus_df.index].sum(axis = 0)
    time_now = dt.datetime(2021, 3, 18).timestamp() # Temporarily
    # time_now = dt.datetime.now().timestamp()        Actually (Permanently)
    if type(dt_corpus_df) == pd.core.series.Series:
        dt_series = pd.Series([time_now]*len(dt_corpus_df), index = dt_corpus_df.index, name = "Time_Now") - pd.to_datetime(dt_corpus_df).apply(dt.datetime.timestamp)
    else:
        dt_series = pd.Series([time_now]*len(dt_corpus_df), index = dt_corpus_df.index, name = "Time_Now") - pd.to_datetime(dt_corpus_df.Datetime).apply(dt.datetime.timestamp)
    score_df = dt_wt*dt_series + rat_wt*avg_art_rat
    max_idx_list = list()
    max_score_list = list()
    for clu_id, clu_df in score_df.groupby(level = "clu_idx"):
        max_idx = clu_df.idxmax()
        max_idx_list.append(max_idx)
        max_score_list.append(clu_df[max_idx])
    new_user_base_recomm = pd.Series(max_score_list, index = max_idx_list, name = "Max_Scores", dtype = "float64").sort_values(ascending=False)
    return new_user_base_recomm.index


def bot1_recommendation(corpus_df):
    
    reform_corpus_df = modify(corpus_df)

    cluster_idx_dict = {1: "Entertainment", 2: "Sports", 3: "Technology", 4: "Business", 5: "World", 6: "India",
                    7: "Society", 8: "Education", 9: "Lifestyle", 10: "Miscellaneous"}

    reform_corpus_df = pd.DataFrame(columns = corpus_df.columns)
    frames = list()

    for i in range(1, 11):
        clu = cluster_idx_dict[i]
        print(clu)
        frames.append(corpus_df[corpus_df["Category"] == clu].sort_values(by = "Datetime", ignore_index = True))
    reform_corpus_df = pd.concat(frames, keys = [i for i in range(1, 11)], names = ["clu_idx", "art_idx"])

    trial_user_rating_df = pd.DataFrame([[np.random.randint(-1, 2) for i in range(len(reform_corpus_df))] for user in range(50)], columns = reform_corpus_df.index)

    return reform_corpus_df.loc[bot1baseScoring(reform_corpus_df, trial_user_rating_df)].to_dict("records")