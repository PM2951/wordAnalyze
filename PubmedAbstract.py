import sys

args = sys.argv

search_word = args[1]       #検索ワード
cycles = args[2]            #現在から何年分遡るか


import os
import math
import pandas as pd
import requests
import urllib.parse
import xml.etree.ElementTree as ET
from collections import OrderedDict
import datetime
import nltk
import collections
from pprint import pprint
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import random
from tqdm.notebook import tqdm as tqdm
import datetime

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

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
  #  print('request url is: ' + url)
   return url

def getXmlFromURL(base_url, params):
   response = requests.get(mkquery(base_url, params))
   return ET.fromstring(response.text)

def getTextFromNode(root, path, fill='', mode=0, attrib='attribute'):
   if (root.find(path) == None):
       return fill
   else:
       if mode == 0:
           return root.find(path).text
       if mode == 1:
           return root.find(path).get(attrib)

# cycles = 10   
interval_m = 3
max_day = datetime.datetime.now()
min_day = max_day - datetime.timedelta(days=30 *interval_m)
total_wards =[]
print(f'total year: {cycles*interval_m/12}')
for i in tqdm(range(cycles)): 
  # pubmed search parameters
  SOURCE_DB    = 'pubmed'
  TERM         = search_word 
  DATE_TYPE    = 'pdat'       
  MIN_DATE     = min_day.strftime('%Y/%m/%d')
  MAX_DATE     = max_day.strftime('%Y/%m/%d')
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
  
  max_day = min_day - datetime.timedelta(days=1)
  min_day = max_day - datetime.timedelta(days=30 *interval_m)

  # get querykey and webenv
  Count = rootXml.find('Count').text
  QueryKey = rootXml.find('QueryKey').text
  WebEnv = urllib.parse.quote(rootXml.find('WebEnv').text)
  print(f'範囲{MIN_DATE} - {MAX_DATE};  total Count: {Count}')

  # get all article data
  articleDics = []

  def pushData(rootXml):
    for article in rootXml.iter('PubmedArticle'):
        articleDic = {
            'Abstract' : getTextFromNode(article, 'MedlineCitation/Article/Abstract/AbstractText', ''),
        }
        articleDics.append(OrderedDict(articleDic))

  # ceil
  iterCount = math.ceil(int(Count) / BATCH_NUM)
  
  # get all data
  for i in range(iterCount):
    try:
      rootXml = getXmlFromURL(BASEURL_FTCH, {
          'db': SOURCE_DB,
          'query_key': QueryKey,
          'WebEnv': WebEnv,
          'retstart': i * BATCH_NUM,
          'retmax': BATCH_NUM,
          'retmode': 'xml',
          })
      pushData(rootXml)
    except:
      try:
        print('try again')
        rootXml = getXmlFromURL(BASEURL_FTCH, {
          'db': SOURCE_DB,
          'query_key': QueryKey,
          'WebEnv': WebEnv,
          'retstart': i * BATCH_NUM,
          'retmax': BATCH_NUM,
          'retmode': 'xml',
          })
        pushData(rootXml)
      except:
        print('skip')
      

    
  # article
  df_article = pd.DataFrame(articleDics)
  df_article = df_article.dropna()

  txts = ''
  try:
    for i in list(df_article['Abstract']):
        txts += i
        txts += ' '
    txts = ' '.join(txts.splitlines())
    txts = ' '.join(txts.split('('))
    txts = ' '.join(txts.split(')'))
    txts = ' '.join(txts.split('.'))
    txts = ' '.join(txts.split(','))
    txts = txts.split(' ')
    txts = [txt for txt in txts if len(txt) > 1]
    txts = ' '.join(txts)

    frequent_words = []
    words = nltk.word_tokenize(txts)
    tagging_words =nltk.pos_tag(words)
    selection = ['NN', 'NNS', 'NNP', 'NNP', 'NNPS', 'FW']
    for tagwrd in tagging_words:
      if tagwrd[1] in selection:
        frequent_words += [tagwrd[0]]
    frequent_words = [str.upper(i) for i in frequent_words]

    total_wards += frequent_words
  except:
    print('論文数が0です')

print(len(total_wards))
if len(total_wards) == 0:
  print('論文数が0です')
else:
  c = collections.Counter(total_wards)
  #単数と複数形を合わせる（sとesの標準形だけ）
  key_list = list(c.keys())
  for k in key_list:
    if k == 'ET':
      c.pop('ET')
    elif k == 'AL':
      c.pop('AL')
    elif c[k +'S'] !=0:
      c[k] += c[k +'S']
      c.pop(k +'S')
    elif c[k +'ES'] !=0:
      c[k] += c[k +'ES']
      c.pop(k +'ES')

  list_word= c.most_common()

  cword = []
  for w in list_word:
    if w[1] >= 3:
      cword += [w[0]] * w[1]

  random.shuffle(cword)
  cword = ' '.join(cword)

  wordcloud = WordCloud(background_color="white",
                        # font_path=fpath, 
                        width=600,
                        height=400,
                        min_font_size=15,
                        )
  wordcloud =wordcloud.generate(cword)
  plt.figure()
  plt.axis("off")
  plt.imshow(wordcloud)
  all_word = list_word