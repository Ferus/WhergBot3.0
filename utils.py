#! /usr/bin/env python

def truncate(content, length=300, suffix='...'):
	if len(content) <= length:
		return content
	else:
		if content[-1] == suffix[0]:
			content = content[0:-1]
		x = ' '.join(content[:length+1].split(' ')[0:-1]) + "{0}".format(suffix)
		return x
