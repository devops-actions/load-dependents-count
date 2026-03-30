# Load Dependents Count

A GitHub Action that scrapes dependent repository counts from GitHub's dependents page using Playwright browser automation.

## Usage

### Option 1: Inline repo list

```yaml
- uses: devops-actions/load-dependents-count@28e45ff9cc0e7b7caf85b76265e5b3617c3b80b1 # v0.0.1
  with:
    repos: '["devops-actions/action-get-tag", "devops-actions/actionlint"]'
    output-file: repo-usage.json
```

### Option 2: Scope file (compatible with [openssf-scorecard-monitor](https://github.com/ossf/scorecard-monitor))

```yaml
- uses: devops-actions/load-dependents-count@28e45ff9cc0e7b7caf85b76265e5b3617c3b80b1 # v0.0.1
  with:
    scope-file: ossf-reporting/scope.json
    output-file: ossf-reporting/repo-usage.json
```

### Using the outputs

```yaml
steps:
  - uses: devops-actions/load-dependents-count@28e45ff9cc0e7b7caf85b76265e5b3617c3b80b1 # v0.0.1
    id: dependents
    with:
      repos: '["devops-actions/action-get-tag"]'

  - run: echo "Results: ${{ steps.dependents.outputs.results }}"

  - run: cat ${{ steps.dependents.outputs.output-file }}
```

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `repos` | One of `repos` or `scope-file` | | JSON array of `"org/repo"` strings |
| `scope-file` | One of `repos` or `scope-file` | | Path to a scope.json file |
| `output-file` | No | `repo-usage.json` | Path to write the JSON results |

Both `repos` and `scope-file` can be provided simultaneously — results are merged (deduplicated).

## Outputs

| Output | Description |
|---|---|
| `results` | JSON string with dependent counts, e.g. `{"org/repo": 123}` |
| `output-file` | Path to the generated JSON file |

## Output file format

```json
{
  "devops-actions/action-get-tag": 677,
  "devops-actions/actionlint": 311
}
```

## Scope file format

The scope file follows the same format as [openssf-scorecard-monitor](https://github.com/ossf/scorecard-monitor):

```json
{
  "github.com": {
    "devops-actions": {
      "included": [
        "action-get-tag",
        "actionlint"
      ]
    }
  }
}
```

## Step Summary

The action automatically writes a markdown summary table to the GitHub Actions step summary, showing each repository and its dependent count.