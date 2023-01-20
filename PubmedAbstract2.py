# !pip install nltk
# !pip install wordcloud

import requests
import xml.etree.ElementTree as et
import os
import pandas as pd
import nltk
import collections
from wordcloud import WordCloud
import random
import math
import numpy as np
import urllib.parse
import uuid
from collections import OrderedDict
import sys


# os.chdir(os.path.dirname(os.path.abspath(__file__)))

path = os.getcwd()
try:
    os.makedirs(path + 'csv')
except FileExistsError:
    pass
try:
    os.makedirs(path + 'Figure')
except FileExistsError:
    pass

args = sys.argv
search = str(args[1])
# search = 'arabidopsis'


# pubmed search parameters
SOURCE_DB    = 'pubmed'
TERM         = search
DATE_TYPE    = 'pdat'       # Type of date used to limit a search. The allowed values vary between Entrez databases, but common values are 'mdat' (modification date), 'pdat' (publication date) and 'edat' (Entrez date). Generally an Entrez database will have only two allowed values for datetype.
# MIN_DATE     = '2021/06/01' # yyyy/mm/dd
# MAX_DATE     = '2021/12/31' # yyyy/mm/dd
SEP          = ' '
BATCH_NUM    = 1000

# pubmed api URL
BASEURL_INFO = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/einfo.fcgi'
BASEURL_SRCH = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
BASEURL_FTCH = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'

BASE_PATH = os.getcwd()

def mkquery(base_url, params):
   base_url += '?'
   for key, value in zip(params.keys(), params.values()):
       base_url += '{key}={value}&'.format(key=key, value=value)
   url = base_url[0:len(base_url) - 1]
   print('request url is: ' + url)
   return url

def getXmlFromURL(base_url, params):
   response = requests.get(mkquery(base_url, params))
   return et.fromstring(response.text)

def getTextFromNode(root, path, fill='', mode=0, attrib='attribute'):
   if (root.find(path) == None):
       return fill
   else:
       if mode == 0:
           return root.find(path).text
       if mode == 1:
           return root.find(path).get(attrib)
       
# get xml
rootXml = getXmlFromURL(BASEURL_SRCH, {
   'db': SOURCE_DB,
   'term': TERM,
   'usehistory': 'y',
  #  'datetype': DATE_TYPE,
  #  'mindate': MIN_DATE,
  #  'maxdate': MAX_DATE,
   })

# get querykey and webenv
Count = rootXml.find('Count').text
QueryKey = rootXml.find('QueryKey').text
WebEnv = urllib.parse.quote(rootXml.find('WebEnv').text)

if int(Count) >= 30000:
  raise ValueError('論文数が0の可能性があります')

# get all article data
articleDics = []

def pushData(rootXml):
   for article in rootXml.iter('PubmedArticle'):
       
       articleDic = {
           'Title'                   : getTextFromNode(article, 'MedlineCitation/Article/ArticleTitle', ''),
           'Abstract'                : getTextFromNode(article, 'MedlineCitation/Article/Abstract/AbstractText', ''),
           'Keyword'                 : SEP.join([keyword.text if keyword.text != None else ' '  for keyword in article.findall('MedlineCitation/KeywordList/')]),
       }
       articleDics.append(OrderedDict(articleDic))

# ceil
iterCount = math.ceil(int(Count) / BATCH_NUM)

# get all data
for i in range(iterCount):
  num =0
  while num <=3:
    try:
      rootXml = getXmlFromURL(BASEURL_FTCH, {
          'db': SOURCE_DB,
          'query_key': QueryKey,
          'WebEnv': WebEnv,
          'retstart': i * BATCH_NUM,
          'retmax': BATCH_NUM,
          'retmode': 'xml'})
      num +=10
    except:
      num +=1
  pushData(rootXml)
   
# article
df_article = pd.DataFrame(articleDics)
df_article = df_article.fillna(' ')

txts =''
for t,a,k in zip(list(df_article['Title']), list(df_article['Abstract']), list(df_article['Keyword'])):
  txts += t + ' ' + a + ' ' + k + ' '

##　文字列の処理
# txts = ' '.join(txts.splitlines())
# txts = ' '.join(txts.split('('))
# txts = ' '.join(txts.split(')'))
txts = ' '.join(txts.split('.'))
txts = ' '.join(txts.split('-'))
# txts = ' '.join(txts.split(','))
# txts = ' '.join(txts.split(':'))
# txts = txts.split(' ')
# txts = [txt for txt in txts if len(txt) > 1]  #1文字のものは削除
# txts = ' '.join(txts)

frequent_words = []

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
words = nltk.word_tokenize(txts)
tagging_words =nltk.pos_tag(words)
selection = ['NN', 'NNS', 'NNP', 'NNP', 'NNPS', 'FW']
for tagwrd in tagging_words:
  if tagwrd[1] in selection:
    frequent_words += [tagwrd[0]]
frequent_words = [str.upper(i) for i in frequent_words]
c = collections.Counter(frequent_words)

#単数と複数形を合わせる（sとesの標準形だけ）
key_list = list(c.keys())
for k in key_list:
  if c[k +'S'] !=0:
    c[k] += c[k +'S']
    c.pop(k +'S')
  elif c[k +'ES'] !=0:
    c[k] += c[k +'ES']
    c.pop(k +'ES') 
  elif c['AT' + k] !=0:    #　NPR1 = AtNPR1　にする
    c[k] += c['AT' + k]
    c.pop('AT' + k) 

list_word= c.most_common()

from functools import lru_cache
import scipy.stats as st


@lru_cache(maxsize=None)
def fisher(a,b,c,d):
  data = [[a,b-a],
          [c,d-c]]
  return st.fisher_exact(data)[1]


dfa=pd.read_csv('wordcloud_arabidopsis.csv') #ここを変えればarabidopsis以外も可能
dfs = pd.DataFrame(list_word)
dfs.columns=['word', 'count']
df = pd.merge(dfa,dfs, on ='word')
df['expect'] =df['countAll']* df['count'].sum() /df['countAll'].sum()
df['FC'] = df['count']/df['expect']
df_filter = df[df['FC'] >=3].copy()
b = df['count'].sum()
d = df['countAll'].sum()
df_filter['Pvalue'] = [fisher(a,b,c,d) for a,c in zip(list(df_filter['count']), list(df_filter['countAll']))]
df_filter= df_filter[df_filter['Pvalue'] <0.01].copy()
df_filter.to_csv(f'csv/wordcloud_{search}.csv', index=False)



wordcld = []
n = 3
output = f'Figure/wordcloud_{search}.png'
for w, num in zip(list(df_filter['word']), list(df_filter['count'])):
  if num >= n:
    wordcld += [w] * num
random.shuffle(wordcld)
wordcld = ' '.join(wordcld)
wordcloud = WordCloud(background_color="white",
                      # font_path=fpath, 
                      width=600,
                      height=400,
                      min_font_size=15,
                      )
wordcloud =wordcloud.generate(wordcld)
wordcloud.to_file(output)
print('SAVE Fig')

