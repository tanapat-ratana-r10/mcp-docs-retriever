import asyncio
import traceback
from server import add_documentation, search_documentation

async def test_docs_retriever():
    print("Testing documentation retriever...")
    
    try:
        # Test adding documentation
        print("\n1. Testing add_documentation...")
        result = await add_documentation(
            url="https://ai.pydantic.dev",
            max_pages=5  # Limit to 5 pages for testing
        )
        print(f"Add documentation result: {result}")
        
        # Test searching documentation
        print("\n2. Testing search_documentation...")
        search_result = await search_documentation(
            query="What is PydanticAI?",
            num_results=3
        )
        print(f"Search result: {search_result}")
        
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_docs_retriever()) 