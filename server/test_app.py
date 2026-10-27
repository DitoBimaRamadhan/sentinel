import os, unittest
from pathlib import Path
from unittest.mock import patch
import app as sentinel

class SentinelSmokeTests(unittest.TestCase):
    def setUp(self):
        sentinel.app.config['TESTING'] = True
        self.client = sentinel.app.test_client()

    def test_home_serves_html(self):
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'SENTINEL', r.data)

    def test_health_without_keys(self):
        r = self.client.get('/api/health')
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json['openrouter_configured'])

    def test_health_reads_key_from_header_only(self):
        r = self.client.get('/api/health', headers={'X-OpenRouter-Key': 'sk-or-test'})
        self.assertTrue(r.json['openrouter_configured'])
        self.assertNotIn(b'sk-or-test', r.data)
        # The key must not carry over to the next request.
        self.assertFalse(self.client.get('/api/health').json['openrouter_configured'])

    def test_analyze_without_key_is_actionable_error(self):
        with patch.object(sentinel, 'fetch_article') as fetch:
            r = self.client.post('/api/analyze', json={'type':'url','url':'https://example.org/'})
        self.assertEqual(r.status_code, 401)
        self.assertIn('API key', r.json['error'])
        fetch.assert_not_called()  # no outbound work without the visitor's own key

    def test_config_cannot_store_keys(self):
        before = set(os.listdir(sentinel.APP_DIR))
        r = self.client.post('/api/config', json={'openrouter_api_key':'sk-or-should-not-persist',
                                                   'tavily_api_key':'tvly-x', 'model':'openai/gpt-4.1-mini'})
        self.assertEqual(r.status_code, 405)
        self.assertEqual(before, set(os.listdir(sentinel.APP_DIR)))
        self.assertFalse(hasattr(sentinel, 'save_config'))
        self.assertFalse(self.client.get('/api/health').json['openrouter_configured'])
        self.assertNotIn(b'sk-or-should-not-persist', self.client.get('/api/config').data)

    def test_request_size_limit(self):
        big = 'a' * (sentinel.MAX_BODY_BYTES + 10)
        r = self.client.post('/api/analyze', data=big, content_type='application/json',
                             headers={'X-OpenRouter-Key':'k'})
        self.assertEqual(r.status_code, 413)

    def test_private_url_rejected(self):
        for url in ('http://127.0.0.1:5000/private', 'http://169.254.169.254/latest/meta-data',
                    'http://localhost/', 'file:///etc/passwd', 'http://user:pw@example.com/'):
            with self.assertRaises(ValueError):
                sentinel.safe_public_url(url)

    def test_social_url_without_text_uses_article_fetch(self):
        fake_article = {'title':'Artikel Uji','url':'https://example.org/news','text':'Isi berita cukup panjang untuk dianalisis. '*20}
        seen = {}
        def fake_call(cfg, prompt, image_data_url=None):
            seen['key'] = cfg['openrouter_api_key']; seen['model'] = cfg['model']
            return {'status':'belum_terverifikasi','summary':'Uji','claims':[],'indicators':[]}
        with patch.object(sentinel, 'fetch_article', return_value=fake_article), \
             patch.object(sentinel, 'extract_search_queries', return_value=['klaim uji']), \
             patch.object(sentinel, 'call_openrouter', side_effect=fake_call), \
             patch.object(sentinel, 'tavily_search', return_value=[]), \
             patch.object(sentinel, 'google_factchecks', return_value=[]):
            r = self.client.post('/api/analyze', json={'type':'social','url':'https://example.org/news','text':'','platform':'X',
                                                       'model':'google/gemini-2.5-flash'},
                                 headers={'X-OpenRouter-Key':'test-key'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json['summary'], 'Uji')
        self.assertEqual(seen, {'key':'test-key', 'model':'google/gemini-2.5-flash'})
        self.assertTrue(any(x.get('source_type') == 'submitted_article' for x in r.json['sources']))

    def test_bad_image_data_url_rejected(self):
        r = self.client.post('/api/analyze', json={'type':'image','image_data_url':'data:text/html;base64,PGgxPg=='},
                             headers={'X-OpenRouter-Key':'k'})
        self.assertEqual(r.status_code, 400)

if __name__ == '__main__':
    unittest.main(verbosity=2)
