import os
import math
import time
import pandas as pd
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
search_word = args[1]       #検索ワード
min_year = args[2]            #現在から何年分遡るか
max_year = args[3]            #現在から何年分遡るか

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

def main():
  
  # pubmed api URL
  BASEURL_SRCH = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
  BASEURL_FTCH = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'

  total_wards =[]

  # pubmed search parameterss
  SOURCE_DB    = 'pubmed'
  TERM         = search_word 
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

  # get all article data
  articleDics = []
  pushData(rootXml, articleDics)
  # ceil
  iterCount = math.ceil(int(Count) / BATCH_NUM)
  
  # get all data
  for i in range(iterCount):
    print("\r"+str(i)+'/'+str(iterCount),end="")
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
        time.sleep(10)
        num +=1
       
  total_wards += WordSelect(articleDics)
      
  if len(total_wards) == 0:
    print('論文数が0です')
  else:
    list_word= CommonWord(total_wards)
    WordToFig(list_word, 3)

main()
