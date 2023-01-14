import os
import math
import time
import pandas as pd
from scipy import stats
import requests
import urllib.parse
import xml.etree.ElementTree as ET
from collections import OrderedDict
import datetime
import nltk
import collections
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import random
import datetime
import sys
from PubmedAbstract_utils import getXmlFromURL, pushData, WordSelect, CommonWord, WordToFig


args = sys.argv
control_word = args[1]       #検索ワード
search_word = args[2]       #検索ワード
min_year = args[3]            #現在から何年分遡るか
max_year = args[4]            #現在から何年分遡るか

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

def main(word):
  
  # pubmed api URL
  BASEURL_SRCH = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
  BASEURL_FTCH = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'

  total_wards =[]

  # pubmed search parameterss
  SOURCE_DB    = 'pubmed'
  TERM         = word 
  DATE_TYPE    = 'pdat'       
  MIN_DATE     = min_year
  MAX_DATE     = max_year
  SEP          = '|'
  BATCH_NUM    = 1000

  # get xml
  rootXml = getXmlFromURL(BASEURL_SRCH, {
    'db': SOURCE_DB,
    'term': TERM,
    'usehistory': 'y',
    'datetype': DATE_TYPE,
    'mindate': MIN_DATE,
    'maxdate': MAX_DATE})

  # get querykey and webenv
  Count = rootXml.find('Count').text
  QueryKey = rootXml.find('QueryKey').text
  WebEnv = urllib.parse.quote(rootXml.find('WebEnv').text)
  print(f'範囲{MIN_DATE} - {MAX_DATE};  total Count: {Count}')
  if Count ==0:
    print('論文数が0です')
  else:
    # get all article data
    articleDics = []
    pushData(rootXml, articleDics)
    # ceil
    iterCount = math.ceil(int(Count) / BATCH_NUM)

    # get all data
    print("\r"+'0/'+str(iterCount),end="")
    for i in range(iterCount):
      num =1
      while num <= 3:
        try:
          rootXml = getXmlFromURL(BASEURL_FTCH, {
            'db': SOURCE_DB, 'query_key': QueryKey,
            'WebEnv': WebEnv, 'retstart': i * BATCH_NUM,
            'retmax': BATCH_NUM, 'retmode': 'xml'})
          pushData(rootXml,articleDics)
          num +=10
        except:
          time.sleep(10*num)
          if num == 3:
            print('skip')
          num +=1
      print("\r"+str(i+1)+'/'+str(iterCount),end="")
      
    print('\n')
    total_wards += WordSelect(articleDics)
    list_word= CommonWord(total_wards)
    path = os.getcwd()
    output = f'{path}/wordcloud_{word}.png'
    WordToFig(list_word, 3, output)
    return list_word

ctl = main(control_word)
sch = main(search_word)

df1 = pd.DataFrame(ctl)
df1.columns=['word', 'count1']
df2 = pd.DataFrame(sch)
df2.columns=['word', 'count2']

df = pd.merge(df1,df2, on='word')
del df1, df2
ration = df['count2'].sum()/df['count1'].sum()
df['RARf'] = (df['count2']/df['count1'])/ration
df['pvalue'] = [stats.binom_test(v2, df['count2'].sum(), v1/(df['count1'].sum())) for v1, v2 in zip(list(df['count1']),list(df['count2']))]
path = os.getcwd()
df.to_csv(f'{path}/wordcloud_df.csv')
df_filter=df[(df['RARf'] >=3) & (df['pvalue'] < 0.05)
df_filter.to_csv(f'{path}/wordcloud_dffilter.csv')
