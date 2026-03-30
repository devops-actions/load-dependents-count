#!/usr/bin/env python3
"""
Fetch repository dependents counts by scraping GitHub's dependents page.
Designed to run as a GitHub Action (Docker-based).

Inputs (via environment variables):
  INPUT_REPOS:       JSON array of "org/repo" strings
  INPUT_SCOPE_FILE:  Path to scope.json file
  INPUT_OUTPUT_FILE: Path to write the output JSON (default: repo-usage.json)

At least one of INPUT_REPOS or INPUT_SCOPE_FILE must be provided.
"""

import asyncio
import json
import os
import re
import sys
from pathlib import Path

from playwright.async_api import async_playwright

PAGE_DELAY_SECONDS = 2


def resolve_repos():
    """Build a list of 'org/repo' strings from action inputs."""
    repos_input = os.environ.get("INPUT_REPOS", "").strip()
    scope_file = os.environ.get("INPUT_SCOPE_FILE", "").strip()

    repos = []

    if repos_input:
        try:
            parsed = json.loads(repos_input)
            if isinstance(parsed, list):
                repos.extend(parsed)
            else:
                print(f"::error::repos input must be a JSON array, got {type(parsed).__name__}")
                sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"::error::Failed to parse repos input as JSON: {e}")
            sys.exit(1)

    if scope_file:
        # Support running inside GitHub Actions where GITHUB_WORKSPACE is the repo root
        workspace = os.environ.get("GITHUB_WORKSPACE", "")
        scope_path = Path(workspace) / scope_file if workspace else Path(scope_file)

        if not scope_path.exists():
            print(f"::error::scope-file not found at {scope_path}")
            sys.exit(1)

        with open(scope_path, "r", encoding="utf-8") as f:
            scope = json.load(f)

        for platform in scope:
            for org in scope[platform]:
                included = scope[platform][org].get("included", [])
                for repo in included:
                    full_name = f"{org}/{repo}"
                    if full_name not in repos:
                        repos.append(full_name)

    if not repos:
        print("::error::No repositories specified. Provide either 'repos' or 'scope-file' input.")
        sys.exit(1)

    return repos


async def fetch_dependents_count(page, org, repo, retries=2):
    """Navigate to the GitHub dependents page and scrape the repository count."""
    url = f"https://github.com/{org}/{repo}/network/dependents"
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)

        link = page.get_by_role("link", name=re.compile(r"^\d+\s+Repositor"))
        text = await link.first.text_content(timeout=10000)
        match = re.search(r"(\d[\d,]*)", text)
        if match:
            return int(match.group(1).replace(",", ""))
        print(f"  Warning: could not parse count from '{text.strip()}'")
        return 0
    except Exception as e:
        if retries > 0:
            print(f"  Retrying {org}/{repo}... ({retries} retries left)")
            await asyncio.sleep(5)
            return await fetch_dependents_count(page, org, repo, retries - 1)
        print(f"  ::warning::Error fetching dependents for {org}/{repo}: {e}")
        return None


async def run():
    repos = resolve_repos()
    output_file_input = os.environ.get("INPUT_OUTPUT_FILE", "repo-usage.json").strip()

    workspace = os.environ.get("GITHUB_WORKSPACE", "")
    output_path = Path(workspace) / output_file_input if workspace else Path(output_file_input)

    print(f"Fetching dependents for {len(repos)} repositories...")
    usage_counts = {}

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()

        for i, full_name in enumerate(repos):
            parts = full_name.split("/", 1)
            if len(parts) != 2:
                print(f"  ::warning::Skipping invalid repo format: {full_name}")
                continue

            org, repo = parts
            count = await fetch_dependents_count(page, org, repo)
            if count is not None:
                usage_counts[full_name] = count
                print(f"  {full_name}: {count} dependents")
            else:
                print(f"  {full_name}: could not determine dependents")

            if i < len(repos) - 1:
                await asyncio.sleep(PAGE_DELAY_SECONDS)

        await browser.close()

    # Write output file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(usage_counts, f, indent=2, sort_keys=True)
        f.write("\n")

    print(f"\nDependents counts saved to {output_path}")

    # Set GitHub Actions outputs
    github_output = os.environ.get("GITHUB_OUTPUT", "")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            results_json = json.dumps(usage_counts, sort_keys=True)
            f.write(f"results={results_json}\n")
            f.write(f"output-file={output_file_input}\n")

    # Summary
    github_summary = os.environ.get("GITHUB_STEP_SUMMARY", "")
    if github_summary:
        with open(github_summary, "a", encoding="utf-8") as f:
            f.write("## Dependents Count Results\n\n")
            f.write("| Repository | Dependents |\n|---|---|\n")
            for repo_name in sorted(usage_counts.keys()):
                count = usage_counts[repo_name]
                f.write(f"| [{repo_name}](https://github.com/{repo_name}/network/dependents) | {count} |\n")
            f.write(f"\n*{len(usage_counts)} repositories scanned*\n")


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
