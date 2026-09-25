from pathlib import Path
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW_FILE = REPO_ROOT / ".github" / "workflows" / "release-windows.yml"


def load_workflow() -> dict:
    """Helper function to read and parse the release-windows.yml workflow file."""
    assert WORKFLOW_FILE.is_file(), f"Workflow file not found at: {WORKFLOW_FILE}"
    content = WORKFLOW_FILE.read_text(encoding="utf-8")
    parsed = yaml.safe_load(content)
    assert isinstance(parsed, dict), "Parsed workflow YAML must be a dictionary"
    return parsed


def test_workflow_file_exists():
    """.github/workflows/release-windows.yml dosyasının mevcut olduğunu doğrular."""
    assert WORKFLOW_FILE.is_file(), f"Workflow dosyası bulunamadı: {WORKFLOW_FILE}"


def test_workflow_syntax_and_triggers():
    """Workflow YAML sözdizimini, adını ve tetikleyicilerini doğrular."""
    workflow = load_workflow()

    # Name check
    assert workflow.get("name") == "Build and Release Windows Packages"

    # Triggers check (YAML boolean 'on' or string 'on')
    triggers = workflow.get("on") or workflow.get(True)
    assert triggers is not None, "Workflow 'on' tetikleyicisi tanımlanmamış."

    # Push tag trigger
    assert "push" in triggers, "'push' tetikleyicisi eksik."
    push_triggers = triggers["push"]
    assert "tags" in push_triggers, "'push.tags' tetikleyicisi eksik."
    assert any("v*" in tag for tag in push_triggers["tags"]), "Tag tetikleyicisi 'v*' içermeli."

    # workflow_dispatch trigger
    assert "workflow_dispatch" in triggers, "'workflow_dispatch' tetikleyicisi eksik."
    dispatch = triggers["workflow_dispatch"]
    assert dispatch is not None, "workflow_dispatch parametresi boş olamaz."
    assert "inputs" in dispatch, "'inputs' anahtarı workflow_dispatch altında tanımlanmalı."
    inputs = dispatch["inputs"]
    assert "version" in inputs, "'version' girdisi workflow_dispatch altında tanımlanmalı."
    assert inputs["version"].get("default") == "2.1.0", "Varsayılan sürüm '2.1.0' olmalı."


def test_workflow_permissions_and_runner():
    """Workflow izinlerini ve koşucu (runner) ortamını doğrular."""
    workflow = load_workflow()

    # Permissions check (top-level or job-level)
    permissions = workflow.get("permissions")
    jobs = workflow.get("jobs", {})
    assert "build-windows" in jobs, "'build-windows' işi (job) tanımlanmalı."
    job = jobs["build-windows"]

    job_permissions = job.get("permissions")
    has_write_perm = (
        (permissions and permissions.get("contents") == "write") or
        (job_permissions and job_permissions.get("contents") == "write")
    )
    assert has_write_perm, "GitHub Releases için 'contents: write' izni gereklidir."

    # Runner check
    assert job.get("runs-on") == "windows-latest", "Runner ortamı 'windows-latest' olmalı."


def test_workflow_build_steps():
    """Derleme adımlarının sıralamasını ve parametrelerini doğrular."""
    workflow = load_workflow()
    jobs = workflow.get("jobs", {})
    job = jobs.get("build-windows", {})
    steps = job.get("steps", [])

    assert len(steps) >= 10, f"En az 10 adım bekleniyordu, bulunan: {len(steps)}"

    # 1. Checkout
    checkout_step = next((s for s in steps if "actions/checkout" in str(s.get("uses", ""))), None)
    assert checkout_step is not None, "actions/checkout adımı eksik."
    assert checkout_step.get("with", {}).get("fetch-depth") == 0, "Checkout fetch-depth: 0 olmalı."

    # 2. Determine Version
    version_step = next(
        (s for s in steps if "version" in s.get("name", "").lower() or "version" in s.get("run", "").lower()),
        None
    )
    assert version_step is not None, "VERSION belirleme adımı eksik."
    assert "$env:GITHUB_ENV" in version_step.get("run", ""), "Version GITHUB_ENV ortamına yazılmalı."

    # 3. Setup Python
    python_step = next((s for s in steps if "actions/setup-python" in str(s.get("uses", ""))), None)
    assert python_step is not None, "actions/setup-python adımı eksik."
    py_with = python_step.get("with", {})
    assert str(py_with.get("python-version")) == "3.11", "Python versiyonu 3.11 olmalı."
    assert py_with.get("cache") == "pip", "Python pip önbelleği (cache: pip) etkin olmalı."

    # 4. Install Dependencies
    install_step = next(
        (s for s in steps if "pip install" in str(s.get("run", ""))),
        None
    )
    assert install_step is not None, "Bağımlılık yükleme adımı eksik."
    install_run = install_step["run"]
    assert "requirements.txt" in install_run, "requirements.txt kurulmalı."
    assert "pyinstaller" in install_run, "pyinstaller kurulmalı."
    assert "Pillow" in install_run, "Pillow kurulmalı."

    # 5. Generate Icon
    icon_step = next(
        (s for s in steps if "generate_icon.py" in str(s.get("run", ""))),
        None
    )
    assert icon_step is not None, "generate_icon.py çalıştırma adımı eksik."

    # 6. PyInstaller
    pyinstaller_step = next(
        (s for s in steps if "pyinstaller" in str(s.get("run", "")) and "kast.spec" in str(s.get("run", ""))),
        None
    )
    assert pyinstaller_step is not None, "PyInstaller kast.spec derleme adımı eksik."
    assert "--noconfirm" in pyinstaller_step["run"], "PyInstaller --noconfirm parametresi içermeli."

    # 7. Pack Portable ZIP
    zip_step = next(
        (s for s in steps if "Compress-Archive" in str(s.get("run", ""))),
        None
    )
    assert zip_step is not None, "Compress-Archive ile taşınabilir ZIP paketleme adımı eksik."
    assert "KastStudio" in zip_step["run"], "ZIP kaynağı KastStudio olmalı."
    assert "Windows-Portable.zip" in zip_step["run"], "ZIP hedefi Windows-Portable.zip içermeli."

    # 8. Install Inno Setup
    choco_step = next(
        (s for s in steps if "choco install innosetup" in str(s.get("run", ""))),
        None
    )
    assert choco_step is not None, "Chocolatey ile Inno Setup kurulum adımı eksik."

    # 9. Compile Inno Setup
    iscc_step = next(
        (s for s in steps if "iscc.exe" in str(s.get("run", ""))),
        None
    )
    assert iscc_step is not None, "Inno Setup iscc.exe derleme adımı eksik."
    assert "MyAppVersion" in iscc_step["run"], "iscc.exe /DMyAppVersion parametresi içermeli."
    assert "installer.iss" in iscc_step["run"], "installer.iss derlenmeli."

    # 10. Generate SHA256 Checksums
    checksum_step = next(
        (s for s in steps if "Get-FileHash" in str(s.get("run", ""))),
        None
    )
    assert checksum_step is not None, "Get-FileHash ile SHA256 sağlama adımı eksik."
    assert "checksums.txt" in checksum_step["run"], "checksums.txt dosyası üretilmeli."

    # 11. Publish Release
    release_step = next(
        (s for s in steps if "action-gh-release" in str(s.get("uses", ""))),
        None
    )
    assert release_step is not None, "action-gh-release adımı eksik."
    release_with = release_step.get("with", {})
    release_files = str(release_with.get("files", ""))
    assert "Setup.exe" in release_files, "Release Setup.exe içermeli."
    assert "Windows-Portable.zip" in release_files, "Release Portable.zip içermeli."
    assert "checksums.txt" in release_files, "Release checksums.txt içermeli."
    assert release_with.get("generate_release_notes") is True, "generate_release_notes: true olmalı."


def test_workflow_step_shells():
    """Özel kabuk (powershell/pwsh ve cmd) kullanan adımların doğruluğunu denetler."""
    workflow = load_workflow()
    steps = workflow["jobs"]["build-windows"]["steps"]

    pwsh_steps = [s for s in steps if s.get("shell") == "pwsh"]
    cmd_steps = [s for s in steps if s.get("shell") == "cmd"]

    # At least version determination, zip packaging, and checksum generation use pwsh
    assert len(pwsh_steps) >= 3, "En az 3 adım 'shell: pwsh' kullanmalıdır."

    # Inno Setup compilation must use cmd
    assert any("iscc.exe" in s.get("run", "") for s in cmd_steps), "Inno Setup derleme adımı 'shell: cmd' kullanmalıdır."


def test_workflow_release_condition_and_naming():
    """GitHub Release adımının koşulunu ve adlandırma şablonunu denetler."""
    workflow = load_workflow()
    steps = workflow["jobs"]["build-windows"]["steps"]

    release_step = next(s for s in steps if "action-gh-release" in str(s.get("uses", "")))
    condition = release_step.get("if", "")
    assert "refs/tags/" in condition, "Release adımı etiket (tag) kontrolü yapmalıdır."
    assert "workflow_dispatch" in condition, "Release adımı workflow_dispatch kontrolü yapmalıdır."

    name = release_step.get("with", {}).get("name", "")
    assert "Kast Studio v" in name, "Release adı 'Kast Studio v...' formatında olmalıdır."
    assert "VERSION" in name, "Release adı dinamik VERSION içermelidir."
