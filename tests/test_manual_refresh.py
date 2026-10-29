"""Le lancement manuel doit rester authentifié et ne jamais publier de token."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = 'https://github.com/LenaAlban/observatoire-scpi-LLS/actions/workflows/pages.yml'

class ManualRefreshTests(unittest.TestCase):
    def test_public_button_opens_secure_workflow_and_does_not_fake_a_run(self):
        html = (ROOT / 'index.html').read_text(encoding='utf-8')
        self.assertIn('id="run-collection-btn"', html)
        self.assertIn('href="' + WORKFLOW + '"', html)
        self.assertIn('target="_blank" rel="noopener noreferrer"', html)
        self.assertIn("$('run-collection-btn').onclick=requestFreshCollection;", html)
        self.assertIn('Le clic ici ne lance pas encore le robot', html)
        self.assertIn("Date.parse(syncStatus?.checkedAt||'')", html)
        self.assertIn('collectionMonitor=setInterval(checkCollectionPublication,20000)', html)
        self.assertIn('collectionDeadline=setTimeout', html)
        self.assertIn('id="refresh-btn"', html)
        self.assertNotIn('api.github.com/repos/LenaAlban/observatoire-scpi-LLS/actions/workflows/pages.yml/dispatches',html)

    def test_workflow_dispatch_updates_and_deploys(self):
        yaml=(ROOT / '.github/workflows/pages.yml').read_text(encoding='utf-8')
        self.assertRegex(yaml,r'(?m)^  workflow_dispatch:\s*$')
        self.assertIn("if: github.event_name != 'push'",yaml)
        self.assertIn('run: python scripts/sync.py',yaml)
        self.assertIn('git add data/scpi.json data/status.json',yaml)
        self.assertIn('uses: actions/deploy-pages@v4',yaml)

if __name__ == '__main__':
    unittest.main()
