#!/usr/bin/env Python3

import urllib.request
import json
#fixes formatting
import pprint

key = 'AIzaSyBilR_bODNKMrYLnTYozcW6-6e7K37VoxM'
request = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?'

parameters = 'location=-33.8670,+151.1957&radius=500&types=food&name=cruise&key=%s' % (key)

request = request + parameters

url_response = urllib.request.urlopen(request).read()
directions = json.loads(url_response)

pprint.pprint(directions)


