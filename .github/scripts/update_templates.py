import glob
import os
import re
import sys


def update_issue_templates(version):
    """Update issue templates with the current version if applicable."""
    templates = glob.glob(".github/ISSUE_TEMPLATE/*.yml") + glob.glob(
        ".github/ISSUE_TEMPLATE/*.yaml"
    )
    for t_path in templates:
        if not os.path.exists(t_path):
            continue
        with open(t_path, encoding="utf-8") as f:
            content = f.read()

        # Update integration version default value in forms
        new_content = re.sub(
            r"(default:\s*\"?v?)\d+\.\d+\.\d+(?:(?:b|-dev|-nightly)\d+)?(\"?)",
            rf"\g<1>{version}\g<2>",
            content,
        )
        if new_content != content:
            with open(t_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Updated version in issue template {t_path} to {version}")


def main():
    if len(sys.argv) < 2:
        print("Usage: update_templates.py <version>")
        sys.exit(1)
    version = sys.argv[1]
    update_issue_templates(version)


if __name__ == "__main__":
    main()
