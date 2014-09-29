import sys
import os
import time

if 'alexpb' not in os.getcwd():
	localServer = True
else:
	localServer = False
if localServer == False:
	INTERP = "/home/alexpb/bin/python2.6"
	if sys.executable != INTERP: os.execl(INTERP, INTERP, *sys.argv)
sys.path.append(os.getcwd())

import jsonBunch

import web, os, time, re, cgi, urllib, urllib2, json, string, zipfile, urlparse
import datetime


def log(*args):
	web.debug(args)


db = None


if not os.path.exists("ppsshots"):os.makedirs("ppsshots")
if not os.path.exists("crashs"):os.makedirs("crashs")

def loadDB():
	dbname = "db.json"
	if not os.path.isfile(dbname):
		output = open(dbname, 'w')
		output.write("{}")
		output.close()
	t = open('db.json', 'r').read()
	f = json.loads(t)
	globals()['db'] = jsonBunch.bunchify(f)
	jsonBunch.superself = globals()['db']
	jsonBunch.printer = web.debug

# log('database reloaded with:')
#log(globals()['db'])
#print('test')
#db = Shove('sqlite:///test.db')
loadDB()

urls = (
'/', 'home',
'/uploadLevel', 'uploadLevel',
'/uploadCrash', 'uploadCrash',
'/downloadLevel', 'downloadLevel',
'/queryLevels', 'queryLevels',
'/listLevels', 'listLevels',
'/createUser', 'createUser',
'/listLevel', 'listLevel',
'/downloadSS', 'downloadSS',
'/rateLevel', 'rateLevel',
'/(js|css|images|kee|ppsshots)/(.*)', 'static'
)

class static:
	def GET(self, media, file):
		try:
			f = open(media+'/'+file, 'r')
			return f.read()
		except:
			print "Unexpected error:", sys.exc_info()[0]
			print "looking for file: " + media+'/'+file
			return media+'/'+file # you can send an 404 error here if you want

def fail(input=None):
	return json.dumps({"result":"fail", "data":input})
def OK(input=None):
	return json.dumps({"result":"OK", "data":input})

def compareScores(b, a):
	return int(a[1]) - int(b[1])


class listLevel:
	def GET(self):
		i = web.input()
		if "levelid" in i:
			return OK(db.ppLevels[i.levelid])
		else:
			return fail("level not found")

class rateLevel:
	def GET(self):
		return OK(db.ppLevels)

'''class listScores:
	def GET(self):

		web.header("Content-Type", "text/html; charset=utf-8")

		#content.Add(H1('TEST'))
		i = web.input()
		print "db.scores =", db.scores
		if i.game not in db.scores:
			return ('Game Scores Not Found')
		#adding score
		if 'name' in i and 'score' in i and 'code' in i:
			db.scores[i.game].scores.append([i.name, int(i.score)])
			print str(db.scores[i.game].scores)
			db.scores[i.game].scores.sort(compareScores)
			db.sync()

		#print scores
		result = 'High scores for ' + db.scores[i.game].name + "\n"
		for score in db.scores[i.game].scores:
			result += score[0] + ": " + str(score[1]) + "\n"
		return (result)'''

class queryLevels:
	def POST(self):
		web.header("Content-Type", "text/html; charset=utf-8")
		i = web.input()
		print i
		result = []
		if "ppLevels" not in db:return fail("no levels in database!")
		for levelid in db.ppLevels:
			level = db.ppLevels[levelid]
			result.append(level)
		sortKey = "dateAdded"
		if "sortKey" in i:sortKey = i.sortKey
		print sortKey
		from operator import itemgetter
		print result
		#result = sorted(result, key=itemgetter(sortKey))
		#result = sorted(result, key=lambda k: k[sortKey])
		result.sort(key=itemgetter(sortKey))
		#result.sort(sortmethod)
		print result
		cursor = 0
		limit = 20
		if "cursor" in i:cursor = int(i.cursor)
		if "limit" in i:limit = int(i.limit)

		if "reverse" in i:result.reverse()
		print cursor, cursor+limit

		result = result[cursor:cursor+limit]

		print "returning: ", result
		return OK(result)


def pythonicVarName(field):
	firstLetter = True
	for word in field.split(' '):
		if firstLetter == False:
			wordCapped = str(word[0]).upper() + word[1:]
			id = id + wordCapped
		else:
			id = word.lower()
		firstLetter = False
	for i in string.punctuation:
		if i in id:
			id = id.replace(i, "")
	return id

def authUser(i):
	if "users" not in db: return "No user accounts! create one!"
	if i.author not in db.users:
		return "User " + i.author + " not Found! Create an account."
	user = db.users[i.author]
	print "passes:", user.passHash, i.passHash
	if user.passHash != i.passHash:
		return "Invalid Password!"
	return True

class uploadCrash:
	def POST(self):
		i = web.input()
		print "POST uploading crash"

		now = str(datetime.datetime.now())

		namepath = "crashs/" + now+"--" + str(i.version)
		output = open(namepath, 'wb')
		output.write(i.crashData)
		output.close()

		return OK("Success!")

class uploadLevel:
	def POST(self):
		i = web.input()
		print "POST uploading level"
		userResult = authUser(i)
		print userResult
		if userResult != True: return fail(userResult)

		fullname = pythonicVarName(i.author + i.name)

		namepath = "pplevels/" + fullname
		output = open(namepath, 'wb')
		output.write(i.levelData)
		output.close()

		import base64
		ssdata = base64.b64decode(i.sshot)
		namepath = "ppsshots/" + fullname+".png"
		output = open(namepath, 'wb')
		output.write(ssdata)
		output.close()

		newLevel = {}
		isNew = True
		if "ppLevels" not in db:
			db.ppLevels = {}
		try:
			newLevel = db.ppLevels[fullname]
			isNew = False
		except KeyError:
			pass
		newLevel['name'] = i.name
		newLevel['author'] = i.author
		newLevel['filename'] = fullname
		now = str(datetime.datetime.now())
		nowStamp = time.time()
		if (isNew):
			newLevel['rating'] = 2.5
			newLevel['ratingCount'] = 0
			newLevel['dateAdded'] = nowStamp
			newLevel['downloads'] = 0
		newLevel['dateModified'] = nowStamp
		newLevel['description'] = "description"
		newLevel['screenshot'] = "none"
		db.ppLevels[fullname] = newLevel
		return OK("Success!")


class listLevels:
	def GET(self):
		return OK(json.dumps(db.ppLevels))

	def POST(self):
		reval = json.dumps(db.ppLevels)
		return OK(retval)
		'''levelList = []
		for lI in db.ppLevels:
			level = db.ppLevels[lI]
			levelList.append([level.name, level.filename])
		return json.dumps(levelList)'''


class downloadSS:
	def GET(self):
		#image/png
		web.header("Content-Type", "image/png")
		i = web.input()
		namepath = "ppsshots/" + i.fullname
		return open(namepath, 'r').read()

class downloadLevel:
	def POST(self):
		i = web.input()
		print i
		if "fullname" in i:
			fullname = i.fullname
		else:
			#userResult = authUser(i)
			#print userResult
			#if userResult != True: return fail(userResult)

			fullname = pythonicVarName(i.author + i.name)
		if fullname in db.ppLevels:
			db.ppLevels[fullname].downloads+=1
			namepath = "pplevels/" + fullname
			return OK(open(namepath, 'r').read())
		else:
			return fail("level not found")

def makeUser(name,passHash):
		user = {}
		user['name'] = name
		user['passHash'] = passHash
		db.users[name] = user


class createUser:
	def POST(self):
		i = web.input()
		name = i.userName
		passHash = i.passHash
		if "users" not in db:
			db.users = {}
		if name in db.users:
			user = db.users[name]
			if user.passHash == i.passHash:
				return OK("Password Matches - You can upload!")
			return fail("User Exists with different password.")
		if "creating" in i and i.creating == "false":
			return fail("Account not found")
		makeUser(name,passHash)
		return OK("Account " + name + " created!")


class home:
	def GET(self):
		web.header("Content-Type", "text/html; charset=utf-8")
		#content = contentBaseDiv()
		#content.add("test")
		#return templateOrMinimal(content)
		return open("kee/index.html", 'r').read()
		#return OK("basic Functions working on kivented server")

	#return db.scores
	def POST(self):
		i = web.input()
		print i
		return OK()

#from paste.exceptions.errormiddleware import ErrorMiddleware
if localServer == False:
	app = web.application(urls, globals(), autoreload=False)
	application = app.wsgifunc()
#def application(environ, start_response):
#write = start_response('200 OK', [('Content-type', 'text/plain')])
#return ["Hello then, world!"]
#return applicationc.wsgi(environ,start_response)
else:
	if __name__ == "__main__":
		app = web.application(urls, globals(), autoreload=True)
		app.run()
