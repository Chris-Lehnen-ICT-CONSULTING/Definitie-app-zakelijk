import json

import requests

API_KEY = "lin_api_CZ4ROGZBmfy3g8qmG6UZhGHgb9f7CqzpHlA6hM94"
URL = "https://api.linear.app/graphql"

def fetch_issues():
    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json"
    }

    # Query to get issues from the 'DEF' team (inferred from DEF-60)
    # We'll fetch open issues.
    query = """
    query {
      issues(
        filter: { 
          team: { key: { eq: "DEF" } }
          state: { type: { neq: "completed" } }
        }
        first: 50
      ) {
        nodes {
          identifier
          title
          priority
          state {
            name
            type
          }
          assignee {
            displayName
          }
          description
        }
      }
    }
    """

    response = requests.post(URL, headers=headers, json={"query": query})
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return

    data = response.json()
    if "errors" in data:
        print("GraphQL Errors:")
        print(json.dumps(data["errors"], indent=2))
        return

    issues = data["data"]["issues"]["nodes"]
    
    print(f"Found {len(issues)} open issues for team DEF:\n")
    
    # Sort by priority (approximate, Linear priority is number but 0 is no priority, 1 is urgent, etc. 
    # Actually priority is 0=No Priority, 1=Urgent, 2=High, 3=Medium, 4=Low.
    # Let's just print them.
    
    for issue in issues:
        assignee = issue['assignee']['displayName'] if issue['assignee'] else "Unassigned"
        print(f"[{issue['identifier']}] {issue['title']}")
        print(f"  Status: {issue['state']['name']} | Priority: {issue['priority']} | Assignee: {assignee}")
        print("-" * 40)

if __name__ == "__main__":
    fetch_issues()
