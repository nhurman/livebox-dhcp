#!/usr/bin/env python3

import json
import requests

from pprint import pprint

class Error(Exception): pass

class StaticLease:
  def __init__(self, mac=None, ipv4=None):
    self.mac = mac
    self.ipv4 = ipv4

  def __str__(self):
    return self.mac + ' => ' + self.ipv4

  def __repr__(self):
    return 'StaticLease({})'.format(self)

  def __eq__(self, other):
    return self.mac == other.mac and self.ipv4 == other.ipv4

class Livebox:
  def __init__(self, base_url):
    self.base_url = base_url
    self.token = None
    self.cookies = None

  def authenticate(self, username, password):
    url = self.base_url + '/authenticate'
    params = {'username': username, 'password': password}

    r = requests.post(url, params=params)
    j = r.json()

    self.token = j['data']['contextID'] if j['status'] is 0 else None
    self.cookies = r.cookies
    return self.token

  def send_request(self, url, params={}):
    headers = {'X-Context': self.token}
    data = {'parameters': params}
    r = requests.post(self.base_url + url, headers=headers, data = json.dumps(data), cookies=self.cookies)
    return r.json()

  def get_static_leases(self):
    j = self.send_request('/sysbus/DHCPv4/Server/Pool/default:getStaticLeases')

    leases = []
    for lease in j['status']:
      l = StaticLease()
      l.ipv4 = lease['IPAddress']
      l.mac = lease['MACAddress']
      leases.append(l)
    return leases

  def add_static_lease(self, lease):
    j = self.send_request('/sysbus/DHCPv4/Server/Pool/default:addStaticLease', {'IPAddress': lease.ipv4, 'MACAddress': lease.mac})
    if 'errors' in j: raise Error(j)

  def del_static_lease(self, lease):
    j = self.send_request('/sysbus/DHCPv4/Server/Pool/default:deleteStaticLease', {'MACAddress': lease.mac})
    if 'errors' in j: raise Error(j)

##
## Connect to the Livebox and update the DHCP static leases
##

lb = Livebox('http://livebox-ip')
lb.authenticate('admin', 'password')

current_leases = lb.get_static_leases()
final_leases = (
  StaticLease('00:01:02:03:04:05', '1.2.3.4'),
  StaticLease('00:01:02:03:04:06', '1.2.3.5'),
)

# Purge old ones
for lease in current_leases:
  if lease not in final_leases:
    print('Deleting', lease)
    lb.del_static_lease(lease)

# Add new ones
for lease in final_leases:
  if lease not in current_leases:
    print('Adding', lease)
    lb.add_static_lease(lease)

# Print final table
pprint(lb.get_static_leases())
