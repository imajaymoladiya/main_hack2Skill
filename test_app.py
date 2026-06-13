import unittest
import json
from app import app

class ZenExamTestCase(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_index_route(self):
        """Test that the index landing page loads successfully."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<title>ZenExam AI | Student Mental Wellness Companion</title>', response.data)

    def test_status_route(self):
        """Test that the configuration status API endpoint responds with configurations."""
        response = self.client.get('/api/status')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertIn('has_api_key', data)
        self.assertIn('model_configured', data)

    def test_analyze_journal_valid_fallback(self):
        """Test the journaling API with a standard request, confirming the analysis schema."""
        payload = {
            "journal_text": "I feel slightly worried about my GATE exam syllabus revisions.",
            "mood": "anxious",
            "exam": "GATE"
        }
        response = self.client.post(
            '/api/analyze-journal',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        
        # Verify schema elements are present
        self.assertIn('stress_level', data)
        self.assertIn('burnout_risk', data)
        self.assertIn('primary_triggers', data)
        self.assertIn('detected_cognitive_patterns', data)
        self.assertIn('emotional_state_distribution', data)
        self.assertIn('actionable_coping_strategies', data)
        self.assertIn('personalized_mindfulness_exercise', data)
        self.assertIn('empathetic_insight', data)
        self.assertIn('motivational_boost', data)

    def test_analyze_journal_safety_trigger(self):
        """Test that the journaling API correctly intercepts suicidal keywords for safety."""
        payload = {
            "journal_text": "I want to kill myself because I failed my mock test scores.",
            "mood": "burned_out",
            "exam": "NEET"
        }
        response = self.client.post(
            '/api/analyze-journal',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        
        # Verify safety redirection
        self.assertTrue(data.get('is_safety_trigger'))
        self.assertIn('helplines', data)
        self.assertGreater(len(data['helplines']), 0)
        self.assertTrue(any("kiran" in h["name"].lower() for h in data["helplines"]))

    def test_chat_valid(self):
        """Test that the chat companion API responds with empathetic replies and prompts."""
        payload = {
            "messages": [
                {"role": "user", "content": "How do I deal with study fatigue?"}
            ],
            "exam": "UPSC",
            "stress_level": 6,
            "triggers": ["Fatigue"]
        }
        response = self.client.post(
            '/api/chat',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        
        self.assertIn('reply', data)
        self.assertIn('suggested_quick_prompts', data)
        self.assertGreater(len(data['suggested_quick_prompts']), 0)

    def test_chat_safety_trigger(self):
        """Test that the chat API intercepts self-harm statements immediately."""
        payload = {
            "messages": [
                {"role": "user", "content": "I feel like ending my life right now."}
            ],
            "exam": "JEE",
            "stress_level": 9,
            "triggers": ["Extreme Stress"]
        }
        response = self.client.post(
            '/api/chat',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        
        self.assertTrue(data.get('is_safety_trigger'))
        self.assertIn('helplines', data)

if __name__ == '__main__':
    unittest.main()
