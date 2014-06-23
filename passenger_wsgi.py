import sys
import os

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


def loadDB():
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
'/downloadLevel', 'downloadLevel',
'/listLevels', 'listLevels',
'/createUser', 'createUser',
'/listLevel', 'listLevel'
'/rateLevel', 'rateLevel',
)

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
	user = None
	try:
		user = db.users[i.author]
	except KeyError:
		return "User " + i.author + " not Found! Create an account."
		pass
	print "passes:", user.passHash, i.passHash
	if user.passHash != i.passHash:
		return "Invalid Password!"
	return True

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
		if (isNew):
			newLevel['rating'] = 2.5
			newLevel['ratingCount'] = 0
			newLevel['dateAdded'] = now
			newLevel['downloads'] = 0
		newLevel['dateModified'] = now
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


class createUser:
	def POST(self):
		i = web.input()
		name = i.userName
		passHash = i.passHash
		if "users" not in db:
			db.users = {}
		try:
			user = db.users[name]
			if user.passHash == i.passHash:
				return OK("Password Matches - You can upload!")
			return fail("User Exists with different password.")
		except KeyError:
			pass
		if i.creating == "false":
			return fail("Account not found")
		user = {}
		user['name'] = name
		user['passHash'] = passHash
		db.users[name] = user
		return OK("Account " + name + " created!")


class home:
	def GET(self):
		#content = contentBaseDiv()
		#content.add("test")
		#return templateOrMinimal(content)
		return OK("basic Functions working on kivented server")

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
