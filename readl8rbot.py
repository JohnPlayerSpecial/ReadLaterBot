from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (Updater, CommandHandler, Handler,MessageHandler, ShippingQueryHandler, Filters, ChosenInlineResultHandler, RegexHandler,ConversationHandler, CallbackQueryHandler, PreCheckoutQueryHandler)
from telegram import *
import logging
import telegram
import datetime
import tzlocal
import time
import postgresql
from html_telegraph_poster import upload_to_telegraph
from newspaper import Article
import os
import urllib


try:
	STRING_DB = os.environ['DATABASE_URL'].replace("postgres","pq")
	TOKEN_ALERT = os.environ['TOKEN_ALERT']
	TOKEN_TELEGRAM = os.environ['TOKEN_TELEGRAM']
	TELEGRAPH_ACCOUNT = os.environ['TELEGRAPH_ACCOUNT']
	MY_CHAT_ID = int( os.environ['MY_CHAT_ID'] )
	TELEGRAPH_ACCOUNT = os.environ['TELEGRAPH_ACCOUNT']
	
except:
	hour = datetime.datetime.time(datetime.datetime.now()).hour
	minute = datetime.datetime.time(datetime.datetime.now()).minute
	second = datetime.datetime.time(datetime.datetime.now()).second
	dt = datetime.datetime.combine(datetime.date.today(), datetime.time(hour,minute,second)) + datetime.timedelta(seconds=10)
	HOUR_I_WANNA_GET_MESSAGE = dt.hour
	MINUTES_I_WANNA_GET_MESSAGE = dt.minute
	SECONDS_I_WANNA_GET_MESSAGE = dt.second
	0
	MY_CHAT_ID = 31923577
	TELEGRAPH_ACCOUNT = 's'
		
TOKEN_TELEGRAM = '352887843:AAGFmxDpBFc9v6__gN6c2kQF9wntbkahtE4'
TOKEN_TELEGRAM_2 = '408255938:AAEspHUZw2tJ3m1xkjGF3bW6TgWkyycgYzU' #visto web
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

STRING_DB = 'postgres://eygmgbtinfsxrx:1b019452e37816ab12c60b80a6ec1c767bd067e6f78c346e8f76d15f30e4ce9e@ec2-54-75-234-89.eu-west-1.compute.amazonaws.com:5432/d10htgn7cvq4q3'
STRING_DB = STRING_DB.replace("postgres","pq")

def sendVnW(bot, job):
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
	print('*' * 40)
	for item in resultsList:
		url = item[1]
		photo_file_id = item[2]
		width = item[3]
		height = item[4]
		timeAdded = item[6]
		if url:
			try:
				print("\t", url)
				article = Article(url)
				article.download()
				article.parse()
				length = min( 30, len(article.text) )
				articleTitle = article.title
				url2 = urllib.parse.urlsplit(url).netloc.replace("www.","")
				html_content += '<b>{}</b>\n<br>Added on {}<br>:::<a href="{}">{}</a>\n\n'.format( articleTitle, timeAdded, url, url2 )#.replace("\n","<br>")
			except Exception as e:
				print("ERROR sendVnW url", url, e)
		if photo_file_id:
			print("\t", photo_file_id)
			photo_url = bot.getFile(file_id = photo_file_id).file_path
			#html_content += '<figure><img src="{}"></img><figcaption>Added on {}</figcaption></figure>\n'.format( photo_url,  timeAdded )
			
	print(html_content)
	print('*' * 40)
	resp = upload_to_telegraph(title='Visto nel Web', author='@f126ck', text=html_content)
	url2send = resp['url'] 
	text = '<b>Good Morning!</b>\n<a href="{}">Here</a> is the post, good reading!!'.format( url2send ) + "\n" + u"\u2063"
	botVnW.sendMessage(chat_id = MY_CHAT_ID, text = text, parse_mode = "Html")
	
	ps = db.prepare("UPDATE VistoNelWeb SET done=1 WHERE timestamp < {};".format(timestamp) )
	ps()    
	
	print('\n')
	print(html_content) 
	print('\n')
	print("Check Telegram!") 
	db.close()

def insertDB(url="", timeAdded = "", photo_file_id="", photo_width=0, photo_height=0):
	global STRING_DB
	timestamp = round( datetime.datetime.now().timestamp() )
	db = postgresql.open(STRING_DB)
	ps = db.prepare("CREATE TABLE IF NOT EXISTS VistoNelWeb (id SERIAL PRIMARY KEY, url VARCHAR(300) UNIQUE, timestamp INT, timeAdded VARCHAR(25), done INT DEFAULT 0 );")
	ps()
	ps = db.prepare("INSERT INTO VistoNelWeb (url,timestamp,timeAdded,photo_file_id,photo_width,photo_height) VALUES ('{}','{}','{}','{}','{}','{}');".format(url, timestamp, timeAdded, photo_file_id, photo_width, photo_height) )
	ps()      
	db.close()

def getMyTimeZoneTime():
	nowTimestamp = round( datetime.datetime.now().timestamp() )
	utc_offset_heroku = time.localtime().tm_gmtoff 
	unix_timestamp = float(nowTimestamp)
	local_timezone = tzlocal.get_localzone() # get pytz timezone
	local_time = datetime.datetime.fromtimestamp(unix_timestamp, local_timezone)
	myLocalTimestamp = nowTimestamp + utc_offset_heroku 
	my_time = datetime.datetime.fromtimestamp(myLocalTimestamp, local_timezone)
	return my_time.strftime("%a %d %b %Y %H:%M")

def getMyTimeZoneTime():
	global HOUR_I_WANNA_GET_MESSAGE
	global MINUTES_I_WANNA_GET_MESSAGE
	utc_offset_heroku = time.localtime().tm_gmtoff / 3600
	hour = HOUR_I_WANNA_GET_MESSAGE + ( int(utc_offset_heroku) - 2 ) # 2 is my offset
	time2 = datetime.time(hour = hour , minute = MINUTES_I_WANNA_GET_MESSAGE, second = SECONDS_I_WANNA_GET_MESSAGE)
	return time2
	
def printUpdate(bot,update):
	timeAdded = getMyTimeZoneTime()
	if update.message.text:
		if update.message.entities:
			#print(update.message.entities[0], end='')
			text = update.message.text
			length = update.message.entities[0]['length']
			offset = update.message.entities[0]['offset']
			url = text[offset:(offset + length)]
			insertDB(url = url, timeAdded = timeAdded)
			print("Done inserting url", url)
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
updater.dispatcher.add_handler( MessageHandler( Filters.text | Filters.photo , callback = printUpdate) ) #Filters.entity("url")
j = updater.job_queue
'''
0 = Mon
1 = Tue
2 = Wed
...
6 = Sun
'''
j.run_daily(sendVnW, days=(2,), time = getMyTimeZoneTime() )

updater.start_polling()
updater.idle()