import json
import pathlib
import shutil
import subprocess
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXTENSION = ROOT / "experiments" / "chatgpt-deeplink-autosend"


class ChatGptDeepLinkAutosendExtensionTests(unittest.TestCase):
    def test_manifest_is_narrow_and_permission_free(self):
        manifest = json.loads((EXTENSION / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["manifest_version"], 3)
        self.assertNotIn("permissions", manifest)
        self.assertNotIn("host_permissions", manifest)
        self.assertNotIn("background", manifest)
        self.assertNotIn("externally_connectable", manifest)

        scripts = manifest["content_scripts"]
        self.assertEqual(len(scripts), 1)
        self.assertEqual(scripts[0]["matches"], ["https://chatgpt.com/*"])
        self.assertEqual(scripts[0]["js"], ["policy.js", "content.js"])
        self.assertEqual(scripts[0]["world"], "ISOLATED")

    def test_javascript_syntax(self):
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node.js is required to syntax-check the extension")
        for name in ("policy.js", "content.js"):
            completed = subprocess.run(
                [node, "--check", str(EXTENSION / name)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_policy_requires_origin_opt_in_run_id_and_visible_sentinel(self):
        run_id = "autosend-run-example-001"
        prompt = (
            "@Chat Local Bridge Test DEEPLINK_GATE\n"
            f"CAP_AUTOSEND_RUN_ID={run_id}\n"
            "Use only Chat Local Bridge Test."
        )
        valid_url = (
            "https://chatgpt.com/?cap_autosend=1"
            f"&cap_run_id={run_id}"
            "&cap_plugin=Chat%20Local%20Bridge%20Test"
            f"&prompt={self._quote(prompt)}"
        )

        valid = self._run_policy("parseIntent", valid_url)
        self.assertTrue(valid["enabled"])
        self.assertEqual(valid["runId"], run_id)
        self.assertEqual(valid["plugin"], "Chat Local Bridge Test")
        self.assertEqual(valid["sentinel"], f"CAP_AUTOSEND_RUN_ID={run_id}")

        no_opt_in = self._run_policy(
            "parseIntent",
            f"https://chatgpt.com/?cap_run_id={run_id}&prompt={self._quote(prompt)}",
        )
        self.assertEqual(no_opt_in, {"enabled": False, "reason": "not-opted-in"})

        wrong_origin = self._run_policy(
            "parseIntent",
            valid_url.replace("https://chatgpt.com/", "https://example.com/", 1),
        )
        self.assertEqual(wrong_origin, {"enabled": False, "reason": "wrong-origin"})

        bad_run_id = self._run_policy(
            "parseIntent",
            valid_url.replace(run_id, "bad run id", 1),
        )
        self.assertEqual(bad_run_id, {"enabled": False, "reason": "invalid-run-id"})

        missing_sentinel_prompt = "@Chat Local Bridge Test DEEPLINK_GATE"
        missing_sentinel_url = (
            "https://chatgpt.com/?cap_autosend=1"
            f"&cap_run_id={run_id}"
            f"&prompt={self._quote(missing_sentinel_prompt)}"
        )
        mismatch = self._run_policy("parseIntent", missing_sentinel_url)
        self.assertEqual(mismatch, {"enabled": False, "reason": "sentinel-mismatch"})

        composer_ok = self._run_policy(
            "containsRequiredComposerText",
            "Chat Local Bridge Test ... CAP_AUTOSEND_RUN_ID=" + run_id,
            valid,
        )
        self.assertTrue(composer_ok)

        composer_missing_plugin = self._run_policy(
            "containsRequiredComposerText",
            "CAP_AUTOSEND_RUN_ID=" + run_id,
            valid,
        )
        self.assertFalse(composer_missing_plugin)

    @staticmethod
    def _quote(value):
        from urllib.parse import quote

        return quote(value, safe="")

    @staticmethod
    def _run_policy(function_name, *args):
        node = shutil.which("node")
        if node is None:
            raise AssertionError("Node.js is required to execute extension policy tests")

        policy_path = EXTENSION / "policy.js"
        script = r"""
const fs = require('fs');
const vm = require('vm');
const path = process.argv[1];
const fn = process.argv[2];
const args = JSON.parse(process.argv[3]);
const context = { URL, console };
context.globalThis = context;
vm.createContext(context);
vm.runInContext(fs.readFileSync(path, 'utf8'), context, { filename: path });
const result = context.CAPAutoSendPolicy[fn](...args);
process.stdout.write(JSON.stringify(result));
"""
        completed = subprocess.run(
            [node, "-e", script, str(policy_path), function_name, json.dumps(args)],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(completed.stderr)
        return json.loads(completed.stdout)


if __name__ == "__main__":
    unittest.main()
