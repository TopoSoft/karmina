import tempfile
import unittest
from pathlib import Path

from karmina.studio import Studio, StudioError, AGENTS


class StudioTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'studio.sqlite3'
        self.studio = Studio(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def project(self, tenant='alpha', mode='animation'):
        return self.studio.create(tenant, {'title': 'Pencil moon', 'brief': 'A drawn fox finds a city of light.', 'mode': mode, 'language': 'en'})

    def test_create_persist_and_isolate(self):
        project = self.project()
        self.assertEqual(Studio(self.path).get('alpha', project['id'])['title'], 'Pencil moon')
        self.assertEqual(self.studio.list('beta'), [])
        with self.assertRaises(StudioError) as ctx:
            self.studio.get('beta', project['id'])
        self.assertEqual(ctx.exception.code, 'not_found')

    def test_pipeline_requires_approval_and_exports_versioned_artifacts(self):
        p = self.project()
        with self.assertRaises(StudioError):
            self.studio.draft('alpha', p['id'], 'writer', 0)
        for agent in AGENTS:
            role = agent['id']
            p = self.studio.draft('alpha', p['id'], role, p['version'])
            step = next(s for s in p['steps'] if s['agent_id'] == role)
            self.assertEqual(step['status'], 'review')
            self.assertTrue(step['artifact']['content'])
            p = self.studio.approve('alpha', p['id'], role, p['version'])
        self.assertEqual(p['status'], 'preproduction_ready')
        self.assertEqual(len(self.studio.export('alpha', p['id'])['artifacts']), len(AGENTS))

    def test_optimistic_locking_and_revision_preservation(self):
        p = self.project()
        first = self.studio.draft('alpha', p['id'], 'producer', p['version'])
        with self.assertRaises(StudioError) as ctx:
            self.studio.approve('alpha', p['id'], 'producer', p['version'])
        self.assertEqual(ctx.exception.code, 'version_conflict')
        second = self.studio.draft('alpha', p['id'], 'producer', first['version'], 'Director revision')
        step = second['steps'][0]
        self.assertEqual(step['artifact']['revision'], 2)
        self.assertEqual(len(step['history']), 2)
        self.assertEqual(step['artifact']['content'], 'Director revision')

    def test_mode_validation_and_no_paid_execution(self):
        self.assertEqual(self.project(mode='photorealistic')['mode'], 'photorealistic')
        for change in ({'mode': 'other'}, {'title': ''}, {'brief': 'x' * 12001}, {'language': 'xx'}):
            data = {'title': 'Film', 'brief': 'Story', 'mode': 'animation', 'language': 'en', **change}
            with self.assertRaises(StudioError):
                self.studio.create('alpha', data)
        p = self.project()
        with self.assertRaises(StudioError) as ctx:
            self.studio.draft('alpha', p['id'], 'producer', 0, runtime='ohagent')
        self.assertEqual(ctx.exception.code, 'runtime_unavailable')
        self.assertEqual(self.studio.get('alpha', p['id'])['version'], 0)

    def test_cannot_edit_approved_artifact_or_export_incomplete(self):
        p = self.project()
        with self.assertRaises(StudioError):
            self.studio.export('alpha', p['id'])
        with self.assertRaises(StudioError):
            self.studio.approve('alpha', p['id'], 'producer', 0)
        p = self.studio.draft('alpha', p['id'], 'producer', 0)
        p = self.studio.approve('alpha', p['id'], 'producer', p['version'])
        with self.assertRaises(StudioError):
            self.studio.draft('alpha', p['id'], 'producer', p['version'])

    def test_unknown_agent_and_cross_tenant_writes_fail(self):
        p = self.project()
        for tenant, role in [('beta', 'producer'), ('alpha', 'unknown')]:
            with self.assertRaises(StudioError):
                self.studio.draft(tenant, p['id'], role, 0)
        self.assertEqual(self.studio.get('alpha', p['id'])['version'], 0)


if __name__ == '__main__':
    unittest.main()
