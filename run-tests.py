#!/usr/bin/env python
#
# Runs all unit tests included in PyBaMM.
#
# The code in this file is adapted from Pints
# (see https://github.com/pints-team/pints)
#
import re
import os
import sys
import argparse
import subprocess


def run_flake8():
    """
    Runs flake8 in a subprocess, exits if it doesn't finish.
    """
    print("Running flake8 ... ")
    sys.stdout.flush()
    p = subprocess.Popen(["flake8"], stderr=subprocess.PIPE)
    try:
        ret = p.wait()
    except KeyboardInterrupt:
        try:
            p.terminate()
        except OSError:
            pass
        p.wait()
        print("")
        sys.exit(1)
    if ret == 0:
        print("ok")
    else:
        print("FAILED")
        sys.exit(ret)


def run_notebook_and_scripts(skip_slow_books=False, executable="python"):
    """
    Runs Jupyter notebook tests. Exits if they fail.
    """
    # Ignore slow books?
    ignore_list = []
    if skip_slow_books and os.path.isfile(".slow-books"):
        with open(".slow-books", "r") as f:
            for line in f.readlines():
                line = line.strip()
                if not line or line[:1] == "#":
                    continue
                if not line.startswith("results/"):
                    line = "results/" + line
                if not line.endswith(".ipynb"):
                    line = line + ".ipynb"
                if not os.path.isfile(line):
                    raise Exception("Slow notebook note found: " + line)
                ignore_list.append(line)

    # Scan and run
    print("Testing notebooks and scripts with executable `" + str(executable) + "`")
    if not scan_for_nb_and_scripts("results", True, executable, ignore_list):
        print("\nErrors encountered in notebooks")
        sys.exit(1)
    print("\nOK")


def scan_for_nb_and_scripts(root, recursive=True, executable="python", ignore_list=[]):
    """
    Scans for, and tests, all notebooks and scripts in a directory.
    """
    ok = True
    debug = False

    # Scan path
    for filename in os.listdir(root):
        path = os.path.join(root, filename)
        if path in ignore_list:
            print("Skipping slow book: " + path)
            continue

        # Recurse into subdirectories
        if recursive and os.path.isdir(path):
            # Ignore hidden directories
            if filename[:1] == ".":
                continue
            ok &= scan_for_nb_and_scripts(path, recursive, executable)

        # Test notebooks
        if os.path.splitext(path)[1] == ".ipynb":
            if debug:
                print(path)
            else:
                ok &= test_notebook(path, executable)
        # Test scripts
        elif os.path.splitext(path)[1] == ".py":
            if debug:
                print(path)
            else:
                ok &= test_script(path, executable)

    # Return True if every notebook is ok
    return ok


def test_notebook(path, executable="python"):
    """
    Tests a single notebook, exists if it doesn't finish.
    """
    import nbconvert
    import pybamm

    b = pybamm.Timer()
    print("Test " + path + " ... ", end="")
    sys.stdout.flush()

    # Load notebook, convert to python
    e = nbconvert.exporters.PythonExporter()
    code, __ = e.from_filename(path)

    # Remove coding statement, if present
    code = "\n".join([x for x in code.splitlines() if x[:9] != "# coding"])

    # Tell matplotlib not to produce any figures
    env = dict(os.environ)
    env["MPLBACKEND"] = "Template"

    # Run in subprocess
    cmd = [executable] + ["-c", code]
    try:
        p = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env
        )
        stdout, stderr = p.communicate()
        # TODO: Use p.communicate(timeout=3600) if Python3 only
        if p.returncode != 0:
            # Show failing code, output and errors before returning
            print("ERROR")
            print("-- script " + "-" * (79 - 10))
            for i, line in enumerate(code.splitlines()):
                j = str(1 + i)
                print(j + " " * (5 - len(j)) + line)
            print("-- stdout " + "-" * (79 - 10))
            print(str(stdout, "utf-8"))
            print("-- stderr " + "-" * (79 - 10))
            print(str(stderr, "utf-8"))
            print("-" * 79)
            return False
    except KeyboardInterrupt:
        p.terminate()
        print("ABORTED")
        sys.exit(1)

    # Sucessfully run
    print("ok (" + b.format() + ")")
    return True


def test_script(path, executable="python"):
    """
    Tests a single notebook, exists if it doesn't finish.
    """
    import pybamm

    b = pybamm.Timer()
    print("Test " + path + " ... ", end="")
    sys.stdout.flush()

    # Tell matplotlib not to produce any figures
    env = dict(os.environ)
    env["MPLBACKEND"] = "Template"

    # Run in subprocess
    cmd = [executable] + [path]
    try:
        p = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env
        )
        stdout, stderr = p.communicate()
        # TODO: Use p.communicate(timeout=3600) if Python3 only
        if p.returncode != 0:
            # Show failing code, output and errors before returning
            print("ERROR")
            print("-- stdout " + "-" * (79 - 10))
            print(str(stdout, "utf-8"))
            print("-- stderr " + "-" * (79 - 10))
            print(str(stderr, "utf-8"))
            print("-" * 79)
            return False
    except KeyboardInterrupt:
        p.terminate()
        print("ABORTED")
        sys.exit(1)

    # Sucessfully run
    print("ok (" + b.format() + ")")
    return True


def export_notebook(ipath, opath):
    """
    Exports the notebook at `ipath` to a python file at `opath`.
    """
    import nbconvert
    from traitlets.config import Config

    # Create nbconvert configuration to ignore text cells
    c = Config()
    c.TemplateExporter.exclude_markdown = True

    # Load notebook, convert to python
    e = nbconvert.exporters.PythonExporter(config=c)
    code, __ = e.from_filename(ipath)

    # Remove "In [1]:" comments
    r = re.compile(r"(\s*)# In\[([^]]*)\]:(\s)*")
    code = r.sub("\n\n", code)

    # Store as executable script file
    with open(opath, "w") as f:
        f.write("#!/usr/bin/env python")
        f.write(code)
    os.chmod(opath, 0o775)


if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Run tests for repository.",)
    # Notebook tests
    parser.add_argument(
        "--results",
        action="store_true",
        help="Test all Jupyter notebooks and scripts in `results`.",
    )
    parser.add_argument(
        "-debook",
        nargs=2,
        metavar=("in", "out"),
        help="Export a Jupyter notebook to a Python file for manual testing.",
    )
    # Doctests
    parser.add_argument(
        "--flake8", action="store_true", help="Run flake8 to check for style issues"
    )
    # Combined test sets
    parser.add_argument(
        "--quick", action="store_true", help="Run quick checks (results, flake8)",
    )

    # Parse!
    args = parser.parse_args()

    # Run tests
    has_run = False
    # Flake8
    if args.flake8:
        has_run = True
        run_flake8()
    # Notebook tests
    elif args.results:
        has_run = True
        run_notebook_and_scripts()
    if args.debook:
        has_run = True
        export_notebook(*args.debook)
    # Combined test sets
    if args.quick:
        has_run = True
        run_flake8()
        run_notebook_and_scripts()
    # Help
    if not has_run:
        parser.print_help()
