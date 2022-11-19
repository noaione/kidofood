import subprocess as sp
import sys
from pathlib import Path
from typing import Optional

to_be_linted = ["internals", "routes", "app.py"]


def check_license_header(file: Path) -> bool:
    # Find the MIT License header on file that's not __init__.py
    with file.open("r") as fp:
        # Check until line 10
        for idx, line in enumerate(fp):
            if idx == 10:
                break
            if file.name == "__init__.py":
                if line.startswith(":copyright:") or line.startswith(":license:"):
                    return True
                return True
            else:
                if line.startswith("MIT License"):
                    return True
    return False


def check_future_annotations(file: Path) -> bool:
    # Check if the file has __future__ import
    if file.name == "__init__.py":
        return True
    with file.open("r") as fp:
        for line in fp:
            if line.startswith("from __future__ import annotations"):
                return True
    return False


current_path = Path(__file__).absolute().parent.parent  # root dir
venv_dir = [
    current_path / ".venv",
    current_path / "venv",
    current_path / "env",
]
selected_venv_dir: Optional[Path] = None
for venv in venv_dir:
    if venv.exists():
        selected_venv_dir = venv

if selected_venv_dir is None:
    raise RuntimeError("No virtual environment found")


script_path = selected_venv_dir / "Scripts" if sys.platform == "win32" else selected_venv_dir / "bin"

print(f"[*] Running tests at {current_path}")

print("[*] Running isort test...")
isort_res = sp.Popen([script_path / "isort", "-c"] + to_be_linted).wait()
print("[*] Running flake8 test...")
flake8_res = sp.Popen(
    [script_path / "flake8", "--statistics", "--show-source", "--benchmark", "--tee"] + to_be_linted
).wait()

results = [(isort_res, "isort"), (flake8_res, "flake8")]
any_error = False

for res in results:
    if res[0] != 0:
        print(f"[-] {res[1]} returned an non-zero code")
        any_error = True
    else:
        print(f"[+] {res[1]} passed")


print("[*] Running license check and future annotations test...")
any_license_future_error = False
for folder in to_be_linted:
    if folder.endswith(".py"):
        files = [current_path / folder]
    else:
        files = (current_path / folder).glob("**/*.py")
    for file in files:
        if not check_license_header(file):
            print(f"[-] {file} is missing license header")
            any_license_future_error = True
            any_error = True
        if not check_future_annotations(file):
            print(f"[-] {file} is missing __future__ annotations import")
            any_license_future_error = True
            any_error = True

if any_license_future_error:
    print("[-] Please add the license header and __future__ annotations import on the files above")
else:
    print("[+] License header and __future__ annotations import check passed")

if any_error:
    print("[-] Test finished, but some tests failed")
    exit(1)
print("[+] All tests passed")
exit(0)
