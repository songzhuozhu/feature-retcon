from __future__ import annotations

import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "contract.py"
JOURNAL_BEGIN = "<!-- feature-retcon:journal:begin -->"
JOURNAL_END = "<!-- feature-retcon:journal:end -->"


class ContractCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_cli(self, *arguments: str, expect: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(
            expect,
            result.returncode,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        return result

    def init_contract(self, *, version_control: str = "none", baseline_ref: str | None = None) -> Path:
        arguments = [
            "init",
            str(self.root),
            "--target-stage",
            "implementation",
            "--version-control",
            version_control,
            "--writable-root",
            str(self.root),
        ]
        if baseline_ref:
            arguments.extend(["--baseline-ref", baseline_ref])
        self.run_cli(*arguments)
        return self.root / "RECONCILIATION.md"

    def read_journal(self, contract: Path) -> dict[str, object]:
        content = contract.read_text(encoding="utf-8")
        payload = content.split(JOURNAL_BEGIN, 1)[1].split(JOURNAL_END, 1)[0].strip()
        if payload.startswith("```json") and payload.endswith("```"):
            payload = payload[len("```json") : -len("```")].strip()
        value = json.loads(payload)
        self.assertIsInstance(value, dict)
        return value

    def write_journal(self, contract: Path, journal: dict[str, object]) -> None:
        content = contract.read_text(encoding="utf-8")
        before, remainder = content.split(JOURNAL_BEGIN, 1)
        _, after = remainder.split(JOURNAL_END, 1)
        payload = json.dumps(journal, ensure_ascii=False, indent=2, sort_keys=True)
        contract.write_text(
            f"{before}{JOURNAL_BEGIN}\n```json\n{payload}\n```\n{JOURNAL_END}{after}",
            encoding="utf-8",
        )

    def test_init_creates_private_contract(self) -> None:
        contract = self.init_contract()
        self.assertTrue(contract.is_file())
        self.assertEqual(0o600, stat.S_IMODE(contract.stat().st_mode))
        content = contract.read_text(encoding="utf-8")
        self.assertIn("schema_version: 1", content)
        self.assertNotIn("{{", content)

    def test_existing_file_round_trip(self) -> None:
        target = self.root / "spec.md"
        target.write_text("old\n", encoding="utf-8")
        contract = self.init_contract()

        self.run_cli("prepare", str(contract), "--path", str(target))
        target.write_text("new\n", encoding="utf-8")
        self.run_cli("applied", str(contract), "--path", str(target))
        verified = json.loads(self.run_cli("verify", str(contract)).stdout)
        self.assertTrue(verified["valid"])

        restored = json.loads(self.run_cli("restore", str(contract)).stdout)
        self.assertEqual("ready_to_close", restored["status"])
        self.assertEqual("old\n", target.read_text(encoding="utf-8"))
        self.assertTrue(json.loads(self.run_cli("verify", str(contract)).stdout)["valid"])

    def test_restore_retry_accepts_target_already_at_original_state(self) -> None:
        target = self.root / "spec.md"
        target.write_text("old\n", encoding="utf-8")
        contract = self.init_contract()
        self.run_cli("prepare", str(contract), "--path", str(target))
        target.write_text("new\n", encoding="utf-8")
        self.run_cli("applied", str(contract), "--path", str(target))

        # 模拟进程在恢复文件后、持久化日志状态前中断。
        target.write_text("old\n", encoding="utf-8")
        restored = json.loads(self.run_cli("restore", str(contract)).stdout)

        self.assertEqual("ready_to_close", restored["status"])
        self.assertEqual("old\n", target.read_text(encoding="utf-8"))
        self.assertTrue(json.loads(self.run_cli("verify", str(contract)).stdout)["valid"])

    def test_new_file_is_removed_during_restore(self) -> None:
        target = self.root / "new.md"
        contract = self.init_contract()
        self.run_cli("prepare", str(contract), "--path", str(target))
        target.write_text("created\n", encoding="utf-8")
        self.run_cli("applied", str(contract), "--path", str(target))
        self.run_cli("restore", str(contract))
        self.assertFalse(target.exists())

    def test_repeated_mutations_restore_in_reverse_order(self) -> None:
        target = self.root / "plan.md"
        target.write_text("A\n", encoding="utf-8")
        contract = self.init_contract()
        for value in ("B\n", "C\n"):
            self.run_cli("prepare", str(contract), "--path", str(target))
            target.write_text(value, encoding="utf-8")
            self.run_cli("applied", str(contract), "--path", str(target))
        self.run_cli("restore", str(contract))
        self.assertEqual("A\n", target.read_text(encoding="utf-8"))

    def test_restore_stops_on_external_drift(self) -> None:
        target = self.root / "tasks.md"
        target.write_text("before\n", encoding="utf-8")
        contract = self.init_contract()
        self.run_cli("prepare", str(contract), "--path", str(target))
        target.write_text("after\n", encoding="utf-8")
        self.run_cli("applied", str(contract), "--path", str(target))
        target.write_text("outside-change\n", encoding="utf-8")

        result = self.run_cli("restore", str(contract), expect=2)
        self.assertIn("外部漂移", result.stderr)
        status_result = json.loads(self.run_cli("status", str(contract)).stdout)
        self.assertEqual("blocked", status_result["status"])
        self.assertEqual("outside-change\n", target.read_text(encoding="utf-8"))

    def test_sensitive_value_is_never_echoed(self) -> None:
        target = self.root / ".env"
        sensitive_value = "secret-value-that-must-not-leak"
        target.write_text(f"API_TOKEN={sensitive_value}\n", encoding="utf-8")
        contract = self.init_contract()
        result = self.run_cli("prepare", str(contract), "--path", str(target), expect=2)
        combined = result.stdout + result.stderr
        self.assertIn("敏感候选", combined)
        self.assertNotIn(sensitive_value, combined)

    def test_sensitive_file_requires_explicit_flag_then_round_trips(self) -> None:
        target = self.root / "settings.ini"
        sensitive_value = "secret-value-that-must-stay-local"
        target.write_text(f"client_secret={sensitive_value}\n", encoding="utf-8")
        contract = self.init_contract()
        self.run_cli(
            "prepare",
            str(contract),
            "--path",
            str(target),
            "--allow-sensitive",
        )
        target.write_text("client_secret=replaced-locally\n", encoding="utf-8")
        self.run_cli("applied", str(contract), "--path", str(target))
        self.assertNotIn(sensitive_value, contract.read_text(encoding="utf-8"))
        self.run_cli("restore", str(contract))
        self.assertEqual(f"client_secret={sensitive_value}\n", target.read_text(encoding="utf-8"))

    def test_new_sensitive_content_blocks_without_echo(self) -> None:
        target = self.root / "settings.ini"
        target.write_text("theme=light\n", encoding="utf-8")
        contract = self.init_contract()
        self.run_cli("prepare", str(contract), "--path", str(target))
        sensitive_value = "new-secret-that-must-not-leak"
        target.write_text(f"client_secret={sensitive_value}\n", encoding="utf-8")
        result = self.run_cli("applied", str(contract), "--path", str(target), expect=2)
        self.assertIn("新的敏感候选", result.stderr)
        self.assertNotIn(sensitive_value, result.stderr)
        self.assertNotIn(sensitive_value, contract.read_text(encoding="utf-8"))
        status_result = json.loads(self.run_cli("status", str(contract)).stdout)
        self.assertEqual("blocked", status_result["status"])

    def test_blocked_sensitive_round_cannot_be_marked_ready(self) -> None:
        target = self.root / "settings.ini"
        target.write_text("theme=light\n", encoding="utf-8")
        contract = self.init_contract()
        self.run_cli("prepare", str(contract), "--path", str(target))
        target.write_text("client_secret=local-only-value\n", encoding="utf-8")
        self.run_cli("applied", str(contract), "--path", str(target), expect=2)

        result = self.run_cli("verify", str(contract), "--mark-ready", expect=2)

        self.assertIn("当前状态不能标记", result.stderr)
        status_result = json.loads(self.run_cli("status", str(contract)).stdout)
        self.assertEqual("blocked", status_result["status"])

    def test_large_embedded_payload_requires_explicit_flag(self) -> None:
        target = self.root / "large.bin"
        target.write_bytes(os.urandom(8 * 1024 * 1024))
        contract = self.init_contract()
        result = self.run_cli("prepare", str(contract), "--path", str(target), expect=2)
        self.assertIn("超过 10 MiB", result.stderr)

    def test_authorization_rejects_path_outside_writable_root(self) -> None:
        contract = self.init_contract()
        with tempfile.TemporaryDirectory() as outside_directory:
            outside = Path(outside_directory) / "outside.md"
            outside.write_text("unchanged\n", encoding="utf-8")
            result = self.run_cli("prepare", str(contract), "--path", str(outside), expect=2)
            self.assertIn("不在已授权可写工作根", result.stderr)

    def test_restore_rejects_tampered_path_outside_writable_root(self) -> None:
        target = self.root / "created.md"
        contract = self.init_contract()
        self.run_cli("prepare", str(contract), "--path", str(target))
        target.write_text("same-bytes\n", encoding="utf-8")
        self.run_cli("applied", str(contract), "--path", str(target))

        with tempfile.TemporaryDirectory() as outside_directory:
            outside = Path(outside_directory) / "outside.md"
            outside.write_text("same-bytes\n", encoding="utf-8")
            journal = self.read_journal(contract)
            entries = journal["entries"]
            self.assertIsInstance(entries, list)
            entries[0]["path"] = str(outside)
            self.write_journal(contract, journal)

            result = self.run_cli("restore", str(contract), expect=2)

            self.assertIn("不在已授权可写工作根", result.stderr)
            self.assertEqual("same-bytes\n", outside.read_text(encoding="utf-8"))

    def test_applied_rejects_damaged_journal_shape(self) -> None:
        target = self.root / "spec.md"
        target.write_text("before\n", encoding="utf-8")
        contract = self.init_contract()
        self.run_cli("prepare", str(contract), "--path", str(target))
        target.write_text("after\n", encoding="utf-8")
        journal = self.read_journal(contract)
        entries = journal["entries"]
        self.assertIsInstance(entries, list)
        entries[0]["sensitive_signals"] = {"not": "a-list"}
        self.write_journal(contract, journal)

        result = self.run_cli("applied", str(contract), "--path", str(target), expect=2)

        self.assertIn("sensitive_signals", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_prepare_rejects_symbolic_link(self) -> None:
        real_target = self.root / "real.md"
        link_target = self.root / "linked.md"
        real_target.write_text("unchanged\n", encoding="utf-8")
        link_target.symlink_to(real_target)
        contract = self.init_contract()
        result = self.run_cli("prepare", str(contract), "--path", str(link_target), expect=2)
        self.assertIn("符号链接", result.stderr)
        self.assertEqual("unchanged\n", real_target.read_text(encoding="utf-8"))

    def test_git_recovery_mode_uses_clean_baseline(self) -> None:
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        target = self.root / "design.md"
        target.write_text("baseline\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", "design.md"], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(self.root),
                "-c",
                "user.name=Fixture Author",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "-q",
                "-m",
                "synthetic baseline",
            ],
            check=True,
        )
        contract = self.init_contract(version_control="git", baseline_ref="HEAD")
        self.run_cli("prepare", str(contract), "--path", str(target), "--recovery-mode", "git")
        target.write_text("changed\n", encoding="utf-8")
        self.run_cli("applied", str(contract), "--path", str(target))
        self.run_cli("restore", str(contract))
        self.assertEqual("baseline\n", target.read_text(encoding="utf-8"))

    def test_git_recovery_freezes_moving_baseline_ref(self) -> None:
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        target = self.root / "design.md"
        target.write_text("baseline\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", "design.md"], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(self.root),
                "-c",
                "user.name=Fixture Author",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "-q",
                "-m",
                "synthetic baseline",
            ],
            check=True,
        )
        baseline_sha = subprocess.run(
            ["git", "-C", str(self.root), "rev-parse", "HEAD"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        contract = self.init_contract(version_control="git", baseline_ref="HEAD")
        self.assertIn(f'baseline_ref: "{baseline_sha}"', contract.read_text(encoding="utf-8"))
        self.run_cli("prepare", str(contract), "--path", str(target), "--recovery-mode", "git")
        target.write_text("changed\n", encoding="utf-8")
        self.run_cli("applied", str(contract), "--path", str(target))
        subprocess.run(["git", "-C", str(self.root), "add", "design.md"], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(self.root),
                "-c",
                "user.name=Fixture Author",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "-q",
                "-m",
                "move HEAD",
            ],
            check=True,
        )

        self.run_cli("restore", str(contract))

        self.assertEqual("baseline\n", target.read_text(encoding="utf-8"))

    def test_git_recovery_rejects_dirty_baseline(self) -> None:
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        target = self.root / "design.md"
        target.write_text("baseline\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", "design.md"], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(self.root),
                "-c",
                "user.name=Fixture Author",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "-q",
                "-m",
                "synthetic baseline",
            ],
            check=True,
        )
        contract = self.init_contract(version_control="git", baseline_ref="HEAD")
        target.write_text("accepted working tree baseline\n", encoding="utf-8")
        result = self.run_cli(
            "prepare",
            str(contract),
            "--path",
            str(target),
            "--recovery-mode",
            "git",
            expect=2,
        )
        self.assertIn("必须使用 embed", result.stderr)

    def test_verify_blocks_tracked_contract(self) -> None:
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        marker = self.root / "marker.txt"
        marker.write_text("baseline\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", "marker.txt"], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(self.root),
                "-c",
                "user.name=Fixture Author",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "-q",
                "-m",
                "synthetic baseline",
            ],
            check=True,
        )
        contract = self.init_contract(version_control="git", baseline_ref="HEAD")
        subprocess.run(["git", "-C", str(self.root), "add", contract.name], check=True)
        verified = json.loads(self.run_cli("verify", str(contract)).stdout)
        self.assertFalse(verified["valid"])
        self.assertIn("Git", " ".join(verified["issues"]))

    def test_init_rejects_incorrect_git_declaration(self) -> None:
        result = self.run_cli(
            "init",
            str(self.root),
            "--target-stage",
            "requirements",
            "--version-control",
            "git",
            "--baseline-ref",
            "HEAD",
            "--writable-root",
            str(self.root),
            expect=2,
        )
        self.assertIn("与实际权威根不一致", result.stderr)

    def test_mark_ready_requires_complete_journal(self) -> None:
        target = self.root / "spec.md"
        target.write_text("before\n", encoding="utf-8")
        contract = self.init_contract()
        self.run_cli("prepare", str(contract), "--path", str(target))
        result = self.run_cli("verify", str(contract), "--mark-ready", expect=2)
        self.assertIn("机械校验未通过", result.stderr)


class PackageTests(unittest.TestCase):
    def test_skill_metadata_is_user_invoked(self) -> None:
        skill = (REPO_ROOT / "SKILL.md").read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---", skill, re.DOTALL)
        self.assertIsNotNone(match)
        assert match is not None
        metadata = {
            key.strip(): value.strip()
            for line in match.group(1).splitlines()
            for key, value in [line.split(":", 1)]
        }
        self.assertEqual("feature-retcon", metadata["name"])
        self.assertEqual({"name", "description"}, set(metadata))
        self.assertIn("当用户", metadata["description"])
        self.assertIn("已推进", metadata["description"])

    def test_skill_reference_links_are_direct_and_exist(self) -> None:
        skill = (REPO_ROOT / "SKILL.md").read_text(encoding="utf-8")
        links = re.findall(r"\]\((references/[^)]+\.md)\)", skill)
        self.assertTrue(links)
        for link in links:
            self.assertEqual(2, len(Path(link).parts))
            self.assertTrue((REPO_ROOT / link).is_file(), msg=link)

    def test_local_markdown_links_resolve(self) -> None:
        markdown_files = sorted(REPO_ROOT.glob("*.md")) + sorted((REPO_ROOT / "references").glob("*.md"))
        for markdown in markdown_files:
            content = markdown.read_text(encoding="utf-8")
            for target in re.findall(r"\]\(([^)]+)\)", content):
                target = target.split("#", 1)[0]
                if not target or "://" in target or target.startswith("mailto:"):
                    continue
                self.assertTrue((markdown.parent / target).resolve().exists(), msg=f"{markdown}: {target}")

    def test_bilingual_readmes_have_three_copy_ready_golden_cases(self) -> None:
        chinese = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        chinese_cases = chinese.split("## 三个可复制的黄金案例", 1)[1].split("## 安全不是口号", 1)[0]
        self.assertEqual(3, chinese_cases.count("<summary><strong>案例 "))
        self.assertEqual(3, chinese_cases.count("请使用 feature-retcon Skill"))
        self.assertNotIn("$feature-retcon", chinese_cases)
        self.assertIn("评估后的第二轮：确认或安全停止", chinese_cases)
        self.assertIn("不得使用 git reset", chinese_cases)

        english = (REPO_ROOT / "README_EN.md").read_text(encoding="utf-8")
        english_cases = english.split("## Three copy-ready golden cases", 1)[1].split(
            "## Safety is not a slogan", 1
        )[0]
        self.assertEqual(3, english_cases.count("<summary><strong>Case "))
        self.assertEqual(3, english_cases.count("Use the feature-retcon skill"))
        self.assertNotIn("$feature-retcon", english_cases)
        self.assertIn("Round two: confirm or stop safely", english_cases)
        self.assertIn("Do not use git reset", english_cases)

    def test_bilingual_readmes_document_portable_multi_agent_installation(self) -> None:
        readmes = [
            (REPO_ROOT / "README.md").read_text(encoding="utf-8"),
            (REPO_ROOT / "README_EN.md").read_text(encoding="utf-8"),
        ]
        for content in readmes:
            self.assertIn("npx skills add songzhuozhu/feature-retcon -g", content)
            for agent_id in (
                "codex",
                "claude-code",
                "cursor",
                "opencode",
                "gemini-cli",
                "github-copilot",
                "openclaw",
            ):
                self.assertIn(f"`{agent_id}`", content)
            self.assertIn("clawhub install @songzhuozhu/feature-retcon", content)
            self.assertIn("MIT-0", content)

    def test_distribution_bundle_and_publish_workflow_fail_closed(self) -> None:
        ignore = (REPO_ROOT / ".clawhubignore").read_text(encoding="utf-8")
        for excluded in (
            "README.md",
            "README_EN.md",
            "SECURITY.md",
            "CHANGELOG.md",
            "tests/",
            "scripts/render_demo.py",
            "assets/feature-retcon-demo-*.gif",
            "assets/social-preview.png",
            "agents/",
        ):
            self.assertIn(excluded, ignore)
        self.assertNotIn("scripts/contract.py", ignore)
        self.assertNotIn("references/", ignore)
        self.assertNotIn("assets/RECONCILIATION.md", ignore)

        workflow = (REPO_ROOT / ".github" / "workflows" / "clawhub-publish.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("confirm_mit0", workflow)
        self.assertIn("inputs.confirm_mit0 == true", workflow)
        self.assertIn("skill_path: .", workflow)
        self.assertIn("id-token: write", workflow)
        self.assertIn("dry_run: true", workflow)
        self.assertIn("dry_run: false", workflow)
        self.assertIn("clawhub_token: ${{ secrets.CLAWHUB_TOKEN }}", workflow)

    def test_release_community_files_and_social_preview_are_ready(self) -> None:
        security = (REPO_ROOT / "SECURITY.md").read_text(encoding="utf-8")
        changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("GitHub Security Advisory", security)
        self.assertIn("## [0.1.0] - 2026-08-07", changelog)

        issue_root = REPO_ROOT / ".github" / "ISSUE_TEMPLATE"
        for name in ("bug_report.yml", "feature_request.yml"):
            form = (issue_root / name).read_text(encoding="utf-8")
            self.assertIn("name:", form)
            self.assertIn("description:", form)
            self.assertIn("body:", form)
        config = (issue_root / "config.yml").read_text(encoding="utf-8")
        self.assertIn("blank_issues_enabled: false", config)
        self.assertIn("security/advisories/new", config)

        preview = REPO_ROOT / "assets" / "social-preview.png"
        data = preview.read_bytes()
        self.assertEqual(b"\x89PNG\r\n\x1a\n", data[:8])
        self.assertEqual((1280, 640), tuple(int.from_bytes(data[i : i + 4], "big") for i in (16, 20)))
        self.assertLess(len(data), 1024 * 1024)

    def test_readme_demos_are_localized_15_to_25_second_gifs(self) -> None:
        rendered: list[bytes] = []
        for language in ("zh", "en"):
            demo = REPO_ROOT / "assets" / f"feature-retcon-demo-{language}.gif"
            data = demo.read_bytes()
            rendered.append(data)
            self.assertIn(data[:6], {b"GIF87a", b"GIF89a"})
            dimensions = (
                int.from_bytes(data[6:8], "little"),
                int.from_bytes(data[8:10], "little"),
            )
            self.assertEqual((1200, 720), dimensions)
            self.assertLess(len(data), 1024 * 1024)

            delays: list[int] = []
            offset = 0
            while True:
                offset = data.find(b"\x21\xf9\x04", offset)
                if offset < 0:
                    break
                delays.append(int.from_bytes(data[offset + 4 : offset + 6], "little"))
                offset += 3
            self.assertGreaterEqual(len(delays), 8)
            self.assertGreaterEqual(sum(delays), 1500)
            self.assertLessEqual(sum(delays), 2500)

        self.assertNotEqual(rendered[0], rendered[1])
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        readme_en = (REPO_ROOT / "README_EN.md").read_text(encoding="utf-8")
        self.assertIn("assets/feature-retcon-demo-zh.gif", readme)
        self.assertIn("assets/feature-retcon-demo-en.gif", readme_en)

    def test_openai_metadata_disables_implicit_invocation(self) -> None:
        metadata = (REPO_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("allow_implicit_invocation: false", metadata)
        match = re.search(r'^\s*short_description:\s*"([^"]+)"', metadata, re.MULTILINE)
        self.assertIsNotNone(match)
        assert match is not None
        self.assertGreaterEqual(len(match.group(1)), 25)
        self.assertLessEqual(len(match.group(1)), 64)

    def test_no_scaffold_placeholders_remain(self) -> None:
        paths = [REPO_ROOT / "SKILL.md", *sorted((REPO_ROOT / "references").glob("*.md"))]
        scaffold_marker = "TO" + "DO"
        for path in paths:
            self.assertNotIn(scaffold_marker, path.read_text(encoding="utf-8"), msg=str(path))

    def test_contract_template_has_machine_markers(self) -> None:
        template = (REPO_ROOT / "assets" / "RECONCILIATION.md").read_text(encoding="utf-8")
        for marker in (
            "{{SCHEMA_VERSION}}",
            "{{ROUND_ID}}",
            "{{AUTHORITY_ROOT}}",
            "{{TARGET_STAGE}}",
            "{{JOURNAL_JSON}}",
        ):
            self.assertEqual(1, template.count(marker), msg=marker)
        self.assertEqual(1, template.count("feature-retcon:journal:begin"))
        self.assertEqual(1, template.count("feature-retcon:journal:end"))


if __name__ == "__main__":
    unittest.main()
