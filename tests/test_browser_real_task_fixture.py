import json
import socket
import subprocess
import tempfile
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER = REPO_ROOT / 'tests' / 'fixtures' / 'browser_real_task_server.mjs'


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def seed_data():
    return {
        'target_id': 'CASE-TARGET',
        'expected': {
            'address': '18 New Harbor Road',
            'status': 'Approved',
            'comment': 'Reviewed by agent',
        },
        'cases': [
            {'id': 'CASE-TARGET', 'client': 'Marina Volkova', 'status': 'Pending', 'address': '10 Old Harbor Road', 'comment': 'Priority customer'},
            {'id': 'CASE-DECOY', 'client': 'Marina Volkova', 'status': 'Pending', 'address': '44 Pine Street', 'comment': 'Waiting for customer'},
            {'id': 'CASE-OTHER', 'client': 'Maria Volkova', 'status': 'Approved', 'address': '7 Lake Avenue', 'comment': 'Already reviewed'},
        ],
    }


def post_case(port, case_id, address, status, comment):
    body = urllib.parse.urlencode({'address': address, 'status': status, 'comment': comment}).encode('utf-8')
    request = urllib.request.Request(
        f'http://127.0.0.1:{port}/case/{case_id}/save',
        data=body,
        method='POST',
        headers={'content-type': 'application/x-www-form-urlencoded'},
    )
    with urllib.request.urlopen(request) as response:
        return response.status, response.read().decode('utf-8')


class FixtureProcess:
    def __init__(self, root):
        self.root = Path(root)
        self.port = free_port()
        self.gate_token = 'TEST_GATE_TOKEN'
        self.generation = 'TEST_GENERATION'
        (self.root / 'fixture-seed.json').write_text(json.dumps(seed_data()), encoding='utf-8')
        self.proc = subprocess.Popen(
            [
                'node', str(SERVER), '--root', str(self.root), '--port', str(self.port),
                '--gate-token', self.gate_token, '--generation', self.generation,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def wait_ready(self):
        deadline = time.time() + 10
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise AssertionError(self.proc.stderr.read())
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{self.port}/health', timeout=0.5) as response:
                    health = json.load(response)
                if health['status'] == 'ok':
                    self.assert_generation(health)
                    return
            except Exception:
                time.sleep(0.05)
        raise AssertionError('fixture server did not become ready')

    def assert_generation(self, payload):
        if payload.get('generation') != self.generation:
            raise AssertionError(f'fixture generation mismatch: {payload}')

    def freeze(self):
        request = urllib.request.Request(
            f'http://127.0.0.1:{self.port}/__gate/freeze',
            data=b'',
            method='POST',
            headers={'X-Gate-Token': self.gate_token},
        )
        with urllib.request.urlopen(request, timeout=2) as response:
            payload = json.load(response)
        self.assert_generation(payload)
        return payload

    def close(self):
        self.proc.terminate()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=5)


class BrowserRealTaskFixtureTests(unittest.TestCase):
    def test_finish_gate_requires_exact_target_change_and_preserves_decoys(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = FixtureProcess(tmp)
            try:
                fixture.wait_ready()
                root = Path(tmp)
                initial_gate = json.loads((root / 'finish-gate.json').read_text(encoding='utf-8'))
                self.assertEqual(initial_gate['status'], 'not_done')
                self.assertTrue(initial_gate['checks']['decoys_unchanged'])
                self.assertTrue(initial_gate['checks']['only_target_ever_mutated'])

                with urllib.request.urlopen(f'http://127.0.0.1:{fixture.port}/') as response:
                    home = response.read().decode('utf-8')
                self.assertIn('CASE-TARGET', home)
                self.assertIn('CASE-DECOY', home)
                self.assertIn('Similar customer names', home)

                status, detail = post_case(
                    fixture.port,
                    'CASE-TARGET',
                    '18 New Harbor Road',
                    'Approved',
                    'Reviewed by agent',
                )
                self.assertEqual(status, 200)
                self.assertIn('18 New Harbor Road', detail)
                self.assertIn('Approved', detail)
                self.assertIn('Reviewed by agent', detail)

                final_gate = json.loads((root / 'finish-gate.json').read_text(encoding='utf-8'))
                self.assertEqual(final_gate['status'], 'done')
                self.assertTrue(all(final_gate['checks'].values()))
                self.assertEqual(final_gate['save_count'], 1)
                self.assertEqual(final_gate['mutated_ids'], ['CASE-TARGET'])

                state = json.loads((root / 'server-state.json').read_text(encoding='utf-8'))
                decoy = next(item for item in state['cases'] if item['id'] == 'CASE-DECOY')
                self.assertEqual(decoy['address'], '44 Pine Street')
                self.assertEqual(decoy['comment'], 'Waiting for customer')

                audit_lines = (root / 'audit.jsonl').read_text(encoding='utf-8').strip().splitlines()
                self.assertEqual(len(audit_lines), 1)
                self.assertEqual(json.loads(audit_lines[0])['id'], 'CASE-TARGET')
            finally:
                fixture.close()

    def test_touching_and_restoring_a_decoy_still_fails_finish_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = FixtureProcess(tmp)
            try:
                fixture.wait_ready()
                root = Path(tmp)

                post_case(fixture.port, 'CASE-DECOY', 'WRONG TEMP VALUE', 'Pending', 'Waiting for customer')
                post_case(fixture.port, 'CASE-DECOY', '44 Pine Street', 'Pending', 'Waiting for customer')
                post_case(fixture.port, 'CASE-TARGET', '18 New Harbor Road', 'Approved', 'Reviewed by agent')

                gate = json.loads((root / 'finish-gate.json').read_text(encoding='utf-8'))
                self.assertEqual(gate['status'], 'not_done')
                self.assertTrue(gate['checks']['decoys_unchanged'])
                self.assertFalse(gate['checks']['only_target_ever_mutated'])
                self.assertEqual(set(gate['mutated_ids']), {'CASE-TARGET', 'CASE-DECOY'})
            finally:
                fixture.close()

    def test_authenticated_freeze_creates_one_atomic_snapshot_and_blocks_late_save(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = FixtureProcess(tmp)
            try:
                fixture.wait_ready()
                root = Path(tmp)
                post_case(fixture.port, 'CASE-TARGET', '18 New Harbor Road', 'Approved', 'Reviewed by agent')

                frozen = fixture.freeze()
                self.assertEqual(frozen['status'], 'frozen')
                self.assertEqual(frozen['finish'], 'done')

                snapshot = json.loads((root / 'frozen-snapshot.json').read_text(encoding='utf-8'))
                self.assertTrue(snapshot['frozen'])
                self.assertEqual(snapshot['fixture_generation'], fixture.generation)
                self.assertEqual(snapshot['finish']['status'], 'done')
                self.assertEqual(snapshot['state']['save_count'], 1)
                self.assertEqual(len(snapshot['audit']), 1)
                self.assertEqual(snapshot['audit'][0]['id'], 'CASE-TARGET')

                with self.assertRaises(urllib.error.HTTPError) as raised:
                    post_case(fixture.port, 'CASE-DECOY', 'LATE', 'Pending', 'late')
                self.assertEqual(raised.exception.code, 423)

                snapshot_after = json.loads((root / 'frozen-snapshot.json').read_text(encoding='utf-8'))
                self.assertEqual(snapshot_after, snapshot)
            finally:
                fixture.close()


if __name__ == '__main__':
    unittest.main()
