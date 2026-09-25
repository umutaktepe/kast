"""Tests for install.sh and install.ps1 installation scripts."""

import os
import shutil
import subprocess
import pytest

REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INSTALL_SH = os.path.join(REPO_DIR, "install.sh")
INSTALL_PS1 = os.path.join(REPO_DIR, "install.ps1")
BASH_PATH = shutil.which("bash") or "/bin/bash"


def test_install_sh_syntax():
    """Verify install.sh has valid bash syntax."""
    res = subprocess.run([BASH_PATH, "-n", INSTALL_SH], capture_output=True, text=True)
    assert res.returncode == 0, f"Bash syntax error in {INSTALL_SH}:\n{res.stderr}"


def test_install_sh_checks_libreoffice():
    """Verify install.sh checks for soffice / libreoffice before attempting install."""
    with open(INSTALL_SH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "soffice" in content, "install.sh should check for soffice binary"
    assert "libreoffice" in content, "install.sh should check for libreoffice binary"
    assert "command -v soffice" in content or "type soffice" in content or "which soffice" in content


def test_install_sh_package_managers():
    """Verify install.sh detects dnf, apt-get, pacman, zypper and uses appropriate install commands."""
    with open(INSTALL_SH, "r", encoding="utf-8") as f:
        content = f.read()

    for pm in ["dnf", "apt-get", "pacman", "zypper"]:
        assert pm in content, f"install.sh should handle package manager: {pm}"

    assert "libreoffice-writer" in content, "install.sh should install libreoffice-writer"
    assert "libreoffice-fresh" in content, "install.sh should install libreoffice-fresh on pacman"
    assert "sudo" in content, "install.sh should use sudo for system package managers"


def get_libreoffice_install_block():
    """Extract LibreOffice detection and installation block from install.sh."""
    with open(INSTALL_SH, "r", encoding="utf-8") as f:
        content = f.read()
    start_marker = "# 2.5 LibreOffice Kontrolü ve Kurulumu"
    end_marker = "# 3. Bağımlılıkların yüklenmesi"
    assert start_marker in content, "Start marker for Step 2.5 not found in install.sh"
    assert end_marker in content, "End marker for Step 3 not found in install.sh"
    block = content.split(start_marker)[1].split(end_marker)[0]
    header = 'GREEN=""\nBLUE=""\nYELLOW=""\nRED=""\nNC=""\n'
    return header + block


def run_install_sh_block(mock_functions):
    """Helper to execute the extracted install.sh block with bash mock functions."""
    script = f"{mock_functions}\n{get_libreoffice_install_block()}"
    res = subprocess.run([BASH_PATH, "-c", script], capture_output=True, text=True)
    return res


def test_install_sh_execution_soffice_found():
    """When soffice exists, installer should detect it without installing."""
    mock = """
    command() {
        if [ "$2" = "soffice" ]; then return 0; fi
        builtin command "$@"
    }
    """
    res = run_install_sh_block(mock)
    assert res.returncode == 0
    assert "LibreOffice tespit edildi" in res.stdout


def test_install_sh_execution_libreoffice_found():
    """When libreoffice exists, installer should detect it without installing."""
    mock = """
    command() {
        if [ "$2" = "soffice" ]; then return 1; fi
        if [ "$2" = "libreoffice" ]; then return 0; fi
        builtin command "$@"
    }
    """
    res = run_install_sh_block(mock)
    assert res.returncode == 0
    assert "LibreOffice tespit edildi" in res.stdout


@pytest.mark.parametrize("active_pm,expected_command", [
    ("dnf", "dnf install -y libreoffice-writer"),
    ("apt-get", "apt-get install -y libreoffice-writer"),
    ("pacman", "pacman -S --noconfirm libreoffice-fresh"),
    ("zypper", "zypper install -y libreoffice-writer"),
])
def test_install_sh_execution_pm_branches(active_pm, expected_command):
    """When soffice is missing, installer should trigger the corresponding package manager command."""
    mock = f"""
    sudo() {{
        echo "MOCK_SUDO: $*"
        return 0
    }}
    command() {{
        if [ "$2" = "soffice" ] || [ "$2" = "libreoffice" ]; then return 1; fi
        if [ "$2" = "{active_pm}" ]; then return 0; fi
        if [ "$2" = "dnf" ] || [ "$2" = "apt-get" ] || [ "$2" = "pacman" ] || [ "$2" = "zypper" ]; then return 1; fi
        builtin command "$@"
    }}
    """
    res = run_install_sh_block(mock)
    assert res.returncode == 0
    assert "MOCK_SUDO:" in res.stdout
    assert expected_command in res.stdout


def test_install_sh_execution_no_pm_warning():
    """When soffice and all known package managers are missing, installer should warn user."""
    mock = """
    command() {
        if [ "$2" = "soffice" ] || [ "$2" = "libreoffice" ]; then return 1; fi
        if [ "$2" = "dnf" ] || [ "$2" = "apt-get" ] || [ "$2" = "pacman" ] || [ "$2" = "zypper" ]; then return 1; fi
        builtin command "$@"
    }
    """
    res = run_install_sh_block(mock)
    assert res.returncode == 0
    assert "Paket yöneticisi otomatik tespit edilemedi" in res.stdout


def test_install_ps1_no_dxpdf():
    """Verify dxpdf is removed completely from install.ps1."""
    with open(INSTALL_PS1, "r", encoding="utf-8") as f:
        content = f.read()

    assert "dxpdf" not in content.lower(), "install.ps1 should not reference dxpdf"


def test_install_ps1_word_and_libreoffice_checks():
    """Verify install.ps1 checks for Word COM object and soffice.exe, and falls back to winget."""
    with open(INSTALL_PS1, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Word.Application" in content, "install.ps1 should check for Word COM object"
    assert "soffice" in content, "install.ps1 should check for soffice.exe"
    assert "winget" in content, "install.ps1 should check for winget"
    assert "TheDocumentFoundation.LibreOffice" in content, (
        "install.ps1 should install TheDocumentFoundation.LibreOffice via winget"
    )
    assert "--silent" in content, "install.ps1 winget command should include --silent"
    assert "--accept-package-agreements" in content, "install.ps1 should accept package agreements"
    assert "--accept-source-agreements" in content, "install.ps1 should accept source agreements"


def test_kast_cmd_forwards_arguments_for_gui_and_cli():
    """kast.cmd başlatıcısının tüm argümanları (%*) kast.py'ye ilettiğini doğrular."""
    assert os.path.exists("kast.cmd")
    with open("kast.cmd", "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    assert "%*" in content
    assert "kast.py" in content


def test_install_ps1_generates_single_launcher_and_terminal_gui_instructions():
    """Verify install.ps1 generates only kast.cmd (no extra app) and lists kast --gui."""
    with open(INSTALL_PS1, "r", encoding="utf-8") as f:
        content = f.read()
    assert "kast.cmd" in content
    assert "kast-gui.cmd" not in content, "install.ps1 should not create extra kast-gui.cmd launcher"
    assert "kast --gui" in content
    assert "PySide6" in content


def test_install_sh_checks_pyside6_and_terminal_gui_instructions():
    """Verify install.sh checks PySide6 dependency and lists kast --gui in completion message."""
    with open(INSTALL_SH, "r", encoding="utf-8") as f:
        content = f.read()
    assert "PySide6" in content, "install.sh should check for PySide6"
    assert "kast --gui" in content, "install.sh should inform user about kast --gui"

