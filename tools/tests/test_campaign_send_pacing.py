from django.test import SimpleTestCase

from tools.campaign_send_pacing import compute_bridge_wait_seconds


class BridgeSendPacingTests(SimpleTestCase):
    def test_minimum_wait(self):
        for _ in range(20):
            wait = compute_bridge_wait_seconds(base_seconds=12, sent_index=0, message_length=50)
            self.assertGreaterEqual(wait, 8.0)
            self.assertLessEqual(wait, 600.0)

    def test_longer_breaks_on_milestones(self):
        waits = [
            compute_bridge_wait_seconds(base_seconds=12, sent_index=9, message_length=80)
            for _ in range(30)
        ]
        self.assertTrue(any(w >= 40 for w in waits))
