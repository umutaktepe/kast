import os
import re
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALLER_ISS = REPO_ROOT / "packaging" / "installer.iss"


def load_installer_content() -> str:
    """Helper to read packaging/installer.iss content."""
    assert INSTALLER_ISS.is_file(), f"installer.iss not found at: {INSTALLER_ISS}"
    return INSTALLER_ISS.read_text(encoding="utf-8")


def parse_inno_sections(content: str) -> dict[str, list[str]]:
    """Simple parser dividing Inno Setup script by [Section] headers."""
    sections: dict[str, list[str]] = {}
    current_section = ""
    for line in content.splitlines():
        line_clean = line.strip()
        if line_clean.startswith("[") and line_clean.endswith("]"):
            current_section = line_clean.upper()
            sections[current_section] = []
        elif current_section:
            sections[current_section].append(line)
    return sections


def test_installer_file_exists():
    """packaging/installer.iss dosyasının mevcut olduğunu doğrular."""
    assert INSTALLER_ISS.is_file(), "packaging/installer.iss dosyası bulunamadı."


def test_installer_sections_exist():
    """Inno Setup scriptinin tüm zorunlu bölümlerini içerdiğini doğrular."""
    content = load_installer_content()
    sections = parse_inno_sections(content)

    required_sections = [
        "[SETUP]",
        "[LANGUAGES]",
        "[TASKS]",
        "[FILES]",
        "[ICONS]",
        "[RUN]",
        "[CODE]",
    ]
    for section in required_sections:
        assert section in sections, f"Zorunlu bölüm eksik: {section}"


def test_installer_metadata_and_icons():
    """Kurulum meta verilerini, sürümünü, AppId'sini ve ikon bağlantılarını doğrular."""
    content = load_installer_content()

    # App Defines
    assert '#define MyAppName "Kast Studio"' in content
    assert '#define MyAppVersion "2.1.0"' in content
    assert '#define MyAppPublisher "Umut Aktepe"' in content
    assert '#define MyAppURL "https://github.com/umutaktepe/Kast"' in content
    assert '#define MyAppExeName "KastStudio.exe"' in content

    # [Setup] directives
    assert "D37E6F90-7F89-4A73-98C3-2A676E4B15C0" in content
    assert "AppName={#MyAppName}" in content
    assert "AppVersion={#MyAppVersion}" in content
    assert "DefaultDirName={autopf}\\{#MyAppName}" in content
    assert "DefaultGroupName={#MyAppName}" in content
    assert "OutputDir=..\\dist" in content
    assert "OutputBaseFilename=Kast-v{#MyAppVersion}-Setup" in content
    assert re.search(r"SetupIconFile=assets[\\/]kast\.ico", content)
    assert re.search(r"UninstallDisplayIcon=\{app\}[\\/]assets[\\/]kast\.ico", content)
    assert "Compression=lzma2/ultra64" in content
    assert "SolidCompression=yes" in content
    assert "WizardStyle=modern" in content
    assert "ArchitecturesInstallIn64BitMode=x64" in content


def test_languages_and_tasks():
    """Türkçe ve İngilizce dil dosyaları ile masaüstü kısayol görevinin tanımlandığını doğrular."""
    content = load_installer_content()
    sections = parse_inno_sections(content)

    languages_text = "\n".join(sections.get("[LANGUAGES]", []))
    assert 'Name: "turkish"' in languages_text
    assert "Turkish.isl" in languages_text
    assert 'Name: "english"' in languages_text
    assert "Default.isl" in languages_text

    tasks_text = "\n".join(sections.get("[TASKS]", []))
    assert 'Name: "desktopicon"' in tasks_text


def test_files_and_icons_configuration():
    """Kurulum dosyaları ve kısayol simgesi eşleşmelerini doğrular."""
    content = load_installer_content()
    sections = parse_inno_sections(content)

    files_text = "\n".join(sections.get("[FILES]", []))
    assert r'Source: "..\dist\KastStudio\*"' in files_text or r"Source: ..\dist\KastStudio\*" in files_text
    assert r'Source: "assets\kast.ico"' in files_text or r"Source: assets\kast.ico" in files_text
    assert r'DestDir: "{app}\assets"' in files_text or r"DestDir: {app}\assets" in files_text

    icons_text = "\n".join(sections.get("[ICONS]", []))
    assert "{group}\\{#MyAppName}" in icons_text
    assert "{autodesktop}\\{#MyAppName}" in icons_text
    assert "kast.ico" in icons_text
    assert "Tasks: desktopicon" in icons_text
    assert "{uninstallexe}" in icons_text


def test_office_detection_pascal_logic():
    """Pascal [Code] bloğunda MS Word ve LibreOffice tespit fonksiyonlarını doğrular."""
    content = load_installer_content()
    sections = parse_inno_sections(content)
    code_text = "\n".join(sections.get("[CODE]", []))

    # Fonksiyon imzaları
    assert "function IsWordInstalled(): Boolean;" in code_text or "function IsWordInstalled : Boolean;" in code_text
    assert "function IsLibreOfficeInstalled(): Boolean;" in code_text or "function IsLibreOfficeInstalled : Boolean;" in code_text

    # Word kontrolleri (Registry ve COM)
    assert "Winword.exe" in code_text
    assert "Word.Application" in code_text
    assert "HKLM" in code_text or "HKCU" in code_text or "HKCR" in code_text

    # LibreOffice kontrolleri (Registry ve bilinen dosya yolları)
    assert "SOFTWARE\\LibreOffice\\UNO\\InstallPath" in code_text or "LibreOffice" in code_text
    assert "The Document Foundation" in code_text
    assert "soffice.exe" in code_text


def test_silent_install_pascal_logic():
    """LibreOffice yoksa sessiz arka plan kurulumu yapan Pascal adımlarını doğrular."""
    content = load_installer_content()
    sections = parse_inno_sections(content)
    code_text = "\n".join(sections.get("[CODE]", []))

    # CurStepChanged ve ssPostInstall adımı
    assert "procedure CurStepChanged(CurStep: TSetupStep);" in code_text or "CurStepChanged" in code_text
    assert "ssPostInstall" in code_text
    assert "IsWordInstalled" in code_text
    assert "IsLibreOfficeInstalled" in code_text

    # 1. Öncelik: winget sessiz kurulum komutu
    assert "TheDocumentFoundation.LibreOffice" in code_text
    assert "--silent" in code_text or "/qn" in code_text
    assert "--accept-package-agreements" in code_text
    assert "--accept-source-agreements" in code_text
    assert "SW_HIDE" in code_text
    assert "ewWaitUntilTerminated" in code_text

    # 2. Öncelik: powershell MSI indirme ve sessiz msiexec kurulum fallback
    assert "powershell.exe" in code_text
    assert "msiexec" in code_text
    assert "/qn" in code_text
    assert "/norestart" in code_text
