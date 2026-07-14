"""RED-phase consistency tests: documentation and CLI wording vs. actual behavior.

Each test asserts what the docs/CLI *should* say; the current checkout will
fail on at least one assertion per test class.  Do NOT modify implementation
or documentation to make them pass.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "webbuilder" / "scripts"
REFERENCES = ROOT / "webbuilder" / "references"

README_ZH = ROOT / "README.md"
README_EN = ROOT / "README_EN.md"
SKILL_MD = ROOT / "webbuilder" / "SKILL.md"
CAPTURE_EVIDENCE = SCRIPTS / "capture-evidence.py"
TRANSITION_STATE = SCRIPTS / "transition-state.py"
CHECK_STATE = SCRIPTS / "check-state.py"
INIT_STATE = SCRIPTS / "init-state.py"
MIGRATE_STATE = SCRIPTS / "migrate-state.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _ref(name: str) -> str:
    return _read(REFERENCES / name)


# Intentionally allowed lowercase slug/URL/workflow/path identifiers.
_SLUG_RE = re.compile(
    r"https?://\S*spec2web\S*"       # URL
    r"|Zboo-0324/spec2web"            # GitHub slug
    r"|spec2web\.git"                 # git clone URL
    r"|spec2web-smoke"                # temp dir name
    r"|\\spec2web\\"                  # path segment
    r"|/spec2web/"                    # path segment (forward slash)
    r"|Set-Location spec2web"         # directory name
    r"|workflow: spec2web"            # workflow marker
    r"|LEGACY_STATE_DIR_NAME"         # compat constant
    r"|spec2web"                      # bare lowercase slug
)


def _find_capitalized_spec2web(text: str, filename: str) -> list[str]:
    """Return lines with 'Spec2Web' that are NOT allowed lowercase slugs."""
    violations = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if "Spec2Web" in line:
            cleaned = _SLUG_RE.sub("", line)
            if "Spec2Web" in cleaned:
                violations.append(f"{filename}:{lineno}: {line.strip()}")
    return violations


# ===================================================================
# 1. capture-evidence flags: --run / --subject in all public docs
# ===================================================================
class CaptureEvidenceFlagTests(unittest.TestCase):
    """Public docs must use --run and --subject, not --run-id / --subject-id."""

    def test_script_defines_run_flag(self) -> None:
        source = _read(CAPTURE_EVIDENCE)
        self.assertIn('"--run"', source)
        self.assertNotIn('"--run-id"', source)

    def test_script_defines_subject_flag(self) -> None:
        source = _read(CAPTURE_EVIDENCE)
        self.assertIn('"--subject"', source)
        self.assertNotIn('"--subject-id"', source)

    def test_readme_zh_uses_run_subject(self) -> None:
        text = _read(README_ZH)
        self.assertRegex(text, r"capture-evidence\.py\b.*?--run\b.*?--subject\b")
        self.assertNotRegex(text, r"capture-evidence\.py\b.*?--run-id\b")
        self.assertNotRegex(text, r"capture-evidence\.py\b.*?--subject-id\b")

    def test_readme_en_uses_run_subject(self) -> None:
        text = _read(README_EN)
        self.assertRegex(text, r"capture-evidence\.py\b.*?--run\b.*?--subject\b")
        self.assertNotRegex(text, r"capture-evidence\.py\b.*?--run-id\b")
        self.assertNotRegex(text, r"capture-evidence\.py\b.*?--subject-id\b")

    def test_skill_md_uses_run_subject(self) -> None:
        text = _read(SKILL_MD)
        self.assertRegex(text, r"capture-evidence\.py\b.*?--run\b.*?--subject\b")
        self.assertNotRegex(text, r"capture-evidence\.py\b.*?--run-id\b")
        self.assertNotRegex(text, r"capture-evidence\.py\b.*?--subject-id\b")

    def test_ref_state_files_uses_run_subject(self) -> None:
        text = _ref("state-files.md")
        self.assertNotRegex(text, r"capture-evidence\.py\b.*?--run-id\b")
        self.assertNotRegex(text, r"capture-evidence\.py\b.*?--subject-id\b")
        self.assertRegex(text, r"capture-evidence\.py\b.*?--run\b.*?--subject\b")

    def test_ref_worktree_mode_uses_run_subject(self) -> None:
        text = _ref("worktree-mode.md")
        self.assertNotRegex(text, r"capture-evidence\.py\b.*?--run-id\b")
        self.assertNotRegex(text, r"capture-evidence\.py\b.*?--subject-id\b")
        self.assertRegex(text, r"capture-evidence\.py\b.*?--run\b.*?--subject\b")

    def test_ref_multi_agent_uses_run_subject(self) -> None:
        text = _ref("multi-agent-orchestration.md")
        self.assertNotRegex(text, r"capture-evidence\.py\b.*?--run-id\b")
        self.assertNotRegex(text, r"capture-evidence\.py\b.*?--subject-id\b")
        self.assertRegex(text, r"capture-evidence\.py\b.*?--run\b.*?--subject\b")

    def test_ref_delivery_checklist_uses_run_subject(self) -> None:
        text = _ref("delivery-checklist.md")
        self.assertNotRegex(text, r"capture-evidence\.py\b.*?--run-id\b")
        self.assertNotRegex(text, r"capture-evidence\.py\b.*?--subject-id\b")
        self.assertRegex(text, r"capture-evidence\.py\b.*?--run\b.*?--subject\b")


# ===================================================================
# 2. SKILL resume: --resume is a standalone boolean flag
# ===================================================================
class SkillResumeCommandTests(unittest.TestCase):
    """--resume is a standalone boolean flag; --checkpoint pairs only with --stop-reason."""

    def test_transition_state_resume_is_boolean(self) -> None:
        source = _read(TRANSITION_STATE)
        self.assertRegex(
            source,
            r"""add_argument\(\s*["']--resume["'],\s*action=["']store_true["']""",
        )

    def test_skill_md_resume_section_documents_standalone_resume(self) -> None:
        text = _read(SKILL_MD)
        section = text[text.find("## Resume Through the State Kernel"):]
        code_block = section[section.find("```"):]
        code_block = code_block[: code_block.find("```", 3) + 3]
        self.assertNotRegex(code_block, r"--resume\s+\S+")
        self.assertNotIn("--checkpoint", code_block)

    def test_skill_md_resume_section_says_checkpoint_cleared_not_recorded(self) -> None:
        """--resume sets resume_checkpoint to 'none' (clears it); docs must not say it records one."""
        text = _read(SKILL_MD)
        section = text[text.find("## Resume Through the State Kernel"):]
        # Trim to the next ## heading so we only inspect this section.
        next_heading = section.find("\n## ", 1)
        if next_heading != -1:
            section = section[:next_heading]
        # Find the prose paragraph that mentions --resume outside a code block.
        in_code = False
        resume_para = ""
        for line in section.splitlines():
            if line.startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                continue
            if "--resume" in line:
                resume_para = line
                break
        self.assertNotIn(
            "records",
            resume_para,
            "--resume clears resume_checkpoint (sets it to 'none'); "
            "the docs must not say --resume records a checkpoint",
        )


# ===================================================================
# 3. READMEs: eleven phases including host, initialization, ui
# ===================================================================
class ValidationPhaseCountTests(unittest.TestCase):
    """Both READMEs must say eleven phases and describe host, initialization, ui."""

    def test_readme_zh_says_eleven_phases(self) -> None:
        text = _read(README_ZH)
        self.assertNotIn("八个阶段", text,
                          "README.md must not say eight phases")
        self.assertIn("十一个阶段", text,
                       "README.md must say eleven phases")

    def test_readme_en_says_eleven_phases(self) -> None:
        text = _read(README_EN)
        self.assertNotRegex(text, r"eight validation phases")
        self.assertRegex(text, r"eleven validation phases")

    def test_readme_zh_lists_host_initialization_ui(self) -> None:
        text = _read(README_ZH)
        self.assertRegex(text, r"`host`")
        self.assertRegex(text, r"`initialization`")
        self.assertRegex(text, r"`ui`")

    def test_readme_en_lists_host_initialization_ui(self) -> None:
        text = _read(README_EN)
        self.assertRegex(text, r"`host`")
        self.assertRegex(text, r"`initialization`")
        self.assertRegex(text, r"`ui`")


# ===================================================================
# 4. Product name: WebBuilder, not capitalized Spec2Web
# ===================================================================
class ProductNameTests(unittest.TestCase):
    """User-facing docs and CLI must use WebBuilder, not Spec2Web.

    Lowercase spec2web as a slug, URL, workflow marker, directory name,
    LEGACY_STATE_DIR_NAME, or existing test identifier is allowed.
    """

    def test_readme_zh_no_spec2web(self) -> None:
        violations = _find_capitalized_spec2web(_read(README_ZH), "README.md")
        self.assertEqual(violations, [])

    def test_readme_en_no_spec2web(self) -> None:
        violations = _find_capitalized_spec2web(_read(README_EN), "README_EN.md")
        self.assertEqual(violations, [])

    def test_skill_md_no_spec2web(self) -> None:
        violations = _find_capitalized_spec2web(_read(SKILL_MD), "SKILL.md")
        self.assertEqual(violations, [])

    def test_ref_role_protocol_no_spec2web(self) -> None:
        violations = _find_capitalized_spec2web(_ref("role-protocol.md"), "role-protocol.md")
        self.assertEqual(violations, [])

    def test_ref_loop_engineering_no_spec2web(self) -> None:
        violations = _find_capitalized_spec2web(_ref("loop-engineering.md"), "loop-engineering.md")
        self.assertEqual(violations, [])

    def test_ref_reasoning_and_review_no_spec2web(self) -> None:
        violations = _find_capitalized_spec2web(_ref("reasoning-and-review.md"), "reasoning-and-review.md")
        self.assertEqual(violations, [])

    def test_ref_multi_agent_orchestration_no_spec2web(self) -> None:
        violations = _find_capitalized_spec2web(_ref("multi-agent-orchestration.md"), "multi-agent-orchestration.md")
        self.assertEqual(violations, [])

    def test_ref_install_no_spec2web(self) -> None:
        violations = _find_capitalized_spec2web(_ref("install.md"), "install.md")
        self.assertEqual(violations, [])

    def test_check_state_no_spec2web(self) -> None:
        source = _read(CHECK_STATE)
        self.assertNotIn("Spec2Web", source)

    def test_init_state_no_spec2web(self) -> None:
        source = _read(INIT_STATE)
        self.assertNotIn("Spec2Web", source)

    def test_migrate_state_no_spec2web(self) -> None:
        source = _read(MIGRATE_STATE)
        self.assertNotIn("Spec2Web", source)


if __name__ == "__main__":
    unittest.main()
