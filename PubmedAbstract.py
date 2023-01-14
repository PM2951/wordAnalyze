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
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import random
import datetime
import sys
from PubmedAbstract_utils import getXmlFromURL, pushData, WordSelect, CommonWord, WordToFig

def main():
  args = sys.argv
  search_word = args[1]       #検索ワード
  cycles = args[2]            #現在から何年分遡るか
  
  nltk.download('punkt')
  nltk.download('averaged_perceptron_tagger')

  # pubmed api URL
  BASEURL_INFO = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/einfo.fcgi'
  BASEURL_SRCH = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
  BASEURL_FTCH = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'

  BASE_PATH = os.getcwd()

  # cycles = 10   
  interval_m = 3
  max_day = datetime.datetime.now()
  min_day = max_day - datetime.timedelta(days=30 *interval_m)
  total_wards =[]

  for i in range(cycles*4): 
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
    articleDics = pushData(rootXml, articleDics)
    # ceil
    iterCount = math.ceil(int(Count) / BATCH_NUM)
    params = {
      'db': SOURCE_DB,
      'query_key': QueryKey,
      'WebEnv': WebEnv,
      'retstart': i * BATCH_NUM,
      'retmax': BATCH_NUM,
      'retmode': 'xml'}
    
    # get all data
    for i in range(iterCount):
      try:
        rootXml = getXmlFromURL(BASEURL_FTCH, params)
        pushData(rootXml,articleDics)
      except:
        try:
          print('try again')
          rootXml = getXmlFromURL(BASEURL_FTCH, params)
          pushData(rootXml,articleDics)
        except: print('skip')
    
    total_wards += WordSelect(articleDics)
      
  if len(total_wards) == 0:
    print('論文数が0です')
  else:
    list_word= CommonWord(total_wards)
    WordToFig(list_word, 3)

if __name__ == '__main':
  main()