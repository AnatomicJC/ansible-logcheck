import re
import datetime
import gzip
import json
from requests import post
from requests.exceptions import ConnectionError
from os import remove
import sys

class logcheck2ES:
  def __init__(self):
    self.regexp = "(^\w{3} [ :\d]{11}) ([._\w-]+) ([._\w-]*)\[([\d]+)\]: (.*)"
    self.data = []
    with open('es-credentials.json') as handle:
      self.es = json.loads(handle.read())

  def send(self, filename):
    with gzip.open(filename) as f:
      for line in f.readlines():
        try:
          z = re.search(self.regexp, line.decode("utf-8"))
          doc = json.dumps({
              'timestamp': datetime.datetime.strptime('{} {}'.format(datetime.datetime.now().year, z.group(1)), '%Y %b %d %H:%M:%S').strftime('%Y-%m-%dT%H:%M:%S'),
              'hostname': z.group(2),
              'service': z.group(3),
              'process_id': z.group(4),
              'message': z.group(5)
            })
    
          self.data.append(json.dumps({'index': {}}))
          self.data.append(doc)
          index = datetime.datetime.strptime('{} {}'.format(datetime.datetime.now().year, z.group(1)), '%Y %b %d %H:%M:%S').strftime('logcheck-%Y.%m.%d')
    
        except AttributeError:
          pass
    
    # Bulk request must be terminated by a new line
    self.data.append('\n')
    
    try:
      r = post(
        '{}/{}/_bulk/'.format(self.es['uri'], index),
        data='\n'.join(self.data),
        auth=(self.es['user'], self.es['password']),
        headers={'content-type': 'application/json'}
      )
    except ConnectionError as e:
      print(e)
      sys.exit(1)
    
    if r.ok:
      remove(filename)
    else:
      print("Return code: {}".format(r.status_code))
      print("Msg: {}".format(r.text))
      sys.exit(1)

if __name__ == "__main__":
  if len(sys.argv) != 2:
    print("You must specify one logcheck report to send to elasticsearch")
    sys.exit(1)
  logcheck2ES().send(sys.argv[1])
