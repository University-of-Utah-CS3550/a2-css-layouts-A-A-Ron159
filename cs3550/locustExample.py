from locust import HttpUser, between, task

class WebsiteUser(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        self.client.post("/login",
                         json={"username":"foo",
                               "password":""})
    

    @task
    def top_level(self):
        self.client.get("http://127.0.0.1:8000/")