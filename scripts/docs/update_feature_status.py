#!/usr/bin/env python3
"""
Feature Status Updater voor Architectuur Dashboard
Synchroniseert feature status van GitHub Issues/Projects naar de architectuur HTML
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# GitHub API configuratie (gebruik environment variables in productie)
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "username/repo")
GITHUB_PROJECT_NUMBER = os.environ.get("GITHUB_PROJECT_NUMBER", "1")

# Feature mapping van GitHub labels naar status
STATUS_MAPPING = {
    "done": "complete",
    "in-progress": "in-progress",
    "todo": "not-started",
    "blocked": "not-started",
    "review": "in-progress",
}

# Epic mapping van GitHub labels
EPIC_MAPPING = {
    "epic:basis-definitie": "epic-001",
    "epic:kwaliteit": "epic-002",
    "epic:ui": "epic-003",
    "epic:security": "epic-004",
    "epic:performance": "epic-005",
    "epic:export": "epic-006",
    "epic:web-lookup": "epic-007",
    "epic:monitoring": "epic-008",
    "epic:content": "epic-009",
}


def fetch_github_issues():
    """Fetch issues from GitHub using GraphQL API"""
    try:
        import requests

        # GraphQL query voor project items
        query = """
        query($owner: String!, $repo: String!, $projectNumber: Int!) {
          repository(owner: $owner, name: $repo) {
            projectV2(number: $projectNumber) {
              items(first: 100) {
                nodes {
                  id
                  content {
                    ... on Issue {
                      title
                      number
                      labels(first: 10) {
                        nodes {
                          name
                        }
                      }
                      state
                    }
                  }
                  fieldValues(first: 10) {
                    nodes {
                      ... on ProjectV2ItemFieldSingleSelectValue {
                        name
                        field {
                          ... on ProjectV2SingleSelectField {
                            name
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """

        owner, repo = GITHUB_REPO.split("/")
        variables = {
            "owner": owner,
            "repo": repo,
            "projectNumber": int(GITHUB_PROJECT_NUMBER),
        }

        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            "https://api.github.com/graphql",
            json={"query": query, "variables": variables},
            headers=headers,
        )

        if response.status_code == 200:
            return response.json()
        print(f"Error fetching GitHub data: {response.status_code}")
        return None

    except Exception as e:
        print(f"Error: {e}")
        return None


def parse_github_data(github_data) -> dict:
    """Parse GitHub data naar ons feature format"""
    features_by_epic = {
        "epic-001": [],
        "epic-002": [],
        "epic-003": [],
        "epic-004": [],
        "epic-005": [],
        "epic-006": [],
        "epic-007": [],
        "epic-008": [],
        "epic-009": [],
    }

    if not github_data:
        return features_by_epic

    try:
        items = github_data["data"]["repository"]["projectV2"]["items"]["nodes"]

        for item in items:
            if not item["content"]:
                continue

            issue = item["content"]
            title = issue["title"]
            number = issue["number"]
            labels = [label["node"]["name"] for label in issue["labels"]["nodes"]]

            # Bepaal epic
            epic_id = None
            for label in labels:
                if label in EPIC_MAPPING:
                    epic_id = EPIC_MAPPING[label]
                    break

            if not epic_id:
                continue

            # Bepaal status
            status = "not-started"
            for field_value in item["fieldValues"]["nodes"]:
                if field_value.get("field", {}).get("name") == "Status":
                    github_status = field_value.get("name", "").lower()
                    status = STATUS_MAPPING.get(github_status, "not-started")
                    break

            # Check voor critical label
            is_critical = "priority:critical" in labels or "critical" in labels

            # Maak feature object
            feature = {
                "id": f"GH-{number}",
                "name": title,
                "status": status,
                "critical": is_critical,
            }

            features_by_epic[epic_id].append(feature)

    except Exception as e:
        print(f"Error parsing GitHub data: {e}")

    return features_by_epic


def update_html_file(features_by_epic: dict):
    """Update de HTML file met nieuwe feature data"""
    html_path = (
        Path(__file__).parent.parent
        / "docs"
        / "architectuur"
        / "ARCHITECTURE_VISUALIZATION_DETAILED.html"
    )

    if not html_path.exists():
        print(f"HTML file not found: {html_path}")
        return False

    # Lees HTML file
    with open(html_path, encoding="utf-8") as f:
        html_content = f.read()

    # Vind de featureData sectie
    feature_data_start = html_content.find("const featureData = {")
    if feature_data_start == -1:
        print("Could not find featureData in HTML")
        return False

    feature_data_end = html_content.find("};", feature_data_start) + 2

    # Genereer nieuwe feature data
    new_feature_data = generate_feature_data_js(features_by_epic)

    # Vervang de oude data
    new_html = (
        html_content[:feature_data_start]
        + new_feature_data
        + html_content[feature_data_end:]
    )

    # Voeg timestamp toe
    timestamp_comment = f"<!-- Feature Status Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} -->"
    new_html = new_html.replace("<!-- Feature Status Last Updated:", timestamp_comment)

    # Schrijf terug
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(new_html)

    print(f"Updated HTML file: {html_path}")
    return True


def generate_feature_data_js(features_by_epic: dict) -> str:
    """Genereer JavaScript featureData object"""
    epic_definitions = {
        "epic-001": {
            "name": "Basis Definitie Generatie",
            "description": "Core functionality voor het genereren van definities",
        },
        "epic-002": {
            "name": "Kwaliteitstoetsing",
            "description": "Validatie en kwaliteitscontrole van gegenereerde definities",
        },
        "epic-003": {
            "name": "User Interface",
            "description": "Gebruikersinterface en navigatie",
        },
        "epic-004": {
            "name": "Security & Authentication",
            "description": "Beveiliging en gebruikersauthenticatie",
        },
        "epic-005": {
            "name": "Performance",
            "description": "Performance optimalisatie en monitoring",
        },
        "epic-006": {
            "name": "Export/Import",
            "description": "Data export en import functionaliteit",
        },
        "epic-007": {
            "name": "Web Lookup & Integration",
            "description": "Externe data bronnen integratie",
        },
        "epic-008": {
            "name": "Monitoring & Analytics",
            "description": "System monitoring en analytics",
        },
        "epic-009": {
            "name": "Content Management",
            "description": "Beheer van definities en content",
        },
    }

    js_code = "const featureData = {\n    epics: [\n"

    for epic_id, epic_info in epic_definitions.items():
        features = features_by_epic.get(epic_id, [])

        js_code += "        {\n"
        js_code += f"            id: '{epic_id}',\n"
        js_code += f"            name: '{epic_info['name']}',\n"
        js_code += f"            description: '{epic_info['description']}',\n"
        js_code += "            features: [\n"

        for feature in features:
            critical_str = "true" if feature.get("critical", False) else "false"
            js_code += f"                {{ id: '{feature['id']}', name: '{feature['name']}', status: '{feature['status']}'"
            if feature.get("critical"):
                js_code += f", critical: {critical_str}"
            js_code += " },\n"

        js_code += "            ]\n"
        js_code += "        },\n"

    js_code += "    ]\n};"

    return js_code


def main():
    """Main function"""
    print("🔄 Starting Feature Status Update...")

    # Check environment variables
    if not GITHUB_TOKEN:
        print("❌ Error: GITHUB_TOKEN environment variable not set")
        return 1

    # Fetch data from GitHub
    print("📥 Fetching data from GitHub...")
    github_data = fetch_github_issues()

    if not github_data:
        print("❌ Failed to fetch GitHub data")
        return 1

    # Parse data
    print("🔍 Parsing feature data...")
    features_by_epic = parse_github_data(github_data)

    # Count features
    total_features = sum(len(features) for features in features_by_epic.values())
    print(f"📊 Found {total_features} features across {len(features_by_epic)} epics")

    # Update HTML
    print("📝 Updating HTML file...")
    if update_html_file(features_by_epic):
        print("✅ Feature status successfully updated!")
        return 0
    print("❌ Failed to update HTML file")
    return 1


if __name__ == "__main__":
    sys.exit(main())
