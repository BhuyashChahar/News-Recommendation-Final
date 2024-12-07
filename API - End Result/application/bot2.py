import datetime
import numpy as np
import pandas as pd
import random
import re
from datasketch import MinHash, MinHashLSHForest
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.metrics import pairwise_distances
from sklearn.metrics.pairwise import cosine_similarity

np.random.seed(30)

class corpus_process():
    def __init__(self,df):
        self.df=df

    def modify(self,df):
        self.df['Mean_Time']=" "
        artind=[]
        self.df['Article_ID']=" "
        for i in range(len(self.df['Entire_News'])):
            self.df['Mean_Time'][i]= int(len(self.df['Summary'][i])/4)
            artind.append(str(self.df['Category'][i][0:2])+'_'+str(i))
        self.df['Article_ID']=artind
        (unique, counts) = np.unique(self.df['Category'], return_counts=True)
        if len(unique)>10:
            order=sorted(list(counts),reverse=True)
            merge=order[10:]
            for i in range(len(merge)):
                for j in range(len(counts)):
                    if merge[i]==counts[j]:
                        self.df['Category']=self.df['Category'].replace([unique[j]],'Miscellaneous')
        return self.df
    
    def preprocess(self,df):
        self.df= self.modify(self.df)
        return self.df


class content_based_models():
    def __init__(self,df,corpus,LSH_models,Bow_models):
        self.df=df
        self.corpus=corpus
        self.LSH_models=LSH_models
        self.Bow_models=Bow_models
        
    def corpus_dict(self,df,corpus):
        keys=list(self.corpus.keys())
        unique=np.unique(df['Category'])
        misc=list(np.setdiff1d(unique,keys))
        self.df['Category'] = self.df['Category'].replace(misc,'Miscellaneous')
        for i in range(len(keys)):
            ele=self.df[self.df['Category']==keys[i]]
            ele=ele.reset_index(drop=True)
            self.corpus[keys[i]].append(ele)
        return corpus
            
        
    def preprocess(self,text):
        text = re.sub(r'[^\w\s]','',text)
        tokens = text.lower()
        tokens = tokens.split()
        return tokens
    
    def get_forest(self,data, perms):
        minhash = []
        for text in data['text']:
            tokens = self.preprocess(text)
            m = MinHash(num_perm=perms)
            for s in tokens:
                m.update(s.encode('utf8'))
            minhash.append(m)
        forest = MinHashLSHForest(num_perm=perms)
    
        for i,m in enumerate(minhash):
            forest.add(i,m)
        
        forest.index()
        return forest
    
    def predict(self,text, database, perms, num_results, forest):
        num_results+=1
        tokens = self.preprocess(text)
        m = MinHash(num_perm=perms)
        for s in tokens:
            m.update(s.encode('utf8'))
        
        idx_array = np.array(forest.query(m, num_results))
        if len(idx_array) == 0:
            return None # if your query is empty, return none
    
        result = database.iloc[idx_array]['Article_ID']
        return result
    
    def LSH_model(self,df,corpus,LSH_models):
        keys=list(self.corpus.keys())
        permutations=128
        for i in range(len(keys)):
            db=list(corpus[keys[i]])[-1]
            db['text'] = db['Headline'] + ' ' + db['Entire_News']
            forest = self.get_forest(db, permutations)
            LSH_models[keys[i]].append(forest)
        return LSH_models
    
    def Bow_model(self,df,corpus,Bow_models):
        keys=list(self.corpus.keys())
        news_vectorizer = HashingVectorizer()
        for i in range(len(keys)):
            news_features = news_vectorizer.fit_transform(list(corpus[keys[i]])[-1]['Entire_News'])
            Bow_models[keys[i]].append(news_features)
        return Bow_models
            
    def dicts(self,df,corpus,LSH_models,Bow_models):
        self.corpus= self.corpus_dict(self.df,self.corpus)
        self.LSH_models=self.LSH_model(self.df,self.corpus,self.LSH_models)
        self.Bow_models=self.Bow_model(self.df,self.corpus,self.Bow_models)
        return self.corpus,self.LSH_models,self.Bow_models


class user_rating():
    def __init__(self,user_rating_df,df):
        self.df=df
        self.user_rating_df=user_rating_df
    
    def cross_link(self,df,user_rating_df):
        column={}
        col=[col for col in self.user_rating_df.columns[:-1]]
        for i in (col):
            key=i
            ele=str(self.df['Category'][i][0:2])+'_'+str(i)
            column[key]=ele
        
        user_rating_df=user_rating_df.rename(columns=column)
        
        return user_rating_df
    
    def column_add(self,user_rating_df):
        u_id=[]
        for i in range(len(self.user_rating_df.index)):
            ele=i
            u_id.append(ele)
        self.user_rating_df['User_ID']=u_id
        return self.user_rating_df
        
        
    def frame(self,user_rating_df,df):
        self.user_rating_df=self.cross_link(self.df,self.user_rating_df)
        df=self.column_add(self.user_rating_df)
        return df

class content_based_recommendations():
    def __init__(self,article_id,num_recommendations,corpus):
        self.article_id=article_id
        self.num_recommendations=num_recommendations
        self.corpus=corpus
        
    def LSH_recommendation(self,article_id,num_recommendations,corpus):
        reco=[]
        keys=list(self.corpus.keys())
        for i in range(len(keys)):
            if self.article_id[0:2]==keys[i][0:2]:
                new_pd=pd.concat(list(self.corpus[keys[i]]), ignore_index=True)
                title = new_pd['Entire_News'][int(self.article_id[3:])]
                db= new_pd
                permutations=128
                db=new_pd
                db['text'] = db['Headline'] + ' ' + db['Entire_News']
                forest=con_mod.get_forest(db, permutations)
                result = con_mod.predict(title, db, permutations, self.num_recommendations, forest)
                articles= list(result)
                articles=articles[0:self.num_recommendations+1]
        for i in range(len(articles)):
            if articles[i]!=self.article_id:
                reco.append(articles[i])
            if len(reco)== self.num_recommendations:
                break
        return reco
        
    def Bow_recommendation(self,article_id,num_recommendations,corpus):
        keys=list(self.corpus.keys())
        for i in range(len(keys)):
            if self.article_id[0:2]==keys[i][0:2]:
                new_pd=pd.concat(self.corpus[keys[i]], ignore_index=True)
                row_index= new_pd.index[new_pd['Article_ID']==article_id]
        news_vectorizer = HashingVectorizer()
        news_features = news_vectorizer.fit_transform(new_pd['Entire_News'])
        couple_dist = pairwise_distances(news_features,news_features[row_index])
        indices = np.argsort(couple_dist.ravel())#[1:self.num_recommendations]
        indices=list(indices)
        reco=[]
        for i in range(len(indices)):
            if new_pd['Article_ID'][indices[i]]==self.article_id:
                indices.remove(indices[i])
                break
        for i in range(len(indices)):
            try:                    
                reco.append(new_pd['Article_ID'][indices[i]])
                if len(reco)==self.num_recommendations:
                    break
            except:
                continue
        return reco
    
    def recommendations(self,article_id,num_recommendations,corpus):
        #reco1=self.LSH_recommendation(self.article_id,self.num_recommendations,self.corpus)
        reco2=self.Bow_recommendation(self.article_id,self.num_recommendations,self.corpus)
        reco=reco2
        return reco

class collaborative_filtering():
    def __init__(self,user_rating_df,u_id):
        self.user_rating_df=user_rating_df
        self.u_id=u_id
        
    def similar_users(self,user_rating_df,u_id):
        features=[]
        user= self.user_rating_df.index[user_rating_df['User_ID']==self.u_id]
        user=int(user[0])
        query=[]
        query.append(self.user_rating_df.loc[user][:-1].to_numpy())
        for i in (self.user_rating_df.index):
            vector=self.user_rating_df.loc[i][:-1].to_numpy()
            features.append(vector)
            #query.append(self.user_rating_df.loc[user][:-1].to_numpy()) 
        

        user_dist= pairwise_distances(features,query)
        top_k=np.argsort(user_dist.ravel())[1:11]
        user_match=list(top_k)
        return user_match
    
    def articles(self,user_rating_df,u_id):
        user_match=self.similar_users(self.user_rating_df,self.u_id)
        q=int(self.u_id)
        details=[]
        for i in range(len(user_match)):
            vector=list(self.user_rating_df.loc[user_match[i]][:-1].to_numpy())
            details.append(vector)
        query=list(self.user_rating_df.loc[q][:-1].to_numpy())
        for i in range(len(query)):
            if query[i]!=0:
                query[i]=-11
        query=np.asarray(query)
        basic=np.zeros(self.user_rating_df.shape[1]-1)
        for i in details:
            basic=basic+np.asarray(i)
        
        basic=list(basic)
        col=[col for col in self.user_rating_df.columns[:-1]]
        article_id=[]
        basic=basic+query
        for i in range(10):
            for j in range(len(basic)):
                bound=10-i
                if basic[j]>=bound:
                    if col[j] not in article_id:
                        article_id.append(col[j])
                if len(article_id)==10:
                    break
        reco= article_id[0:10]
        return reco
    
    def recommendation(self,user_rating_df,u_id):
        reco=self.articles(self.user_rating_df,self.u_id)
        return reco

def hybrid_recommender(u_id,user_df,user_rating_df,df,corpus):
    #Colaborative
    col_fil=collaborative_filtering(user_rating_df,u_id)
    colab_recom=col_fil.recommendation(user_rating_df,u_id)
    
    # Content Based
    weight_dict=user_df['user_topic_prob'][u_id]
    keys=list(weight_dict.keys())
    values=list(weight_dict.values())
    k=sorted(values,reverse=True)
    cats=[]
    for i in k:
        ind=values.index(i)
        cats.append(keys[ind])
    cats=cats[:5]
    
    history= user_df['recent_history'][u_id]
    reco=[]
    for i in cats:
        for j in history[i]:
            content_recom=content_based_recommendations(j,1,corpus)
            cont_based_recommendations=content_recom.recommendations(j,1,corpus)
            for k in cont_based_recommendations:
                reco.append(k)
    scores=mock_bot2baseScoring(reco) 
    for i in range(len(list(scores.keys()))):
        for j in range(len(keys)):
            if list(scores.keys())[i][0:2]==keys[j][0:2]:
                scores[list(scores.keys())[i]]=round(scores[list(scores.keys())[i]]*weight_dict[keys[j]],2)
    articles= dictionary_sorter(scores)
    articles=articles[:10]
    
    recom= articles+ colab_recom
    scores=mock_bot2baseScoring(recom) 
    for i in range(len(list(scores.keys()))):
        for j in range(len(keys)):
            if list(scores.keys())[i][0:2]==keys[j][0:2]:
                scores[list(scores.keys())[i]]=round(scores[list(scores.keys())[i]]*weight_dict[keys[j]],2)
    articles= dictionary_sorter(scores)
    articles=articles[:10]
    
    headline=[]
    Datetime=[]
    News_Link=[]
    Category=[]
    Author=[]
    for i in range(len(articles)):
        ind=df.index[df["Article_ID"]==articles[i]]
        headline.append((df["Headline"][ind]).tolist()[0])
        Category.append((df["Category"][ind]).tolist()[0])
        Datetime.append((df["Datetime"][ind]).tolist()[0])
        News_Link.append((df["News_Link"][ind]).tolist()[0])
        Author.append((df["Author"][ind]).tolist()[0])
    r_df=pd.DataFrame({"Datetime": Datetime, "Category": Category, "Headline":headline, "News_Link": News_Link, "Author":Author})
    
    return r_df

def dictionary_sorter(dict):
    keys=list(dict.keys())
    values=list(dict.values())
    l=sorted(values, reverse=True)
    s_keys=[]
    for i in range(len(l)):
        for j in keys:
            if dict[j]==l[i] and j not in s_keys:
                s_keys.append(j)
    return keys

def mock_bot2baseScoring(reco):
    scores={}
    for i in reco:
        scores[i]=round(random.uniform(1.0,5.0),2)
    return scores


def bot2_recommendation(Scraped_News, user_id):

    print(user_id)

    inst=corpus_process(Scraped_News)
    df=inst.preprocess(Scraped_News)

    corpus={}
    LSH_models={}
    Bow_models={}
    unique=list(np.unique(df['Category']))
    for i in range(len(unique)):
        key=unique[i]
        corpus[key]=[]
        LSH_models[key]=[]
        Bow_models[key]=[]

    con_mod=content_based_models(df,corpus,LSH_models,Bow_models)
    corpus,LSH_models,Bow_models=con_mod.dicts(df,corpus,LSH_models,Bow_models)

    trial_user_rating_df = pd.DataFrame([[np.random.randint(-1, 2) for i in range(len(df))] for user in range(50)], columns = df.index)
    trial_user_topic_prob_list = pd.DataFrame([[np.random.random(size = (50, ))] for user in range(50)])

    user=user_rating(trial_user_rating_df,df)
    user_rating_df=user.frame(trial_user_rating_df,df)

    article_id={}
    k=list(corpus.keys())
    for i in range(len(k)):
        article_id[k[i]]=[]
    for i in range(len(list(df["Article_ID"]))):
        for j in range(len(k)):
            if k[j][0:2]== list(df["Article_ID"])[i][0:2]:
                article_id[k[j]].append(list(df["Article_ID"])[i])

    topic_list=[]
    hist_list=[]
    u_id=[]
    for i in range(50):
        utp={}
        hict={}
        t_w=list(np.random.dirichlet(np.ones(10))*1)
        k=list(corpus.keys())
        for i in range(len(k)):
            utp[k[i]]=round(t_w[i],2)
            ele=random.sample(article_id[k[i]],10)
            hict[k[i]]=list(ele)
        topic_list.append(utp)
        hist_list.append(hict)
        u_id.append(i)
        
    user_df= pd.DataFrame({"User_ID":u_id, "user_topic_prob": topic_list, "recent_history": hist_list})

    reco_dataframe= hybrid_recommender(user_id,user_df,user_rating_df,df,corpus)
    return reco_dataframe.to_dict("records")






    