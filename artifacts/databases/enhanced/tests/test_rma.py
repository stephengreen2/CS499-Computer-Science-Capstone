import pytest
from app import create_app, db
from app.models import RMA

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Quantigration RMA Dashboard" in response.data

def test_rma_submission(client):
    client.post('/rma/submit', data={'order_id': '1', 'reason': 'Defective item'})
    with client.application.app_context():
        rma_count = RMA.query.count()
        assert rma_count == 1
