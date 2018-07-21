#!/usr/bin/env python

import os
from tornado import ioloop, web, template
from pymongo import MongoClient
from bson import json_util
import json
import requests
import logging

with open('config.json') as json_data_file:
    data = json.load(json_data_file)

db_data = data['database']
db_indexes = data['indexes']
app_config = data['application']
keys = data["keys"]
viewer = data['viewer']
viewer_alternate = data['viewer_alternate']
login = data['login']
j_security = data['j_security']
log_file = data['log_file_base']

MONGODB_DB_URL = 'mongodb://{}:{}/'.format(db_data['host'], db_data['port'])
MONGODB_DB_NAME = db_data['name']
client = MongoClient(MONGODB_DB_URL)
db = client[MONGODB_DB_NAME]

rotation = logging.handlers.RotatingFileHandler(
    log_file, maxBytes=20, backupCount=5)
formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s',
                              datefmt='%Y-%m-%d %H:%M:%S')

handler = logging.handlers.RotatingFileHandler(
    log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

for index in db_indexes:
    db.imagenology.create_index(index)


class IndexHandler(web.RequestHandler):
    def get(self):
        self.render("main.html")


class RepositoryHandler(web.RequestHandler):
    def get(self):
        validate = self.request.headers.get('X-Api-Key')
        status = {'status': 'Error'}
        if validate not in keys:
            self.write(status)
            return
        stories = []
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(list(stories), default=json_util.default))

    def post(self):
        validate = self.request.headers.get('X-Api-Key')
        status = {'status': 'Error'}
        if validate not in keys:
            self.write(status)
            return
        study_data = json.loads(self.request.body)
        story_id = db.imagenology.insert_one(study_data)
        status = {'status': 'Ok'}
        self.set_header("Content-Type", "application/json")
        self.set_status(201)
        self.write(status)


class PatientSearchHandler(web.RequestHandler):
    def get(self, patient_name):
        validate = self.request.headers.get('X-Api-Key')
        patient_name = '{}'.format(patient_name)
        status = {'status': 'Error'}
        if validate not in keys:
            self.write(status)
            return
        patients = db.imagenology.find({'patient_name': {'$regex': patient_name}})  # , {'text': 1, 'created_at': 1})
        try:
            user_agent = self.request.headers['User-Agent']
        except:
            user_agent = 'Unknown'
        remote_ip = self.request.remote_ip
        logger.info('{} : {} _ {} - {}'.format('Patient Name', patient_name, user_agent, remote_ip))
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(list(patients), default=json_util.default))


class PatientIdHandler(web.RequestHandler):
    def get(self, patient_id):
        validate = self.request.headers.get('X-Api-Key')
        patient_id = '{}'.format(patient_id)
        status = {'status': 'Error'}
        if validate not in keys:
            self.write(status)
            return
        studies = db.imagenology.find({"patient_id": patient_id})
        try:
            user_agent = self.request.headers['User-Agent']
        except:
            user_agent = 'Unknown'
        remote_ip = self.request.remote_ip
        logger.info('{} : {} _ {} - {}'.format('Patient ID', patient_id, user_agent, remote_ip))
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(list(studies), default=json_util.default))


class DescriptionHandler(web.RequestHandler):
    def get(self, patient_id):
        validate = self.request.headers.get('X-Api-Key')
        patient_id = '{}'.format(patient_id)
        status = {'status': 'Error'}
        if validate not in keys:
            self.write(status)
            return
        studies = db.imagenology.find({"study_description": patient_id})
        try:
            user_agent = self.request.headers['User-Agent']
        except:
            user_agent = 'Unknown'
        remote_ip = self.request.remote_ip
        logger.info('{} : {} _ {} - {}'.format('Patient ID', patient_id, user_agent, remote_ip))
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(list(studies), default=json_util.default))


class PatientStudiesHandler(web.RequestHandler):
    def get(self):
        arguments = self.request.arguments
        status = {'status': 'Error'}
        if 'patient_id' not in arguments or 'X-Api-Key' not in arguments:
            self.write(status)
            return
        patient_id = self.get_argument('patient_id')
        validate = self.get_argument('X-Api-Key')
        if validate not in keys:
            self.write(status)
            return
        studies = db.imagenology.find({"patient_id": patient_id},
                                      {"patient_id": 1, "patient_name": 1, "study_iuid": 1, "_id": 0,
                                       "study_datetime": 1})
        studies_data = []
        patient_name = ''
        for study in studies:
            studies_data.append(study)
            patient_name = study['patient_name']
        self.render("patient_studies.html", items=studies_data, patient_id=patient_id,
                    patient_name=patient_name, viewer=viewer, session_pacs=session_pacs)


class PatientStudiesAlternateHandler(web.RequestHandler):
    def get(self):
        arguments = self.request.arguments
        status = {'status': 'Error'}
        if 'patient_id' not in arguments or 'X-Api-Key' not in arguments:
            self.write(status)
            return
        patient_id = self.get_argument('patient_id')
        validate = self.get_argument('X-Api-Key')
        if validate not in keys:
            self.write(status)
            return
        studies = db.imagenology.find({"patient_id": patient_id},
                                      {"patient_id": 1, "patient_name": 1, "study_iuid": 1, "_id": 0,
                                       "study_datetime": 1})
        studies_data = []
        patient_name = ''
        for study in studies:
            studies_data.append(study)
            patient_name = study['patient_name']
        self.render("patient_studies_alternate.html", items=studies_data, patient_id=patient_id,
                    patient_name=patient_name, viewer=viewer_alternate, session_pacs=session_pacs)


def session_pacs(studyUID):
    data = {'j_username': 'user', 'j_password': 'user'}
    login = '{}{}'.format(viewer, studyUID)
    ses = requests.Session()
    ses.get(login)  # you need this to get cookies #
    post = ses.post(j_security, data=data)
    new_url = post.url
    # print(post.url)
    return new_url


settings = {
    "template_path": os.path.join(os.path.dirname(__file__), "templates"),
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    "debug": True
}

application = web.Application([
    (r'/', IndexHandler),
    (r'/index', IndexHandler),
    (r'/api/v1/register', RepositoryHandler),
    (r'/api/v1/patient_name/(.*)', PatientSearchHandler),
    (r'/api/v1/patient_id/(.*)', PatientIdHandler),
    (r'/api/v1/description/(.*)', DescriptionHandler),
    (r'/patient_studies', PatientStudiesHandler),
    (r'/patient_studies_alternate', PatientStudiesAlternateHandler),
], **settings)

if __name__ == "__main__":
    application.listen(app_config['port'])
    logger.info('Listening on http://localhost:%d' % app_config['port'])
    ioloop.IOLoop.instance().start()
