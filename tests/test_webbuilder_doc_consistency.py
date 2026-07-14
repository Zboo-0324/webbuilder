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


# ===================================================================
# 5. Product guide: project-results-and-usage.md contract
# ===================================================================
class ProductGuideTests(unittest.TestCase):
    """The approved current-product documentation contract."""

    GUIDE = REFERENCES / "project-results-and-usage.md"

    def _guide(self) -> str:
        if not self.GUIDE.exists():
            return ""
        return _read(self.GUIDE)

    # -- existence -------------------------------------------------------

    def test_guide_exists(self) -> None:
        self.assertTrue(self.GUIDE.exists(),
                        "project-results-and-usage.md must exist")

    # -- Chinese guide must cover every required topic -------------------

    def test_covers_positioning_and_boundaries(self) -> None:
        text = self._guide()
        self.assertRegex(text, r"产品定位|定位")
        self.assertRegex(text, r"边界|不做什么")

    def test_covers_package_composition(self) -> None:
        text = self._guide()
        self.assertRegex(text, r"包|仓库结构|组成")

    def test_covers_every_bundled_script(self) -> None:
        text = self._guide()
        for script in ("init-state.py", "check-state.py", "check-host.py",
                       "capture-evidence.py", "migrate-state.py",
                       "transition-state.py", "approve-contract.py"):
            self.assertIn(script, text,
                          f"Guide must document {script}")

    def test_covers_guided_and_autonomous_usage(self) -> None:
        text = self._guide()
        self.assertRegex(text, r"引导|guided")
        self.assertRegex(text, r"自主|autonomous")

    def test_covers_end_to_end_workflow(self) -> None:
        text = self._guide()
        self.assertRegex(text, r"工作流|workflow")

    def test_covers_seven_state_files(self) -> None:
        text = self._guide()
        self.assertRegex(text, r"七个状态文件|七.*状态文件|7.*state")
        for name in ("project-rules.md", "requirements-baseline.md",
                     "system-design.md", "task-plan.md", "loop-state.md",
                     "validation-log.md", "delivery-report.md"):
            self.assertIn(name, text, f"Guide must list {name}")

    def test_covers_eleven_validation_phases(self) -> None:
        text = self._guide()
        self.assertRegex(text, r"十一|11")
        self.assertRegex(text, r"阶段|phase")
        for phase in ("host", "initialization", "ui"):
            self.assertRegex(text, rf"`{phase}`")

    def test_covers_task_execution_modes(self) -> None:
        text = self._guide()
        self.assertRegex(text, r"执行模式|execution.mode|single.*delegated.*parallel")

    def test_covers_review_evidence_and_manifests(self) -> None:
        text = self._guide()
        self.assertRegex(text, r"证据|evidence")
        self.assertRegex(text, r"manifest")

    def test_covers_host_capabilities(self) -> None:
        text = self._guide()
        self.assertRegex(text, r"宿主能力|宿主|host.capabilit")

    def test_covers_authorization_and_stop_conditions(self) -> None:
        text = self._guide()
        self.assertRegex(text, r"授权|authorization")
        self.assertRegex(text, r"停止条件|stop.condition|stop_reason")

    def test_covers_installation(self) -> None:
        text = self._guide()
        self.assertRegex(text, r"安装|install")

    def test_covers_maintenance_and_extension(self) -> None:
        text = self._guide()
        self.assertRegex(text, r"维护|扩展|maintenance|extension")

    def test_covers_troubleshooting(self) -> None:
        text = self._guide()
        self.assertRegex(text, r"故障|排查|troubleshoot")

    # -- prohibited framing -----------------------------------------------

    def test_no_process_history_framing(self) -> None:
        """The guide must not frame the product as a process or history document."""
        text = self._guide()
        self.assertNotRegex(text, r"开发过程|development process",
                            "Guide must not describe the development process")
        self.assertNotRegex(text, r"发展历史|development history|演变",
                            "Guide must not describe the development history")

    # -- READMEs must link to the guide ----------------------------------

    def test_readme_zh_links_to_guide(self) -> None:
        text = _read(README_ZH)
        self.assertRegex(text, r"project-results-and-usage\.md")

    def test_readme_en_links_to_guide(self) -> None:
        text = _read(README_EN)
        self.assertRegex(text, r"project-results-and-usage\.md")

    # -- SKILL.md must route to the guide --------------------------------

    def test_skill_md_routes_to_guide(self) -> None:
        text = _read(SKILL_MD)
        self.assertRegex(text, r"project-results-and-usage\.md")

    # -- SKILL.md must not say --resume records a checkpoint -------------

    def test_skill_md_no_inaccurate_after_sentence(self) -> None:
        text = _read(SKILL_MD)
        self.assertNotRegex(
            text,
            r"After recovery succeeds, record the resume checkpoint",
            "SKILL.md must not say 'record the resume checkpoint'; "
            "--resume clears resume_checkpoint (sets it to 'none')",
        )


# ===================================================================
# 6. check-host.py must NOT use --phase (that belongs to check-state.py)
# ===================================================================
class CheckHostPhaseFlagTests(unittest.TestCase):
    """check-host.py accepts --target and --set; it does NOT accept --phase.

    The --phase host|initialization|ui readiness gates belong to check-state.py.
    Every documentation line that combines check-host.py with --phase is a bug.
    """

    # -- check-host.py itself must not define --phase ---------------------

    def test_check_host_script_has_no_phase_flag(self) -> None:
        source = _read(ROOT / "webbuilder" / "scripts" / "check-host.py")
        self.assertNotIn('"--phase"', source,
                         "check-host.py must not define --phase")

    # -- README.md -------------------------------------------------------

    def test_readme_zh_no_check_host_phase(self) -> None:
        text = _read(README_ZH)
        bad = re.findall(r"check-host\.py\b.*?--phase\b", text)
        self.assertEqual(bad, [],
                         "README.md must not combine check-host.py with --phase")

    # -- README_EN.md ----------------------------------------------------

    def test_readme_en_no_check_host_phase(self) -> None:
        text = _read(README_EN)
        bad = re.findall(r"check-host\.py\b.*?--phase\b", text)
        self.assertEqual(bad, [],
                         "README_EN.md must not combine check-host.py with --phase")

    # -- SKILL.md --------------------------------------------------------

    def test_skill_md_no_check_host_phase(self) -> None:
        text = _read(SKILL_MD)
        bad = re.findall(r"check-host\.py\b.*?--phase\b", text)
        self.assertEqual(bad, [],
                         "SKILL.md must not combine check-host.py with --phase")

    # -- every webbuilder/references/*.md --------------------------------

    def test_ref_interface_design_no_check_host_phase(self) -> None:
        text = _ref("interface-design.md")
        bad = re.findall(r"check-host\.py\b.*?--phase\b", text)
        self.assertEqual(bad, [],
                         "interface-design.md must not combine check-host.py with --phase")

    def test_ref_multi_agent_no_check_host_phase(self) -> None:
        text = _ref("multi-agent-orchestration.md")
        bad = re.findall(r"check-host\.py\b.*?--phase\b", text)
        self.assertEqual(bad, [],
                         "multi-agent-orchestration.md must not combine check-host.py with --phase")

    def test_ref_product_guide_no_check_host_phase(self) -> None:
        text = _ref("project-results-and-usage.md")
        bad = re.findall(r"check-host\.py\b.*?--phase\b", text)
        self.assertEqual(bad, [],
                         "project-results-and-usage.md must not combine check-host.py with --phase")

    def test_all_refs_no_check_host_phase(self) -> None:
        """Sweep every references/*.md for the forbidden pattern."""
        for md in sorted(REFERENCES.glob("*.md")):
            text = md.read_text(encoding="utf-8")
            bad = re.findall(r"check-host\.py\b.*?--phase\b", text)
            self.assertEqual(bad, [],
                             f"{md.name} must not combine check-host.py with --phase")


# ===================================================================
# 7. Product guide must document check-host.py --target and
#    check-state.py --phase host|initialization|ui separately
# ===================================================================
class CheckHostAndCheckStateCoverageTests(unittest.TestCase):
    """The product guide must show check-host.py --target (its actual CLI)
    and must document check-state.py --phase host, initialization, ui
    as the three readiness gates."""

    GUIDE = REFERENCES / "project-results-and-usage.md"

    def _guide(self) -> str:
        return _read(self.GUIDE)

    def test_guide_documents_check_host_target(self) -> None:
        """check-host.py must appear with --target, not --phase."""
        text = self._guide()
        self.assertRegex(text, r"check-host\.py\b.*?--target\b",
                         "Guide must document check-host.py --target")

    def test_guide_documents_check_state_phase_host(self) -> None:
        text = self._guide()
        self.assertRegex(text, r"check-state\.py\b.*?--phase\b.*?host\b",
                         "Guide must document check-state.py --phase host")

    def test_guide_documents_check_state_phase_initialization(self) -> None:
        text = self._guide()
        self.assertRegex(text, r"check-state\.py\b.*?--phase\b.*?initialization\b",
                         "Guide must document check-state.py --phase initialization")

    def test_guide_documents_check_state_phase_ui(self) -> None:
        text = self._guide()
        self.assertRegex(text, r"check-state\.py\b.*?--phase\b.*?ui\b",
                         "Guide must document check-state.py --phase ui")


# ===================================================================
# 8. Product guide must not contain '当前版本'
# ===================================================================
class ProductGuideNoVersionFramingTests(unittest.TestCase):
    """The product guide must not use '当前版本' (current version) framing."""

    GUIDE = REFERENCES / "project-results-and-usage.md"

    def test_guide_no_dangqian_banben(self) -> None:
        text = _read(self.GUIDE)
        self.assertNotIn("当前版本", text,
                         "Product guide must not use '当前版本' version framing")


# ===================================================================
# 9. READMEs and product guide must not use 'spec2web-smoke' directory
# ===================================================================
class SmokeDirectoryNameTests(unittest.TestCase):
    """The temp smoke directory must be 'webbuilder-smoke', not 'spec2web-smoke'."""

    def test_readme_zh_no_spec2web_smoke(self) -> None:
        text = _read(README_ZH)
        self.assertNotIn("spec2web-smoke", text,
                         "README.md must use webbuilder-smoke, not spec2web-smoke")

    def test_readme_en_no_spec2web_smoke(self) -> None:
        text = _read(README_EN)
        self.assertNotIn("spec2web-smoke", text,
                         "README_EN.md must use webbuilder-smoke, not spec2web-smoke")

    def test_product_guide_no_spec2web_smoke(self) -> None:
        text = _ref("project-results-and-usage.md")
        self.assertNotIn("spec2web-smoke", text,
                         "project-results-and-usage.md must use webbuilder-smoke, not spec2web-smoke")


# ===================================================================
# 10. --explicit-secrets is NOT a CLI flag; redaction.status never
#     writes "failed" in the normal capture path
# ===================================================================
class ExplicitSecretsNotAFlagTests(unittest.TestCase):
    """--explicit-secrets exists only on the internal capture_command_evidence()
    function in evidence_core.py.  capture-evidence.py's argparse does NOT
    expose it.  Documentation must not present it as a CLI flag."""

    # -- capture-evidence.py must not define --explicit-secrets ------------

    def test_script_has_no_explicit_secrets_flag(self) -> None:
        source = _read(CAPTURE_EVIDENCE)
        self.assertNotIn('"--explicit-secrets"', source,
                         "capture-evidence.py must not define --explicit-secrets")

    # -- core docs that must not present --explicit-secrets as a CLI flag --

    def test_skill_md_no_cli_explicit_secrets(self) -> None:
        text = _read(SKILL_MD)
        # Reject the pattern "capture-evidence.py ... --explicit-secrets" or
        # "Pass --explicit-secrets" in the capture-evidence context.
        self.assertNotRegex(
            text,
            r"capture-evidence\.py\b.*?--explicit-secrets\b",
            "SKILL.md must not present --explicit-secrets as a capture-evidence.py CLI flag",
        )
        self.assertNotRegex(
            text,
            r"(?i)pass\s+`?--explicit-secrets\b",
            "SKILL.md must not instruct users to pass --explicit-secrets as a CLI flag",
        )

    def test_delivery_checklist_no_cli_explicit_secrets(self) -> None:
        text = _ref("delivery-checklist.md")
        self.assertNotRegex(
            text,
            r"capture-evidence\.py\b.*?--explicit-secrets\b",
            "delivery-checklist.md must not present --explicit-secrets as a capture-evidence.py CLI flag",
        )
        self.assertNotRegex(
            text,
            r"(?i)(?:use|pass)\s+`?--explicit-secrets\b",
            "delivery-checklist.md must not instruct users to use/pass --explicit-secrets as a CLI flag",
        )

    def test_project_guide_no_cli_explicit_secrets(self) -> None:
        text = _ref("project-results-and-usage.md")
        self.assertNotRegex(
            text,
            r"capture-evidence\.py\b.*?--explicit-secrets\b",
            "project-results-and-usage.md must not present --explicit-secrets as a capture-evidence.py CLI flag",
        )
        self.assertNotRegex(
            text,
            r"--explicit-secrets\b",
            "project-results-and-usage.md must not reference --explicit-secrets as a CLI flag",
        )

    def test_multi_agent_no_cli_explicit_secrets(self) -> None:
        text = _ref("multi-agent-orchestration.md")
        self.assertNotRegex(
            text,
            r"capture-evidence\.py\b.*?--explicit-secrets\b",
            "multi-agent-orchestration.md must not present --explicit-secrets as a CLI flag",
        )

    # -- sweep all references/*.md -----------------------------------------

    def test_all_refs_no_explicit_secrets_cli_flag(self) -> None:
        """No references/*.md file may present --explicit-secrets as a CLI flag."""
        for md in sorted(REFERENCES.glob("*.md")):
            text = md.read_text(encoding="utf-8")
            # Match "capture-evidence.py ... --explicit-secrets" on same line
            bad = re.findall(r"capture-evidence\.py\b.*?--explicit-secrets\b", text)
            self.assertEqual(bad, [],
                             f"{md.name} must not present --explicit-secrets as a CLI flag")


class RedactionStatusFailedTests(unittest.TestCase):
    """The normal capture-evidence CLI path always writes redaction.status
    "passed" after applying built-in redaction.  There is no code path that
    writes redaction.status "failed".  Documentation must not claim otherwise."""

    def test_evidence_core_always_writes_passed(self) -> None:
        """Sanity: the implementation always writes redaction.status 'passed'."""
        source = _read(ROOT / "webbuilder" / "scripts" / "evidence_core.py")
        self.assertRegex(source, r'"redaction".*"status".*"passed"')
        self.assertNotRegex(source, r'"redaction".*"status".*"failed"')

    def test_skill_md_no_redaction_failed_claim(self) -> None:
        text = _read(SKILL_MD)
        self.assertNotRegex(
            text,
            r"(?i)redaction.*fail.*manifest.*redaction\.status.*failed",
            "SKILL.md must not claim redaction failure writes redaction.status: failed",
        )
        self.assertNotRegex(
            text,
            r"redaction\.status:\s*failed",
            "SKILL.md must not mention redaction.status: failed",
        )

    def test_delivery_checklist_no_redaction_failed_claim(self) -> None:
        text = _ref("delivery-checklist.md")
        self.assertNotRegex(
            text,
            r"redaction\.status:\s*failed",
            "delivery-checklist.md must not mention redaction.status: failed",
        )
        self.assertNotRegex(
            text,
            r"(?i)redaction fail.*redaction\.status.*failed",
            "delivery-checklist.md must not claim redaction failure writes redaction.status: failed",
        )

    def test_project_guide_no_redaction_failed_claim(self) -> None:
        text = _ref("project-results-and-usage.md")
        self.assertNotRegex(
            text,
            r"redaction\.status:\s*failed",
            "project-results-and-usage.md must not mention redaction.status: failed",
        )

    # -- sweep all references/*.md -----------------------------------------

    def test_all_refs_no_redaction_status_failed(self) -> None:
        """No references/*.md may claim redaction.status: failed."""
        for md in sorted(REFERENCES.glob("*.md")):
            text = md.read_text(encoding="utf-8")
            matches = re.findall(r"redaction\.status:\s*failed", text)
            self.assertEqual(matches, [],
                             f"{md.name} must not mention redaction.status: failed")


if __name__ == "__main__":
    unittest.main()
