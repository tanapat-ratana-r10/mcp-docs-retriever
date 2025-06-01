import time
from server import add_documentation_tool, search_documentation

def test_add_and_search():
    url = "https://ai.pydantic.dev"
    print("Adding documentation from:", url)
    add_result = add_documentation_tool(url)
    print("Add result:", add_result)

    # Wait a moment to ensure indexing is complete (not strictly necessary for local, but good practice)
    time.sleep(2)

    queries = [
        "What is Pydantic AI?",
        "How do I use the API?",
        "Supported features"
    ]
    for query in queries:
        print(f"\nQuery: {query}")
        results = search_documentation(query, n_results=2)
        for idx, chunk in enumerate(results):
            print(f"Result {idx+1}: {chunk[:200]}...\n")

if __name__ == "__main__":
    test_add_and_search()
