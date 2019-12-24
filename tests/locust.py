# locustfile.py
from locust import HttpLocust, task, TaskSet


class UserBehavior(TaskSet):

    def on_start(self):
        self.login()
    def login(self):
        # GET login page to get csrftoken from it
        response = self.client.get('/login')
        # POST to / page with csrftoken
        self.client.post('/',data=dict(search="asus"))
        self.client.post('/',data=dict(search="lenoko"))
        self.client.post('/', data=dict(search="apple"))
        self.client.post('/', data=dict(search="şşş"))
        self.client.post('/', data=dict(search="apple 8gb"))
        self.client.post('/', data=dict(search="dell"))
        self.client.post('/', data=dict(search="lenovo"))
        self.client.post('/', data=dict(search="hp"))
        self.client.get('/selectingAttribute')
        self.client.get('/register')
        self.client.get('/contact')
    @task(1)
    def index(self):
        self.client.get('/')

class WebsiteUser(HttpLocust):
    task_set = UserBehavior
