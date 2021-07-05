import urllib2

req = urllib2.Request('https://44670.org/ota/ota.json', headers={ 'User-Agent': '44IoT' })
html = urllib2.urlopen(req).read()
print(html)