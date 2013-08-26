from bottle import route, run, static_file, post, response
import requests


@route('/jenkinsflow/graph')
def index():
    return static_file('flow_vis.html', root='./')


@route('/jenkinsflow/js/<filename>')
def js(filename):
    return static_file(filename, root='./js/')


@post('/jenkinsflow/builds')
def builds():
    # TODO: change this to jenkinsapi call because this url
    # returns html table, and we only need job names and state of the build
    return requests.get('http://localhost:8080/ajaxBuildQueue')


@route('/jenkinsflow/flow_graph.json')
def graph_json():
    response.content_type = 'text'
    js = open('/var/www/jenkinsflow/flow_graph.json', 'r')
    return js
    # return static_file('flow_graph.json',
    #                    root='/var/www/jenkinsflow/')

run(host='localhost', port=9090)
