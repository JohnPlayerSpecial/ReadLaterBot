from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (Updater, CommandHandler, Handler,MessageHandler, ShippingQueryHandler, Filters, ChosenInlineResultHandler, RegexHandler,ConversationHandler, CallbackQueryHandler, PreCheckoutQueryHandler)
from telegram import *
import logging
import telegram
import datetime
import tzlocal
import time
import postgresql
from newspaper import Article
import os
import urllib
from telegraph import Telegraph

DayNameDict = { "LUNEDI" : 0,
	       "MARTEDI" : 1,
	       "MERCOLEDI" : 2,
	       "GIOVEDI" : 3,
	       "VENERDI" : 4,
	       "SABATO" : 5,
	       "DOMENICA" : 6,
	      }


STRING_DB = os.environ['DATABASE_URL'].replace("postgres","pq")
TOKEN_TELEGRAM = os.environ['TOKEN_TELEGRAM']
TOKEN_TELEGRAM_2 = os.environ['TOKEN_TELEGRAM_2']
TELEGRAPH_ACCOUNT = os.environ['TELEGRAPH_ACCOUNT']
MY_CHAT_ID = int( os.environ['MY_CHAT_ID'] )
HOUR_I_WANNA_GET_MESSAGE = int( os.environ['HOUR_I_WANNA_GET_MESSAGE'] )
MINUTES_I_WANNA_GET_MESSAGE = int( os.environ['MINUTE_I_WANNA_GET_MESSAGE'] )
DAY_I_WANNA_GET_MESSAGE = os.environ['DAY_I_WANNA_GET_MESSAGE'] 
				  
telegraph = Telegraph()
telegraph.create_account(TELEGRAPH_ACCOUNT)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
STRING_DB = STRING_DB.replace("postgres","pq")

def sendVnW(bot, job):
	contatore = 0
	global TOKEN_TELEGRAM_2
	global MY_CHAT_ID
	global STRING_DB
	global stringDB
	timestamp = round( datetime.datetime.now().timestamp() )
	botVnW = telegram.Bot(TOKEN_TELEGRAM_2)
	html_content = ""
	db = postgresql.open(STRING_DB)
	ps = db.prepare("SELECT * FROM VistoNelWeb WHERE done=0;")
	resultsList = ps()
	for item in resultsList:
		url = item[1]
		photo_file_id = item[2]
		width = item[3]
		height = item[4]
		timeAdded = item[6]
		if url:
			try:
				article = Article(url)
				article.download()
				article.parse()
				length = min( 30, len(article.text) )
				articleTitle = article.title
				url2 = urllib.parse.urlsplit(url).netloc.replace("www.","")
				contatore += 1
				html_content += '<p><b>{}</b><br/>Added {}<br/><a href="{}">:::{}</a></p>'.format( articleTitle, timeAdded, url, url2 )#.replace("\n","<br />")
			except Exception as e:
				print("ERROR sendVnW url", url, e)
		if photo_file_id:
			try:
				photo_url = bot.getFile(file_id = photo_file_id).file_path
				#html_content += '<figure><img src="{}"/><figcaption>Added on {}</figcaption></figure>'.format( photo_url,  timeAdded )
				#html_content += '<img src="{}"/>'.format( photo_url )
				html_content += '<figure><img src="{}"/><figcaption>{}</figcaption></figure>'.format(photo_url,timeAdded)
			except Exception as e:
				print("ERROR sendVnW url", photo_file_id, e)
				
	print('*' * 40)		
	#print(html_content)
	#html_content = '<p>Hello, world!<br/></p><p><a href="https://telegra.ph/">Test link</a></p><figure><img src="/file/6c2ecfdfd6881d37913fa.png"/><figcaption>drawing</figcaption></figure><p>Cia</p>'
	#resp = upload_to_telegraph(title='Visto nel Web 300', author='@f126ck', text=html_content)
	#url2send = resp['url'] 
	page = telegraph.create_page(title='Visto nel Web', html_content = html_content)
	url2send = 'http://telegra.ph/{}'.format(page['path'])
	text = '<b>Good Morning!</b>\n<a href="{}">Here</a> is the post containing {} urls, good reading!!'.format( url2send, contatore) + "\n" + u"\u2063"
	#text = '<a href="{}">{}</a>'.format( url2send, url2send )
	bot.sendMessage(chat_id = MY_CHAT_ID, text = text, parse_mode = "Html")
	
	ps = db.prepare("UPDATE VistoNelWeb SET done=1 WHERE timestamp < {};".format(timestamp) )
	ps()    
	print("Check Telegram!") 
	#db.close()

def insertDB(url="", timeAdded = "", photo_file_id="", photo_width=0, photo_height=0):
	global STRING_DB
	timestamp = round( datetime.datetime.now().timestamp() )
	db = postgresql.open(STRING_DB)
	ps = db.prepare("CREATE TABLE IF NOT EXISTS VistoNelWeb (id SERIAL PRIMARY KEY, url VARCHAR(300) UNIQUE, timestamp INT, timeAdded VARCHAR(25), done INT DEFAULT 0 );")
	ps()
	ps = db.prepare("INSERT INTO VistoNelWeb (url,timestamp,timeAdded,photo_file_id,photo_width,photo_height) VALUES ('{}','{}','{}','{}','{}','{}');".format(url, timestamp, timeAdded, photo_file_id, photo_width, photo_height) )
	ps()      
	#db.close()

def getTimeAdded():
	nowTimestamp = round( datetime.datetime.now().timestamp() )
	utc_offset_heroku = time.localtime().tm_gmtoff 
	unix_timestamp = float(nowTimestamp)
	local_timezone = tzlocal.get_localzone() # get pytz timezone
	local_time = datetime.datetime.fromtimestamp(unix_timestamp, local_timezone)
	myLocalTimestamp = nowTimestamp + utc_offset_heroku 
	my_time = datetime.datetime.fromtimestamp(myLocalTimestamp, local_timezone)
	
	hour = datetime.datetime.time(datetime.datetime.now()).hour
	minute = datetime.datetime.time(datetime.datetime.now()).minute
	second = datetime.datetime.time(datetime.datetime.now()).second
	dt = datetime.datetime.combine(datetime.date.today(), datetime.time(hour,minute,second)) + datetime.timedelta(seconds = utc_offset_heroku)
	
	dateInsertion = dt.strftime("%a %-d %b %Y %-H:%M")
	return dateInsertion

def getMyTimeZoneTime():
	global HOUR_I_WANNA_GET_MESSAGE
	global MINUTES_I_WANNA_GET_MESSAGE
	utc_offset_heroku = time.localtime().tm_gmtoff / 3600
	hour = HOUR_I_WANNA_GET_MESSAGE + ( int(utc_offset_heroku) - 2 ) # 2 is my offset
	time2 = datetime.time(hour = hour , minute = MINUTES_I_WANNA_GET_MESSAGE, second = 0)
	print(time2)
	return time2
	
def printUpdate(bot,update):
	timeAdded = getTimeAdded()
	if update.message.text:
		text = update.message.text
		#print(text)
		if update.message.entities:
			for item in update.message.entities:
				#print(item)
				if item['type'] == 'url':
					#print(item)
					length = item['length']
					offset = item['offset']
					url = text[offset:(offset + length)]
					if url is not None:
						insertDB(url = url, timeAdded = timeAdded)
						print("Done inserting url by TYPE", url)
				else:
					url = item["url"]
					insertDB(url = url, timeAdded = timeAdded)
					print("Done inserting url by URL", url)
	if update.message.photo:
		#print(update.message.photo[-1].file_id, bot.getFile(file_id = update.message.photo[-1].file_id).file_path )
		#update.message.photo is n array: with -1 I get the highest resolution photo
		width = update.message.photo[-1].width
		height = update.message.photo[-1].height
		file_id = update.message.photo[-1].file_id
		insertDB(photo_file_id = file_id, photo_width = width, photo_height = height,  timeAdded = timeAdded)
		print("Done inserting photo", file_id)
		
		
updater = Updater(TOKEN_TELEGRAM) 
dp = updater.dispatcher
updater.dispatcher.add_handler( MessageHandler( Filters.text , callback = printUpdate) ) #Filters.entity("url")
j = updater.job_queue

dayNumber = DayNameDict[ DAY_I_WANNA_GET_MESSAGE ]
print(dayNumber)
#                          must be a tuple
j.run_daily(sendVnW, days=(dayNumber,), time = getMyTimeZoneTime() )

updater.start_polling()
updater.idle()
