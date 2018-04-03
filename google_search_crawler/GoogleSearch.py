#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
import ssl, requests, urllib, sys, json, pyprind
from bs4 import BeautifulSoup

class MyAdapter(HTTPAdapter):
	def init_poolmanager(self, connections, maxsize, block=False):
		self.poolmanager = PoolManager(num_pools=connections,
									   maxsize=maxsize,
									   block=block,
									   ssl_version=ssl.PROTOCOL_TLSv1)
class GoogleSearch(object):
	"""docstring for GoogleSearch"""
	def __init__(self, adapters, keyword):
		self.keyword = keyword
		self.session = requests.Session()
		self.headers = {
		'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.59 Safari/537.36'}
		self.adapters = adapters
		self.response = self.__craw()
		self.soup = BeautifulSoup(self.response.text, "html.parser")
		self.json = {}

	def __craw(self):
		self.session.mount('https://', self.adapters())
		re = self.session.get("https://www.google.com.tw/search?q={}".format(urllib.parse.quote(self.keyword)),  headers=self.headers)
		return re

	def get(self,selector, key):
		try:
			tmp = self.soup.select(selector)[0].text
			self.json[key] = tmp
		except Exception as e:
			return

	def getMetaData(self):
		result = self.soup.find('div', 'ivg-i').text
		result = json.loads(result)
		self.json.update(result)

	def getProf(self):
		self.get('.kno-ecr-pt.kno-fb-ctx', 'Country')
		self.get('.kno-rdesc', 'WikiIntro')
		self.get('span._Xbe.kno-fv', 'Capital')
		self.get('#resultStats', 'resultStats')
		self.get('div._gdf.kno-fb-ctx', 'tag')

	def dump(self):
		with open('GoogleSearch/{}.json'.format(self.keyword), 'w', encoding='utf-8') as f:
			json.dump(self.json, f)

if __name__ == '__main__':
	import time, random
	from gensim import models
	import os.path
	def is_chinese(uchar):         
		if '\u4e00' <= uchar<='\u9fff':
			return True
		else:
			return False
	model = models.KeyedVectors.load_word2vec_format('med400.model.bin.real', binary=True)
	keywordList = sorted([i for i in model.vocab.keys() if len(i) >2 and is_chinese(i)], key=lambda x:len(x), reverse=True)
	for i in pyprind.prog_bar(keywordList):
		if os.path.isfile('GoogleSearch/' + i + '.json'):
			print(i + 'is already in directory.')
		else:
			g = GoogleSearch(MyAdapter, i)
			g.getProf()
			if 'tag' not in g.json:
				continue
			g.dump()
			time.sleep(random.randint(1,15))
