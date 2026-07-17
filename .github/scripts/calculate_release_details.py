#!/usr/bin/env python3
import glob
import json
import os
import re
import subprocess
from datetime import datetime


def run_git(args):
    try:
        return (
            subprocess.check_output(["git"] + args, stderr=subprocess.DEVNULL)
            .decode("utf-8")
            .strip()
        )
    except subprocess.CalledProcessError:
        return ""


def main():
    rtype = os.environ.get("RELEASE_TYPE", "beta")
    bump_level = os.environ.get("BUMP_LEVEL", "patch")
    version_override = os.environ.get("VERSION_OVERRIDE", "")
    repo = os.environ.get("REPO", "")

    # Determine owner and repo_name dynamically
    owner = "faserf"
    repo_name = os.path.basename(os.getcwd())
    if "/" in repo:
        owner, repo_name = repo.split("/", 1)

    # Dynamic manifest location
    manifest_files = glob.glob("custom_components/*/manifest.json")
    if not manifest_files:
        print("Error: manifest.json not found!")
        return
    manifest_path = manifest_files[0]
    domain = os.path.basename(os.path.dirname(manifest_path))

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    friendly_name = manifest.get("name", domain)

    # Dynamic documentation URL logic
    docs_url = manifest.get("documentation")
    if not docs_url:
        if os.path.exists("docs"):
            docs_url = f"https://{owner}.github.io/{repo_name}/"
        else:
            docs_url = (
                f"https://github.com/{repo}"
                if repo
                else f"https://github.com/faserf/{repo_name}"
            )

    # Calculate version via version_manager
    bump_args = [
        "python",
        ".github/scripts/version_manager.py",
        "bump",
        "--type",
        rtype,
        "--level",
        bump_level,
    ]
    if version_override and version_override.strip():
        bump_args += ["--override", version_override.strip()]

    version = subprocess.check_output(bump_args).decode("utf-8").strip()

    # Revert version bump change in manifest file (since versioning job only calculates it, sync-version actually writes it)
    run_git(["checkout", "--", manifest_path])

    print(f"Calculated Version: {version}")
    tag = f"v{version}"
    is_prerelease = "false" if rtype == "stable" else "true"

    # Base version without suffixes
    base_version = version
    m = re.match(r"^(\d+\.\d+\.\d+)", version)
    if m:
        base_version = m.group(1)

    changelog_from = ""
    changelog_label = "initial release — full history"

    # Get sorted list of tags
    tags_raw = run_git(["tag", "-l", "[0-9]*", "v[0-9]*", "--sort=-v:refname"])
    tags = [t.strip() for t in tags_raw.splitlines() if t.strip()]
    latest_tag = ""
    for t in tags:
        if re.match(r"^v?\d+\.\d+\.\d+(?:?:b|-dev|-nightly)\d+)?$", t):
            latest_tag = t
            break

    if rtype == "stable":
        for t in tags:
            if re.match(r"^v?\d+\.\d+\.\d+$", t):
                changelog_from = t
                changelog_label = f"since last stable release (`{t}`)"
                break
    elif rtype == "beta":
        prev_beta_pat = re.compile(rf"^v?{re.escape(base_version)}(?:b|-beta)\d+$")
        for t in tags:
            if prev_beta_pat.match(t):
                changelog_from = t
                changelog_label = f"since previous beta (`{t}`)"
                break
        if not changelog_from:
            for t in tags:
                if re.match(r"^v?\d+\.\d+\.\d+$", t):
                    changelog_from = t
                    changelog_label = f"since last stable release (`{t}`) — first beta of {base_version}"
                    break
    else:
        if latest_tag:
            changelog_from = latest_tag
            changelog_label = f"since `{latest_tag}`"

    print(f"Changelog range start tag: '{changelog_from}' ({changelog_label})")

    # Count commits
    total_commit_count = 0
    count_range = f"{changelog_from}..HEAD" if changelog_from else "HEAD"

    commit_count_raw = run_git(["rev-list", "--count", count_range])
    if commit_count_raw.isdigit():
        total_commit_count = int(commit_count_raw)

    # Generate Changelog
    changelog_md = ""
    if os.path.exists("scripts/generate_changelog.py"):
        try:
            changelog_md = (
                subprocess.check_output(
                    [
                        "python",
                        "scripts/generate_changelog.py",
                        "--from-tag",
                        changelog_from,
                        "--total-commits",
                        str(total_commit_count),
                        "--repo",
                        repo,
                    ]
                )
                .decode("utf-8")
                .strip()
            )
        except Exception:
            changelog_md = (
                "_Changelog could not be generated automatically. See commit history._"
            )
    else:
        changelog_md = "_Changelog script not found._"

    if not changelog_md:
        changelog_md = "_No categorised changes detected._"

    # Channel decorations
    channel_badge = {
        "stable": "![Stable](https://img.shields.io/badge/channel-stable-brightgreen?style=flat-square)",
        "beta": "![Beta](https://img.shields.io/badge/channel-beta-orange?style=flat-square)",
    }.get(
        rtype,
        "![Nightly](https://img.shields.io/badge/channel-nightly-blue?style=flat-square)",
    )

    # Analyze diff impact
    diff_range = f"{changelog_from}..HEAD" if changelog_from else "HEAD"
    changed_files_raw = run_git(["diff", "--name-only", diff_range])
    changed_files = [f.strip() for f in changed_files_raw.splitlines() if f.strip()]

    total_files = len(changed_files)
    integration_count = 0
    translation_count = 0
    ci_count = 0
    docs_count = 0
    test_count = 0

    for f in changed_files:
        if f.startswith(f"custom_components/{domain}/translations/"):
            translation_count += 1
        elif f.startswith("custom_components/"):
            integration_count += 1
        elif f.startswith("tests/"):
            test_count += 1
        elif f.startswith(".github/") or f.startswith("scripts/"):
            ci_count += 1
        elif f.startswith("docs/") or f.endswith(".md"):
            docs_count += 1

    breaking_count = 0
    log_msgs = run_git(["log", diff_range, "--format=%B"])
    for msg in log_msgs.split("\n"):
        if re.search(r"\bBREAKING CHANGE\b|\bBREAKING:\b|^[a-zA-Z]+!:", msg):
            breaking_count += 1

    # Determine Risk Severity
    severity = "Low"
    alert_type = "NOTE"
    preamble = "This release introduces minor updates and code improvements."

    if breaking_count > 0:
        severity = "Critical"
        alert_type = "CAUTION"
        preamble = f"This release contains **{breaking_count} breaking change(s)**! Please review the changelog carefully before updating."
    elif integration_count > 8:
        severity = "High"
        alert_type = "WARNING"
        preamble = "This release contains significant changes to core features. Please verify integration behavior after updating."
    elif integration_count > 2 or translation_count > 5:
        severity = "Medium"
        alert_type = "TIP"
        preamble = "This release contains standard updates and feature enhancements to the integration logic or translations."

    if rtype != "stable":
        preamble = f"ℹ️ **This is a {rtype} build.** It contains preview features for testing.<br><br>{preamble}"

    impact_summary = []
    if total_files > 0:
        if integration_count > 0:
            pct = round((integration_count / total_files) * 100)
            impact_summary.append(f"⚙️ Core ({integration_count} files · {pct}%)")
        if translation_count > 0:
            pct = round((translation_count / total_files) * 100)
            impact_summary.append(
                f"🗣️ Translations ({translation_count} files · {pct}%)"
            )
        if test_count > 0:
            pct = round((test_count / total_files) * 100)
            impact_summary.append(f"🧪 Tests ({test_count} files · {pct}%)")
        if ci_count > 0:
            pct = round((ci_count / total_files) * 100)
            impact_summary.append(f"🚀 CI/CD ({ci_count} files · {pct}%)")
        if docs_count > 0:
            pct = round((docs_count / total_files) * 100)
            impact_summary.append(f"📖 Docs ({docs_count} files · {pct}%)")

    impact_str = (
        " · ".join(impact_summary)
        if impact_summary
        else "No codebase changes detected."
    )

    prerelease_note = (
        f"\n> [!{alert_type}]\n"
        f"> **Release Risk: {severity}**\n"
        f"> {preamble}\n"
    )

    # Format release details markdown
    release_body = (
        f"## {friendly_name} {version} {channel_badge}\n"
        f"{prerelease_note}\n"
        f"📊 **Impact Analysis:** {impact_str}\n"
        f"📝 **Changelog:** {changelog_label}\n"
        f"\n"
        f"{changelog_md}\n"
        f"\n"
        f"---\n"
        f"📖 **Resources:** [Documentation]({docs_url}) · [Changelog](CHANGELOG.md)\n"
    )

    # Write to file
    with open("release_body.md", "w", encoding="utf-8") as f:
        f.write(release_body)

    # Set outputs for GitHub Action step
    # Escape multi-line output for github action output
    def set_output(name, val):
        if "\n" in val:
            # Output delimiter matching GHA requirements
            delimiter = "EOF_DETAILS"
            print(f"{name}<<{delimiter}")
            print(val)
            print(delimiter)
            # Write to environment output file if present
            env_file = os.environ.get("GITHUB_OUTPUT")
            if env_file:
                with open(env_file, "a", encoding="utf-8") as out_f:
                    out_f.write(f"{name}<<{delimiter}\n{val}\n{delimiter}\n")
        else:
            print(f"{name}={val}")
            env_file = os.environ.get("GITHUB_OUTPUT")
            if env_file:
                with open(env_file, "a", encoding="utf-8") as out_f:
                    out_f.write(f"{name}={val}\n")

    set_output("version", version)
    set_output("tag", tag)
    set_output("is_prerelease", is_prerelease)
    set_output("release_body", release_body)


if __name__ == "__main__":
    main()
