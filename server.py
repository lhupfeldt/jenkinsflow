from bottle import route, run, static_file, post, response
from jenkinsapi.jenkins import Jenkins
import json

jenkins_url = 'http://localhost:8080/'


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
    api = Jenkins(jenkins_url)
    simple_queue = []
    if len(api.get_queue()):
        for item in api.get_queue().values():
            print 'queue item: %s %s' % (type(item), item)
            job = api[item.task['name']]
            print 'job: %s %s' % (type(job), job)
            build = job.get_last_build_or_none()
            simple_queue.append({'job': job.name,
                                 'running': job.is_running(),
                                 'job_id': build.get_number()
                                 if build is not None else '???'})

    print 'DEBUG: simple_queue=', simple_queue
    response.content_type = 'application/json'
    return json.dumps(simple_queue)


@route('/jenkinsflow/flow_graph.json')
def graph_json():
    response.content_type = 'text'
    js = open('/var/www/jenkinsflow/flow_graph.json', 'r')
    return js
    # return static_file('flow_graph.json',
    #                    root='/var/www/jenkinsflow/')

run(host='localhost', port=9090)
