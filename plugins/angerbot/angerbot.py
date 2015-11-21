import time
import tweepy
import sys
import aiml

# define all our variables
crontable = []
outputs = []

# define twitter streaming listener
class MyStreamListener(tweepy.StreamListener):
	def on_error(self, status_code):
		outputs.append([ channelId, "OH SHIT WE GOT AN ERROR FROM THE STREAM [ "+str(status_code)+" ]" ])
		# TODO: since we are going to disconnect we should probably reset our follow list/keyword list
		return False # returning False disconnects the stream to prevent making the rate limit problem worse

	def on_status(self, status):
		print(status)
		if len(channelId) > 0:
			if ("@"+status.author.screen_name) in stream_manager.usersToFollow:
				outputs.append([ channelId, "@"+status.author.screen_name+" said '"+status.text+"'" ])
			else:
				outputs.append([ channelId, "Hey I just heard someone say '"+status.text+"'" ])

class TwitterStreamManager:
	def __init__(self):
		self.user_session_table = []
		self.keywordsToWatch = []
		self.usersToFollow = []
		self.connected = False

		self.auth = tweepy.OAuthHandler("", "")
		self.auth.set_access_token("", "")
		self.api = tweepy.API(self.auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
		self.stream_listener = MyStreamListener()
		self.myStream = tweepy.Stream(auth = self.auth, listener=self.stream_listener)

	def set_streaming_filter(self):
		# we need to convert all our followed screen names into actual twitter ids here
		# TODO: add some error checking to ensure we get back only good id's
		twitter_user_ids_to_follow = []
		for element in self.usersToFollow:
			twitter_user_ids_to_follow.append( str(self.api.get_user(element).id) )

		# now we need to turn our lists of keywords and twitter ids we're following into strings to pass into the filter
		track_str = ','.join(str(element) for element in self.keywordsToWatch)
		follow_str = ','.join(str(element) for element in twitter_user_ids_to_follow)

		if self.connected:
			print("DISCONNECTING FROM STREAM")
			self.myStream.disconnect()
			self.connected = False

		if len(track_str) > 0 and len(follow_str) > 0:
			print ("SETTING STREAM FILTER WITH track:"+track_str+" and follow: "+follow_str)
			self.myStream.filter(track=[track_str], follow=[follow_str], async=True)
			self.connected = True
		elif len(track_str) > 0 and len(follow_str) == 0:
			print ("SETTING STREAM FILTER WITH track:"+track_str)
			self.myStream.filter(track=[track_str], async=True)
			self.connected = True
		elif len(track_str) == 0 and len(follow_str) > 0:
			print ("SETTING STREAM FILTER WITH follow: "+follow_str)
			self.myStream.filter(follow=[follow_str], async=True)
			self.connected = True
		else:
			print ("We are no longer following or tracking anything on twitter.")

	def add_followed_user(self,twitter_screen_name):
		if twitter_screen_name not in self.usersToFollow:
			self.usersToFollow.append(twitter_screen_name)
			self.set_streaming_filter()
		return

	def stop_following_user(self,twitter_screen_name):
		if self.connected:
			if twitter_screen_name in self.usersToFollow:
				self.usersToFollow.remove(twitter_screen_name)
				self.set_streaming_filter()
				return 1
		else:
			print ("NOT FOLLOWING ANYONE RIGHT NOW")
			return -1

	def add_filter(self,keyword):
		if keyword not in self.keywordsToWatch:
			self.keywordsToWatch.append(keyword)
			self.set_streaming_filter()
		return

	def remove_filter(self,keyword):
		if self.connected:
			if keyword in self.keywordsToWatch:
				self.keywordsToWatch.remove(keyword)
				self.set_streaming_filter()
				return 1
		else:
			print ("NOT WATCHING ANYTHING RIGHT NOW")
			return -1

	def extract(self, keyword, data):
		keylen = len(keyword)
		initialpos = data.find(keyword)
		startidx = data.find(" ", initialpos+keylen)
		startidx = startidx + 1
		if data.find(" ", startidx) != -1:
			endidx = data.find(" ", startidx)
		else:
			endidx = len(data)
		ret_val = ""
		if startidx != 0:
			ret_val = data[startidx:endidx]
		return ret_val

	def get_keyword(self,data):
		return self.extract("filter",data)

	def get_id_from_name(self,username):
		if username not in self.user_session_table:
			self.user_session_table.append(username)
		return self.user_session_table.index(username)

	def get_twitter_handle(self,data):
		return self.extract("follow",data)

	def get_latest_tweets(self, twitter_username):
		return self.api.user_timeline(twitter_username)

	def get_rate_limit_status(self):
		return api.rate_limit_status()

def load_ai():
	global ai_kernel
	ai_kernel = aiml.Kernel()
	ai_kernel.learn("std-startup.xml")
	ai_kernel.respond("load aiml b")
	return

# run this to kick it all off
load_ai()
stream_manager = TwitterStreamManager()

def process_message(data):
	global channelId
	channelId = data['channel']
	if "<@U0EGJE77D>" in data['text']:
		if "talk dirty" in data['text']:
			outputs.append([data['channel'], "i don't talk dirty to filthy scrubs like you!"])
		elif "love" in data['text']:
			outputs.append([data['channel'], "you digust me <@"+data['user']+">"])
		elif "ops" in data['text']:
			outputs.append([data['channel'], "I'm currently following: "+str(stream_manager.usersToFollow)])
			outputs.append([data['channel'], "I'm currently watching for mentions of: "+str(stream_manager.keywordsToWatch)])
		elif "get latest from" in data['text']:
			twitter_username = stream_manager.extract("get latest from",data['text'])
			if len(twitter_username) > 0:
				public_tweets = stream_manager.get_latest_tweets(twitter_username)
				outputs.append([ data['channel'], twitter_username+' latest tweet: '+public_tweets[0].text ])
			else:
				outputs.append([ data['channel'], "i don't know what you want from me" ])
		elif "tw_status" in data['text']:
			rate_limit_status = stream_manager.get_rate_limit_status()
			outputs.append([ data['channel'], "My twitter rate limits are "+str(rate_limit_status) ])
		elif "unfollow" in data['text']:
			twitter_screen_name = stream_manager.get_twitter_handle(data['text'])
			if len(twitter_screen_name) > 0:
				stream_manager.stop_following_user(twitter_screen_name)
				outputs.append([data['channel'], twitter_screen_name+"? that was a boring account anyway"])
			else:
				outputs.append([data['channel'], "who did you want me to stop following??"])
		elif "follow" in data['text']:
			print "follow start"
			twitter_screen_name = stream_manager.get_twitter_handle(data['text'])
			print "follow user: "+twitter_screen_name
			if len(twitter_screen_name) > 0:
				stream_manager.add_followed_user(twitter_screen_name)
				outputs.append([data['channel'], "ok i'll grudgingly watch "+twitter_screen_name+"'s twitter feed"])
			else:
				outputs.append([data['channel'], "who did you want me to follow??"])	
		elif "add filter" in data['text']:
			keyword_to_add = stream_manager.get_keyword(data['text'])
			if len(keyword_to_add) > 0:
				stream_manager.add_filter(keyword_to_add)
				outputs.append([data['channel'], "ok i'll keep an eye out for "+keyword_to_add])
			else:
				outputs.append([data['channel'], "i didn't catch that"])
		elif "remove filter" in data['text']:
			keyword_to_remove = stream_manager.get_keyword(data['text'])
			if len(keyword_to_remove) > 0:
				result = stream_manager.remove_filter(keyword_to_remove)
				if result == -1:
					outputs.append([data['channel'], "i'm not watching anything right now"])
				else:
					outputs.append([data['channel'], keyword_to_remove+"? that shit was boring anyway"])
			else:
				outputs.append([data['channel'], "i didn't catch that"])
		else:
			# the user said something to angerbot but it's not specific, lets shunt it to the AI
			# print data['text']
			user_query = data['text'][data['text'].find(":"):len(data['text'])]
			user_session_id = stream_manager.get_id_from_name(data['user'])
			outputs.append([data['channel'], ai_kernel.respond(user_query, user_session_id)])
