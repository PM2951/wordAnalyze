import os
import pandas as pd
import requests
import xml.etree.ElementTree as ET
from collections import OrderedDict
import datetime
import nltk
import collections
from wordcloud import WordCloud
import random
import datetime

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

def pushData(rootXml, articleDics):
  for article in rootXml.iter('PubmedArticle'):
      articleDic = {
          'Abstract' : getTextFromNode(article, 'MedlineCitation/Article/Abstract/AbstractText', ''),
      }
      articleDics.append(OrderedDict(articleDic))
      

def WordSelect(articleDics):
  df_article = pd.DataFrame(articleDics)
  df_article = df_article.dropna()

  txts = ''
  for i in list(df_article['Abstract']):
    txts += i
    txts += ' '
  txts = ' '.join(txts.splitlines())
  txts = ' '.join(txts.split('('))
  txts = ' '.join(txts.split(')'))
  txts = ' '.join(txts.split('.'))
  txts = ' '.join(txts.split(','))
  txts = txts.split(' ')
  txts = [txt for txt in txts if len(txt) > 1]  #1文字のものは削除
  txts = ' '.join(txts)

  frequent_words = []
  words = nltk.word_tokenize(txts)
  tagging_words =nltk.pos_tag(words)
  selection = ['NN', 'NNS', 'NNP', 'NNP', 'NNPS', 'FW']
  for tagwrd in tagging_words:
    if tagwrd[1] in selection:
      frequent_words += [tagwrd[0]]
  frequent_words = [str.upper(i) for i in frequent_words]
  
  return frequent_words

def CommonWord(total_wards):
   c = collections.Counter(total_wards)
   
   #単数と複数形を合わせる（sとesの標準形だけ）
   key_list = list(c.keys())
   for k in key_list:
    if c[k +'S'] !=0:
      c[k] += c[k +'S']
      c.pop(k +'S')
    elif c[k +'ES'] !=0:
      c[k] += c[k +'ES']
      c.pop(k +'ES') 
   poplist = ['ET', 'AL', 'PLANT', 'GENE', 'PROTEIN','EXPRESSION', 'ARABIDOPSIS', 'THALIANA', 'ANALYSIS', 'STUDY', 'RESPONSE', 'MUTANT', 'PROCESS', 'ORGAN', "STUDIES",
             'FACTOR', 'TRANSCRIPTION', 'FUNCTION', 'ROLE', 'ACID', 'INTERACTION', 'REGULATION', 'SPECIES', 'ACTIVATION', 'SEQUENCE','MECHANISM', 'TREATMENT',
              'RESULT','LEVEL',"DATA", 'PATHWAY','OVEREXPRESSION', 'ACTIVITY', 'NUMBER','MEMBER', 'FAMILY', 'FAMILIES', 'GROUP', 'CELL', 'TRANSCRIPT', 'LINE', 
              'CROP', 'RICE','CONTROL', 'SYSTEM', 'CHANGE']
   for i in poplist:
      c.pop(i, None)
   list_word= c.most_common()
   return list_word

def WordToFig(list_word, n, output):
  wordcld = []
  for w in list_word:
    if w[1] >= n:
      wordcld += [w[0]] * w[1]
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
