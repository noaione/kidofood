import subprocess as sp
import sys
from pathlib import Path
from typing import Optional

to_be_linted = ["internals", "routes", "app.py"]

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

if any_error:
    print("[-] Test finished, but some tests failed")
    exit(1)
print("[+] All tests passed")
exit(0)
