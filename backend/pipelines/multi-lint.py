import subprocess as sp
from pathlib import Path

to_be_linted = ["internals", "routes", "app.py"]

current_path = Path(__file__).absolute().parent.parent
print(f"[*] Running tests at {current_path}")
print("[*] Running safety test...")
safety_res = sp.Popen(["safety", "check", "--full-report"]).wait()
print("[*] Running isort test...")
isort_res = sp.Popen(["isort", "-c"] + to_be_linted).wait()
print("[*] Running flake8 test...")
flake8_res = sp.Popen(["flake8", "--statistics", "--show-source", "--benchmark", "--tee"] + to_be_linted).wait()

results = [(safety_res, "safety"), (isort_res, "isort"), (flake8_res, "flake8")]
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
