#!/usr/bin/env python

# Copyright (c) 2015 Aleksey Maksimov and Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import os
from os.path import join as jp
import json
import argparse

import requests
from bottle import route, run, static_file, post, response

_HERE = os.path.abspath(os.path.dirname(__file__))

_json_dir = '/var/www/jenkinsflow/'
jenkins_url = 'http://localhost:8080/'


@route('/jenkinsflow/graph')
def index():
    return static_file('flow_vis.html', root=_HERE)


@route('/jenkinsflow/js/<filename>')
def js(filename):
    return static_file(filename, root=jp(_HERE, 'js'))


@route('/jenkinsflow/stylesheets/<filename>')
def stylesheets(filename):
    return static_file(filename, root=jp(_HERE, 'stylesheets'))


@post('/jenkinsflow/builds')
def builds():
    rsp = requests.get(jenkins_url + 'queue/api/json')
    response.content_type = 'application/json'
    return json.dumps(rsp.json())


@post('/jenkinsflow/build/<name>')
def job(name):
    rsp = requests.get(jenkins_url + 'job/' + name + '/api/json')
    response.content_type = 'application/json'
    return json.dumps(rsp.json())


@route('/jenkinsflow/flow_graph.json')
def graph_json():
    response.content_type = 'text'
    return open(jp(_json_dir, 'flow_graph.json'), 'r', encoding="utf-8")
    # return static_file('flow_graph.json', root=_json_dir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Serve flow graph.')
    parser.add_argument('--hostname', default='localhost', help='hostname to listen on')
    parser.add_argument('--port', default=9090, help='port to listen on')
    parser.add_argument('--json-dir', default=_json_dir, help='Where to find json flow graph')
    args = parser.parse_args()
    _json_dir = args.json_dir

    run(host=args.hostname, port=args.port, debug=True)
