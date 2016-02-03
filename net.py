#encoding: UTF-8

import os
import re
import tweepy
import config
import re as regexp
from random import randint
from IPython import embed # call embed() anywhere to debug code

## Ping:19.251msDownload:       28.81 Mbit/s Upload   :  3.04 Mbit/s
## Ping:19.251msDownload:28.81Mbit/sUpload:3.04Mbit/s
## Ping:19.251ms\nDownload:28.81Mbit/s\nUpload:3.04Mbit/s
## Ping:19.251\nDownload:28.81\nUpload:3.04
## Ping:19.251Download:28.81Upload:3.04
## Ping:19.251 Download:28.81 Mbit/s Upload:3.04
## Ping:19.251Download:28.81Upload:3.04
## Ping:19.0\nDownload  :28.81  Mbit/sUpload:3.04
## Ping: 19.0\nDownload: 28.81\nUpload: 3.04

LOG_PATTERN = '\s*(Ping)\s*:\s*(\d+.\d+)\s*(ms)?\n?\s*(Download)\s*:\s*(\d+.\d+)\s*(Mbit\/s)?\s*\n?\s*(Upload)\s*:\s*(\d+.\d+)\s*(Mbit\/s)?\s*\n?'

def main():
  try:
    run_test()
    results = parse_results()
    post_results_in_twitter(results)
  except:
    return

def post_results_in_twitter(results):
  status_message = mount_status(results)

  try:
    twitter = authenticate()
    twitter.update_status(status_message)
  except:
    print 'Error posting message in Twitter timeline (see config.py)'
  finally:
    print "Message: %s" % (status_message)

def run_test():
  print 'collecting internet speed data(this can take a while depending on your connection speed)\n'
  os.system('speedtest-cli --simple > net.log')

def parse_results():
  log = open('net.log')
  log_data = log.read()

  ping, down_speed, up_speed = None, None, None

  try:
    # make sure that system can read speedtest-cli output in different formats
    matches = regexp.findall(regexp.compile(LOG_PATTERN), log_data)[0]

    ping, down_speed, up_speed = map(float, [matches[1], matches[4], matches[7]])
  except:
      print '[Critical] Error parsing .net log file. Check if file content is valid and match LOG_PATTERN'
      exit()

  return [
    ping,
    down_speed,
    (down_speed * 100 / config.down_speed),
    up_speed,
    (up_speed * 100 / config.up_speed)
  ]

def authenticate():
  auth = tweepy.OAuthHandler(config.twitter_consumer_key, config.twitter_consumer_secret)
  auth.set_access_token(config.twitter_access_key, config.twitter_access_secret)
  return tweepy.API(auth)

def mount_status(results):
  return config.twitter_message % (
    results[1], # download speed
    results[2], # download (%)
    results[3], # upload speed
    results[4], # upload (%s)
    results[0], # ping
    final_message(results[2], results[4]) # random final message
  )

def satisfy(down, up, connection_status):
  check_valid_connection_status(connection_status)

  speeds = config.speeds[connection_status]
  up_speed, down_speed = speeds

  return (down > down_speed and up > up_speed)

def get_message(connection_status):
  check_valid_connection_status(connection_status)

  messages = config.messages[connection_status]
  message = messages[randint(0, (len(messages) -1))]

  return message

def check_valid_connection_status(connection_status):
  if not config.speeds.has_key(connection_status):
    raise ValueError("invalid connection_status: %s" % (connection_status))

  return True

def final_message(current_down, current_up):
  for connection_status in config.speeds.keys():
    if satisfy(current_down, current_up, connection_status):
      return get_message(connection_status)
    else:
      return get_message('shit')

main()
