import cPickle as pickle

infile = open("../legacydb/dumps/posts.dump", 'r')
posts = pickle.load(infile)
print posts
infile.close()
