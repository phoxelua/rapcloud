import sqlite3
from os import listdir
from os.path import isfile, join
import sys
import re
import json
from sets import Set
import operator

SKIP_THESE_WORDS = ['a', "ain't", 'am', 'and', 'as', 'be', 'but', 'do', "don't", 'for', 'from', 'girl', 'get', 'got', 'how' ,'had', 'i', "i'm", 'if', 'in', 'is', 'it', "it's", 'its', 'like', 'me', 'my', 'of', 'on', 'that', 'the', 'them', 'they', 'this', 'to', 'too', 'wanna', 'want', 'was', 'we', 'were', 'what', 'when', 'with', 'you', "you're", 'your']


	# SKIP_THESE_WORDS = ['all', 'just', 'being', 'over', 'both', 'through', 'yourselves', 'its', 'before', 'herself', 'had', 'should', 'to', 'only', 'under', 'ours', 'has', 'do', 'them', 'his', 'very', 'they', 'not', 'during', 'now', 'him', 'nor', 'did', 'this', 'she', 'each', 'further', 'where', 'few', 'because', 'doing', 'some', 'are', 'our', 'ourselves', 'out', 'what', 'for', 'while', 'does', 'above', 'between', 't', 'be', 'we', 'who', 'were', 'here', 'hers', 'by', 'on', 'about', 'of', 'against', 's', 'or', 'own', 'into', 'yourself', 'down', 'your', 'from', 'her', 'their', 'there', 'been', 'whom', 'too', 'themselves', 'was', 'until', 'more', 'himself', 'that', 'but', 'don', 'with', 'than', 'those', 'he', 'me', 'myself', 'these', 'up', 'will', 'below', 'can', 'theirs', 'my', 'and', 'then', 'is', 'am', 'it', 'an', 'as', 'itself', 'at', 'have', 'in', 'any', 'if', 'again', 'no', 'when', 'same', 'how', 'other', 'which', 'you', 'after', 'most', 'such', 'why', 'a', 'off', 'i', 'yours', 'so', 'the', 'having', 'once']

def lcs(s1,s2):
	m = len(s1)
	n = len(s2)
	array = [[0 for x in range(n)] for x in range(m)] 
   	z = 0

   	commons = Set()

   	for i in range(0,m):
   		for j in range(0,n):
   			if s1[i] == s2[j]:
   				if i==0 or j==0:
   					array[i][j] = 1
   				else:
   					array[i][j] = array[i-1][j-1] + 1

   				if array[i][j] > z:
   					z = array[i][j]
   					commons.add(s1[i-z+1:i+1])
   				elif array[i][j] == z:
   					commons = commons.union(Set([s1[i-z+1:i+1]]))
			else:
				array[i][j] = 0

   	ret = {}
   	for sub_seq in commons:
   		if len(sub_seq) > 1:
   			st = " ".join(sub_seq)
   			ret[st] = 1
   	# print ret
   	return ret

def aggregate(old, new):
	for k in new.keys():
		if k in old.keys():
			old[k] += new[k]
		else:
			old[k] = new[k]
	return old

def make_table(db_name):
	conn = sqlite3.connect(db_name)
	c = conn.cursor()
	c.execute('''CREATE TABLE music (artist_name text, lyrics text, word_counts text, phrase_counts text)''')
	conn.commit()
	conn.close()

def normalize_line(line):
	# print line
	while ('[' in line) and (']' in line):
		line = line.split('[', 1)[0] + line.split(']', 1)[1]
	while ('(' in line) and (')' in line):
		line = line.split('(', 1)[0] + line.split(')', 1)[1]

	for p in [("(", ")"), ("[", "]")]:
		if p[0] in line and p[1] in line:
			print 'we fucked up somehow'

	# print line
	punct = ["?", "!", ",", "."]

	for p in punct:
		line = line.replace(p, '')

	return line.lower().replace('"', "'").decode('utf-8').replace(u'\u2019', "'").replace(u'\u2018', "'")

def normalize_data(filename):
	lines = [normalize_line(line) for line in open(filename)]
	return ' '.join(" ".join(lines).split()), lines

def insert_rows(dict, db_name):
	conn = sqlite3.connect(db_name)
	c = conn.cursor()
	c.execute('delete from music;');
	for k in dict.keys():
		row = dict[k]
		c.execute('''INSERT INTO music VALUES ((?), (?), (?), (?))''', (k, row[0], row[1], row[2]))
	conn.commit()
	conn.close()	

def count_words(data):

	counts = {}

	for word in data.split():
		if word in SKIP_THESE_WORDS:
			continue
		if word in counts.keys():
			counts[word] += 1
		else:
			counts[word] = 1

	max_count = max(counts.values());
	for word in counts.keys():
		if counts[word] < .05*max_count:
			del counts[word]
	total = sum(counts.values())
	d = len(counts.values())

	alpha = 1
	multiplier = 150 * (total + d*alpha) / (max_count + alpha)


	formated_counts = []

	for word in counts.keys():
		s = multiplier*(counts[word] + alpha) / (total + d*alpha)
		if s < 20:
			continue
		formated_counts.append({"text": word, "size": s})

	return json.dumps(formated_counts[:25], separators=(',', ':')).replace('"', '\"')

def all_ignore_words(words):
	all_ignore = True
	for word in words.split():
		if word not in SKIP_THESE_WORDS:
			all_ignore = False
			break
	return all_ignore

def is_subset(p, all_p):
	is_sub = False
	for a in all_p:
		if p in a and p != a:
			is_sub = True
			break
	return is_sub


def normalize_phrases(phrases):

	norm_phrases = []
	all_p = [p[0] for p in phrases]

	print all_p

	for phrase in phrases:
		p = phrase[0]
		if not all_ignore_words(p) and not is_subset(p, all_p):
			norm_phrases.append(phrase)
	return norm_phrases

def get_phrase_counts(lyrics, phrases):

	counts = []

	for phrase in phrases:
		if len(phrase) >= 20:
			continue
		if phrase in lyrics:
			counts.append({"text": phrase, "size": lyrics.count(phrase)})

	max_count = max([c["size"] for c in counts]);
	for word in list(counts):
		if word["size"] < .05*max_count:
			counts.remove(word)
	total = sum([c["size"] for c in counts])
	d = len(counts)

	alpha = .5
	multiplier = 75 * (total + d*alpha) / (max_count + alpha)

	formated_counts = []

	for word in counts:
		s = multiplier*(word["size"] + alpha) / (total + d*alpha)
		if s < 10:
			continue
		word["size"] = s
		formated_counts.append(word)


	# print phrase_counts
	# return phrase_counts
	return json.dumps(formated_counts, separators=(',', ':')).replace('"', '\"')

if __name__ == "__main__":

	path = "/Users/jawon/swagking/artists/"
	artists = [ f.replace('.txt', '') for f in listdir(path) if isfile(join(path,f)) ]
	db_name = "swag.db"

	# print artists
	temp_dict = {}
	artist_lines = {} #artist-lines array dict

	for artist in artists:
		data = normalize_data(path + artist + ".txt")
		counts = count_words(data[0])
		#add lyrics, count, lcs count
		temp_dict[artist] = [data[0], counts, {}]
		artist_lines[artist] = data[1]


	longest_common = {}

	# find most frequent longest-common-subseq for each artist
	# for artist in artist_lines.keys():
	# 	for lin1 in artist_lines[artist]:
	# 		line1 = tuple(lin1.split())
	# 		for lin2 in artist_lines[artist]:
	# 			line2 = tuple(lin2.split())
	# 			if line1 != line2:
	# 				if artist in longest_common.keys():
	# 					longest_common[artist] = aggregate(longest_common[artist],lcs(line1, line2))
	# 				else:
	# 					longest_common[artist] = lcs(line1, line2)
	# 	print longest_common

	# with open(artist, 'w') as outfile:
	# 	json.dump(longest_common, outfile)
	for artist in artist_lines.keys():
		with open('phrases/' + artist, 'r') as inputfile:
			longest_common[artist] = json.load(inputfile)[artist]

	# print longest_common.keys()

	norm_phrases = {}

	for artist in longest_common.keys():
		sorted_lcss = sorted(longest_common[artist].iteritems(), key=operator.itemgetter(1), reverse=True)
		norm_phrases[artist] = normalize_phrases(sorted_lcss)
		norm_phrases[artist] = norm_phrases[artist][:(min(len(norm_phrases[artist])/4, 15))]

	for artist in temp_dict.keys():
		temp_dict[artist][2] = get_phrase_counts(temp_dict[artist][0], [p[0] for p in norm_phrases[artist]])

	if len(sys.argv) > 1:
		make_table(sys.argv[1])
	else:
		# pass
		insert_rows(temp_dict, db_name)


