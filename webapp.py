#!/bin/python
import subprocess
import falcon
import json 
from wsgiref import simple_server
import os



class HomePage(object):
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = 'text/html'
        with open('html/index.html', 'r') as f:
            resp.body = f.read()

class Invenotry(object):
    def on_get(self, req, resp):
        data = os.listdir('inventory')
        data.sort() 
        resp.media = data 

class Applications(object):
    def set_title(self, fname):
        fname = fname.replace(".yml", "")
        fname = fname.replace("_", " ")
        return fname 

    def on_get(self, req, resp):
        data = os.listdir('apps')
        data.sort()
        rdata = []
        for names in data:
            if 'refresh.yml' == names.lower():
                continue  
            if names.endswith(".yml"):
                rdata.append([names,self.set_title(names)])
        resp.media = rdata 

class AnsibleResource(object):
    def run_command(self, command):
        p = subprocess.Popen(command,stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return iter(p.stdout.readline, b'')

    def update_hostentry(self, host_add):
        f = open('hosts','w')
        f.write(host_add)
        f.close()

    def run_ansible(self, host_ip,application_file):
        self.update_hostentry(host_ip)
        command = 'ansible-playbook -i hosts apps/'+application_file+' -u cloud'
        command = command.split()
        result = []
        for t in self.run_command(command): result.append(t)
        return result

    def on_post(self, req, resp):
        req_data = req.stream.read()
        req_json = json.loads(req_data)
        host_ip = req_json.get('host_ip','127.0.0.1')
        application = req_json.get('app','nothing.yml')
        result_str = self.run_ansible(host_ip, application)
        doc = {
            'host': host_ip,
            'app' : application,
            'result' : result_str
        }
        resp.body = json.dumps(doc, ensure_ascii=False)
        resp.status = falcon.HTTP_200



app = falcon.API()
app.req_options.auto_parse_form_urlencoded = True
app.add_route('/', HomePage())
app.add_route('/ansible/', AnsibleResource())
app.add_route('/inventory/', Invenotry())
app.add_route('/applications/', Applications())
# print  run_ansible('84.39.39.130', 'tomcat.yml')

if __name__ == '__main__':
    http = simple_server.make_server('0.0.0.0', 8003, app)
    http.serve_forever()
