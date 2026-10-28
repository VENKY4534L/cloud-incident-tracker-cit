import unittest
from main import app, INCIDENTS

class IncidentApiTests(unittest.TestCase):
    def setUp(self):
        INCIDENTS.clear()
        self.client = app.test_client()

    def test_health(self):
        r = self.client.get('/health')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()['status'], 'ok')

    def test_create_and_get(self):
        r = self.client.post('/incidents', json={'title':'VPN issue','description':'Cannot connect','severity':'high'})
        self.assertEqual(r.status_code, 201)
        incident_id = r.get_json()['id']
        self.assertEqual(self.client.get(f'/incidents/{incident_id}').status_code, 200)

    def test_invalid_severity(self):
        r = self.client.post('/incidents', json={'title':'Test','description':'Example','severity':'extreme'})
        self.assertEqual(r.status_code, 400)

    def test_update(self):
        created = self.client.post('/incidents', json={'title':'Old title','description':'Example'}).get_json()
        r = self.client.patch(f"/incidents/{created['id']}", json={'status':'resolved'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()['status'], 'resolved')

    def test_not_found(self):
        self.assertEqual(self.client.get('/incidents/missing').status_code, 404)

    def test_delete(self):
        created = self.client.post('/incidents', json={'title':'Delete me','description':'Example'}).get_json()
        self.assertEqual(self.client.delete(f"/incidents/{created['id']}").status_code, 200)
        self.assertEqual(self.client.get(f"/incidents/{created['id']}").status_code, 404)

if __name__ == '__main__': unittest.main()
