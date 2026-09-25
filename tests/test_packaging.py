import ast
import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from PIL import Image
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# Register packaging.generate_icon in sys.modules so standard import works
# without colliding with third-party PyPI 'packaging' package.
_icon_py = REPO_ROOT / "packaging" / "generate_icon.py"
if "packaging.generate_icon" not in sys.modules and _icon_py.is_file():
    _spec = importlib.util.spec_from_file_location("packaging.generate_icon", str(_icon_py))
    _mod = importlib.util.module_from_spec(_spec)
    sys.modules["packaging.generate_icon"] = _mod
    _spec.loader.exec_module(_mod)


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


def test_packaging_files_exist():
    """Tüm paketleme dosyalarının mevcut olduğunu doğrular."""
    assert (REPO_ROOT / "packaging" / "generate_icon.py").is_file()
    assert (REPO_ROOT / "packaging" / "run_gui.py").is_file()
    assert (REPO_ROOT / "packaging" / "kast.spec").is_file()
    assert (REPO_ROOT / "packaging" / "assets" / "kast_icon.png").is_file()
    assert (REPO_ROOT / "packaging" / "assets" / "kast.ico").is_file()


def test_generate_icon_from_source(tmp_path):
    """Mevcut bir kaynaktan çoklu çözünürlüklü .ico dosyasının başarıyla üretildiğini doğrular."""
    from packaging.generate_icon import generate_icon, ICON_SIZES

    source_png = REPO_ROOT / "packaging" / "assets" / "kast_icon.png"
    out_ico = tmp_path / "test_source.ico"

    result = generate_icon(source_path=str(source_png), output_path=str(out_ico))
    assert result == str(out_ico)
    assert out_ico.is_file()
    assert out_ico.stat().st_size > 0

    with Image.open(str(out_ico)) as img:
        assert img.format == "ICO"
        ico_sizes = getattr(img, "ico", None).sizes() if hasattr(img, "ico") else {img.size}
        for size in [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]:
            assert size in ico_sizes


def test_generate_icon_fallback(tmp_path):
    """Kaynak resim bulunamadığında geometrik fallback ikonu üretildiğini doğrular."""
    from packaging.generate_icon import generate_icon

    non_existent = tmp_path / "missing.png"
    out_ico = tmp_path / "fallback.ico"

    result = generate_icon(source_path=str(non_existent), output_path=str(out_ico))
    assert result == str(out_ico)
    assert out_ico.is_file()
    assert out_ico.stat().st_size > 0

    with Image.open(str(out_ico)) as img:
        assert img.format == "ICO"
        ico_sizes = getattr(img, "ico", None).sizes() if hasattr(img, "ico") else {img.size}
        for size in [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]:
            assert size in ico_sizes


def test_generate_icon_cli(tmp_path):
    """generate_icon.py betiğinin CLI argümanlarıyla başarıyla çalıştığını doğrular."""
    out_ico = tmp_path / "cli_test.ico"
    cmd = [
        sys.executable,
        str(REPO_ROOT / "packaging" / "generate_icon.py"),
        "--source",
        str(REPO_ROOT / "packaging" / "assets" / "kast_icon.png"),
        "--output",
        str(out_ico),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert out_ico.is_file()
    assert out_ico.stat().st_size > 0


def test_run_gui_syntax():
    """packaging/run_gui.py sözdizimi ve modül yapısını doğrular."""
    run_gui_path = REPO_ROOT / "packaging" / "run_gui.py"
    assert run_gui_path.is_file()

    content = run_gui_path.read_text(encoding="utf-8")
    tree = ast.parse(content, filename=str(run_gui_path))
    assert tree is not None
    assert "launch_gui" in content
    assert "sys.exit" in content


def test_kast_spec_syntax():
    """packaging/kast.spec dosyasının sözdizimini ve temel PyInstaller ayarlarını doğrular."""
    spec_path = REPO_ROOT / "packaging" / "kast.spec"
    assert spec_path.is_file()

    content = spec_path.read_text(encoding="utf-8")
    tree = ast.parse(content, filename=str(spec_path))
    assert tree is not None

    # Gerekli konfigürasyon parçalarının yer aldığını doğrula
    assert "Analysis" in content
    assert "run_gui.py" in content
    assert "KastStudio" in content
    assert "console=False" in content
    assert "kast.ico" in content
    assert "PySide6.QtCore" in content
    assert "PySide6.QtGui" in content
    assert "PySide6.QtWidgets" in content
    assert "docx" in content
    assert "pdfplumber" in content
    assert "tkinter" in content
    assert "icuuc.dll" in content


def test_gui_window_has_icon(qapp):
    """KastStudioWindow örneklendiğinde pencere ikonunun yüklendiğini doğrular."""
    from src.gui import KastStudioWindow

    window = KastStudioWindow()
    icon = window.windowIcon()
    assert not icon.isNull()
