# Copyright 2019 Chaitanya Prakash N <cp@crosslibs.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#!/usr/bin/python

import sys
import time

import requests
from google.cloud import dns
from requests.exceptions import RequestException

METADATA_URL = 'http://metadata.google.internal/computeMetadata/v1'
METADATA_HEADERS = {
    'Metadata-Flavor': 'Google'
}
METADATA_QUERY_PARAMS = {
    'alt': 'text'
}
CHANGES_RELOAD_TIME_SECS = 2

def get_metadata(path):
    try:
        response = requests.get('{}/{}'.format(METADATA_URL, path),
                                params=METADATA_QUERY_PARAMS,
                                headers=METADATA_HEADERS)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print('Error occured while accessing metadata: {}'.format(e))
        raise e

def get_instance_details():
    return {
        'project': get_metadata('project/project-id'),
        'name': get_metadata('instance/name'),
        'ip': get_metadata('instance/network-interfaces/0/access-configs/0/external-ip'),
        'dns': {
            'project': get_metadata('instance/attributes/dns-project'),
            'zone': get_metadata('instance/attributes/dns-zone'),
            'ttl': get_metadata('instance/attributes/dns-ttl'),
            'domain': get_metadata('instance/attributes/dns-domain'),
        }
    }

def get_dns_zone(dns_project, dns_zone, dns_domain):
    zone = dns.Client(project=dns_project).zone(dns_zone, dns_name=dns_domain)
    if zone.exists():
        print('Zone {} exists.'.format(dns_zone))
    else:
        print('Zone {} does not exist.'.format(dns_zone))
        raise NameError('Zone {} does not exist.'.format(dns_zone))
    return zone

def update_record(changes):
    try: 
        changes.create()
        while changes.status != 'done':
            print('Waiting {} seconds for changes to complete'.format(CHANGES_RELOAD_TIME_SECS))
            time.sleep(CHANGES_RELOAD_TIME_SECS)
            changes.reload()
        print('DNS record updated successfully.')
    except Exception as e:
        print('Error while updating the DNS record: {}'.format(e))

def add_a_record(zone, name, domain, ttl, ip):
    record_set = zone.resource_record_set('{}.{}.'.format(name, domain), 'A', ttl, [ip])
    changes = zone.changes()
    changes.add_record_set(record_set)
    return changes

def delete_a_record(zone, name, domain, ttl, ip):
    record_set = zone.resource_record_set('{}.{}.'.format(name, domain), 'A', ttl, [ip])
    changes = zone.changes()
    changes.delete_record_set(record_set)
    return changes

def update_dns(command):
    instance = get_instance_details()
    print(instance)
    zone = get_dns_zone(instance['dns']['project'], instance['dns']['zone'], instance['dns']['domain'])
    changes = None
    if command == 'startup':
        changes = add_a_record(zone, instance['name'], instance['dns']['domain'], instance['dns']['ttl'], instance['ip'])
    elif command == 'shutdown':
        changes = delete_a_record(zone, instance['name'], instance['dns']['domain'], instance['dns']['ttl'], instance['ip'])
    else:
        print('Unknown command: {}'.format(command))
        raise ValueError('Unknown command: {}'.format(command))
    update_record(changes)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        update_dns(sys.argv[1])
    else:
        print('Invalid usage. Syntax: python3 {} <startup|shutdown>'.format(sys.argv[0]))