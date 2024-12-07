import pandas as pd
from pymongo import MongoClient
import csv
from bs4 import BeautifulSoup
from time import sleep
import re
import requests
import html5lib
from IPython.display import clear_output
from datetime import datetime
import re

client = MongoClient("mongodb://localhost:27017/")
db = client["UTA_Enrollment"]
articles = db["articles"]

def solve(s):                                             
    return re.sub(r'(\d)(st|nd|rd|th)', r'\1', s)

def remove_redun_rows(df, default_cols, cont_col_subset = ["Category", "Headline", "Summary", "Entire_News", "News_Link"], meta_col_subset = ["Datetime"]):
    """It removes faulty or duplicate rows
    If there are more columns in the given dataframe than default, this removes those rows that have such more columns. 
    If there are less columns in the given dataframe than default, it returns "None", thereby marking them unusable. 
    If there are duplicated content in any "cont_col_subset", it drops the extra rows except the latest entry.
    If there are rows with missing values for important columns, it removes such rows. 
    If there are rows with missing values for non-important columns, it ignores them, but informs there existence. 
    It returns the trimmed dataframe as the output in all cases except when the number of columns are less than default,
    and prints any missing values in non-important columns"""
    skip = False
    if list(df.columns) != list(default_cols):
        if len(df.columns) == len(default_cols):
            print("There seems to be some error in columns names")
        elif len(df.columns) < len(default_cols):
            print("The given DataFrame seems to have some missing columns")
            df = None # Marking the df useless
            skip = True # Skipping the DataFrame operations
        elif len(df.columns) > len(default_cols):
            print("The given DataFrame seems to have more columns than required")
            df_xtra_col_idx = df.loc[:, df.columns[len(default_cols):]].isnull().any(axis = 1)
            df = df.loc[df.index[df_xtra_col_idx], default_cols]
    if not skip:
        df = df.drop_duplicates(subset = cont_col_subset)
        df = df.dropna(subset = cont_col_subset+meta_col_subset)
    return df

def cat_reformat(df):
    df['Category'] = df['Category'].replace(['business'],'Business')
    df['Category'] = df['Category'].replace(['Business-news'],'Business')
    df['Category'] = df['Category'].replace(['India-news'],'India')
    df['Category'] = df['Category'].replace(['Sports-news'],'Sports')
    df['Category'] = df['Category'].replace(['sports'],'Sports')
    df['Category'] = df['Category'].replace(['tvshowbiz'],'Entertainment')
    df['Category'] = df['Category'].replace(['entertainment'],'Entertainment')
    df['Category'] = df['Category'].replace(['Television'],'Entertainment')
    df['Category'] = df['Category'].replace(['Entertainment-news'],'Entertainment')
    df['Category'] = df['Category'].replace(['Technology-news'],'Technology')
    df['Category'] = df['Category'].replace(['technology'],'Technology')
    df['Category'] = df['Category'].replace(['World-news'],'World')
    df['Category'] = df['Category'].replace(['news'],'News')
    df['Category'] = df['Category'].replace(['society'],'Society')
    df['Category'] = df['Category'].replace(['Data-intelligence-unit'],'News')
    df['Category'] = df['Category'].replace(['Movies'],'Entertainment')
    df['Category'] = df['Category'].replace(['Education-today'],'Education')
    df['Category'] = df['Category'].replace(['Cities'],'India')
    return df

#looking at the website of indian express,they have a task bar on the first page for broad categories of news
#following those broad categories there were some obvious sub-categories where news were covered, these are
#mentioned here

categories = {
    'india':[''],
    'cities':[''],
    'sports':[
         'badminton', 'cricket', 'football', 
        'fifa', 'hockey', 'motor-sport', 'tennis', 
        'wwe-wrestling'
        ], 
    'business':[
        'aviation', 'banking-and-finance',
        'companies', 'economy', 'market'
        ],
    'technology':[
        'gadgets','laptops',
        'tech-reviews','science','techook'
        ],
    'entertainment':['bollywood','hollywood',
        'television','tamil','telugu','malayalam',
        'web-series','movie-review','box-office-collection'
        ]
}


csv_file = 'IndianExpress.csv'

ndf1 = pd.DataFrame(columns = [
    'Datetime',
    'Category',
    'Subcategory',
    'Headline',
    'Summary',
    'Entire_News',
    'Author',
    'News_Link'
])


ndf1.index.name = "Index"


#suppose a webpage doesn't exisit for a particular category->sub-category then this data frame will be used to 
#append that error! page not found type of error

edf1 = pd.DataFrame(columns = [
    'Website Link',
    'Error'
])


if __name__ == '__main__':
    news_website_link = "https://indianexpress.com"
    
    for category in categories:
        for sub_category in categories[category]:
                
            for page in range(0,1):  #number of pages to search for
                #link for a particular news webpage
                news_url = news_website_link + "/section/" + category + "/" + sub_category + "/" + "page/" + str(page) + "/"
                
                #scrap the html version of the webpage
                sleep(0.05)

                try:
                    news_html_page = requests.get(news_url)

                except Exception as e:
                        
                        # Pushing the error website link data to the DataFrame
                        edf1 = edf1.append({
                            'Website Link' : news_urll, 
                            'Error' : e
                        },
                        ignore_index = True)
                        continue
                
                #interpret the html file to actual sequence of words
                news_html_interpreted = BeautifulSoup(news_html_page.content,'html.parser')
                
                # Fetching news url for every news on a page from headings and titles
                news_head_list = news_html_interpreted.findAll('h2')

                print(category)
                print(sub_category)
                print(page) 
                
                i = 0
                for news_head in news_head_list:

                    try:
                        news_urll = news_head.find('a')['href']

                        if articles.find_one({"News_Link": news_urll}):
                            break    

                        news_html_data = requests.get(news_urll)

                        news_html_interpretation = BeautifulSoup(news_html_data.content, 'html.parser')

                         # Fetching the headline and brief description of the news
                        title = news_html_interpretation.find('h1',attrs={'class':'native_story_title'}).get_text()
                        summary = news_html_interpretation.find('h2', attrs={'class':'synopsis'}).get_text()

                        # Fetching the author, date and time of publish
                        publishing_details = news_html_interpretation.find('div', attrs={'class':'editor'})
                        publisher = publishing_details.find('a').get_text()
                        date_time = publishing_details.find('span').get_text()

                        dt = date_time.split()
                        dt.remove("Updated:")
                        date_time = dt[0] + " " + dt[1] + " " + dt[2] + " " + dt[3] + " " + dt[4]
                        datetime_object = datetime.strptime(solve(date_time), '%B %d, %Y %I:%M:%S %p')
                        
                        
                        # Fetching the entire content of the news 
                        report = ""
                        report_paras = news_html_interpretation.findAll('p')
                        for para in range(len(report_paras)):
                            report += report_paras[para].get_text()

                        print(i, end = " ")
                        i = i + 1
                        
                    except Exception as e:
                        edf1 = edf1.append({
                            'Website Link' : news_urll, 
                            'Error' : e
                        },
                        ignore_index = True)
                        continue
                    
                    # Pushing the scrapped news data to the DataFrame
                    ndf1 = ndf1.append({
                        'Datetime' : datetime_object,
                        # 'Time' : time,
                        'Category' : category.capitalize(),
                        'Subcategory' : sub_category.capitalize(),
                        'Headline' : title,
                        'Summary' : summary, 
                        'Entire_News' : report,
                        'Author' : publisher.capitalize(), 
                        'News_Link' : news_urll
                        },
                        ignore_index = True)

    if not ndf1.empty:

        temp = remove_redun_rows(ndf1, default_cols = ndf1.columns)
        temp = cat_reformat(temp)

        # Storing the DataFrame to a .csv file
        for i in articles.find().sort("ID",-1).limit(1):
            last_id = int(i["ID"]) + 1
            temp.index = temp.index + last_id
        temp.insert(loc=0, column='ID', value=temp.index)
        data_dict = temp.to_dict("records")
        articles.insert_many(data_dict)

        # Storing the unscrapped(error) data to csv
        edf1.to_csv('Error_Data_RW.csv', index = False, encoding='utf')
