from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import time
import numpy as np
import mysql.connector as mysql
from lmdbcache import LMDBCacheContextManager
lmdbpath = "pibcache"

#delays = [5, 4, 6, 2, 1, 3]

#delays = [1]

db = mysql.connect(
  host='localhost',
  user='root',
  database='pibscrape'
)
cursor = db.cursor()
#cursor.execute("CREATE TABLE data (prid INT, text MEDIUMTEXT, date VARCHAR(255))")

headers = {
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36',
    'referrer': 'https://google.com',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
    }

def url_open(url):
    req = Request(url, headers=headers)
    web_byte = urlopen(req).read()
    web_page = web_byte.decode('utf-8')
    soup = BeautifulSoup(web_page, 'html.parser')
    return soup

def insert(prid,text,date):
	query = "INSERT INTO data (prid, text, date) VALUES (%s, %s, %s)"
	values = (prid, text, date)
	cursor.execute(query, values)
	db.commit()


with LMDBCacheContextManager(lmdbpath+"error") as errorcache:
	with LMDBCacheContextManager(lmdbpath+"empty") as emptycache:
		with LMDBCacheContextManager(lmdbpath) as cache:
			for i in range(1479816,1590000):
				if (not cache.db.findkey(str(i))) and (not emptycache.db.findkey(str(i))) and (not errorcache.db.findkey(str(i))):
					#delay = np.random.choice(delays)
					delay = 1
					#time.sleep(delay)
					try:
						soup = url_open('https://pib.gov.in/PressReleasePage.aspx?PRID={}'.format(i))
					except Exception as e:
						print(i,e)
						errorcache(str(i), "Error")
						continue
					else:
						content = soup.find('div', {'id': 'PdfDiv'})
						text = content.text.strip()
						if(text != "Posted On:"):
							cached_text = cache(str(i), text)
							insert(i,text,None)
							print('release found with id:{} and inserted into db'.format(i))
						else:
							emptycache(str(i), "Nothing")
							print('empty release found with id:{}'.format(i))

#out=open('out/{}.txt'.format(i),'w')
#out.write(text)
#out.close()

'''
for i in range(1450000,1600000):
	try:
		soup=url_open('https://pib.gov.in/PressReleasePage.aspx?PRID={}'.format(i))		
	except:
		print('no release found with id:{} found'.format(i))
	else:
		paragraph=soup.find('div', {'id': 'PdfDiv'})
		if(paragraph!="Posted On:"):
			#print('empty release found with id:{} found'.format(i))
		#else:
			out=open('{}.txt'.format(i),'w')
			out.write(paragraph.text.strip())
			out.close()
'''

