"""
tests/test_routes.py
Tests Flask API routes.
"""
import sys
import io
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

@pytest.fixture
def client():
    import app as app_module
    app_module.app.config['TESTING'] = True
    app_module.app.config['WTF_CSRF_ENABLED'] = False
    with app_module.app.test_client() as client:
        yield client


def test_homepage_loads(client):
    resp = client.get('/')
    assert resp.status_code == 200
    assert b'CurriculumLens' in resp.data


def test_health_endpoint(client):
    resp = client.get('/api/health')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'status' in data
    assert data['status'] == 'ok'
    assert 'model_available' in data


def test_single_analysis_no_file(client):
    resp = client.post('/api/analyze-single')
    assert resp.status_code == 400
    data = resp.get_json()
    assert 'error' in data


def test_single_analysis_bad_extension(client):
    resp = client.post(
        '/api/analyze-single',
        data={'syllabus': (io.BytesIO(b'content'), 'file.xyz')},
        content_type='multipart/form-data'
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert 'error' in data


def test_single_analysis_with_txt(client):
    syllabus_content = b"""
Unit 1: Machine Learning
- Supervised learning: classification and regression
- Model evaluation: cross-validation and metrics
- Feature engineering and selection

Unit 2: Neural Networks
- Feedforward networks and backpropagation
- Activation functions and optimization
"""
    resp = client.post(
        '/api/analyze-single',
        data={'syllabus': (io.BytesIO(syllabus_content), 'test_syllabus.txt')},
        content_type='multipart/form-data'
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get('success') is True
    result = data.get('result', {})
    assert 'total_topics' in result
    assert result['total_topics'] > 0


def test_compare_missing_files(client):
    resp = client.post('/api/compare')
    assert resp.status_code in (400, 503)


def test_model_performance_endpoint(client):
    resp = client.get('/api/model-performance')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'available' in data


def test_about_page_removed(client):
    """About page was removed as per project specifications."""
    resp = client.get('/about')
    assert resp.status_code == 404


def test_model_performance_page(client):
    resp = client.get('/model-performance')
    assert resp.status_code == 200


def test_single_page(client):
    resp = client.get('/analyze-single')
    assert resp.status_code == 200


def test_compare_page(client):
    resp = client.get('/compare')
    assert resp.status_code == 200
