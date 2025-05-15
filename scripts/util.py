import shutil
import subprocess


def format_c_file(filepath: str) -> None:
    if shutil.which("clang-format") is not None:
        style = "{BasedOnStyle: llvm, IndentWidth: 2, ColumnLimit: 160}"
        subprocess.run(f"clang-format -i --style=\"{style}\" {filepath}", shell=True)
