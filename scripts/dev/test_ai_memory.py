#!/usr/bin/env python3
"""Test AI Memory MCP Server
Verify that the AI Memory system is working for Cursor AI integration
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


async def test_ai_memory_server():
    """Test the AI Memory MCP server functionality"""
    print("🧠 Testing AI Memory MCP Server...")

    try:
        from backend.mcp.ai_memory_mcp_server import AIMemoryMCPServer

        # Initialize server
        server = AIMemoryMCPServer()
        await server.initialize_integration()

        print("✅ AI Memory MCP Server initialized successfully")

        # Test storing a conversation
        print("\n📝 Testing conversation storage...")
        store_result = await server._store_conversation(
            {
                "conversation_text": "This is a test conversation about MCP server infrastructure and AI memory integration.",
                "context": "Testing AI Memory functionality",
                "category": "code_decision",
                "tags": ["mcp", "ai_memory", "testing", "infrastructure"],
            }
        )

        if store_result.get("success"):
            print(
                f"✅ Conversation stored successfully: {store_result.get('memory_id')}"
            )
            memory_id = store_result.get("memory_id")
        else:
            print(f"❌ Failed to store conversation: {store_result}")
            return False

        # Test recalling memories
        print("\n🔍 Testing memory recall...")
        recall_result = await server._recall_memory(
            {"query": "MCP server infrastructure testing", "top_k": 3}
        )

        if recall_result.get("success"):
            memories = recall_result.get("memories", [])
            print(f"✅ Recalled {len(memories)} memories")
            for i, memory in enumerate(memories[:2], 1):
                print(
                    f"  {i}. Score: {memory.get('score', 0):.3f} - {memory.get('text', '')[:100]}..."
                )
        else:
            print(f"❌ Failed to recall memories: {recall_result}")
            return False

        # Test deleting memory
        if memory_id:
            print("\n🗑️ Testing memory deletion...")
            delete_result = await server._delete_memory({"memory_id": memory_id})

            if delete_result.get("success"):
                print("✅ Memory deleted successfully")
            else:
                print(f"❌ Failed to delete memory: {delete_result}")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed:")
        print("pip install pinecone sentence-transformers mcp")
        return False
    except Exception as e:
        print(f"❌ Error testing AI Memory: {e}")
        return False


async def test_cursor_ai_integration():
    """Test integration patterns for Cursor AI"""
    print("\n🎯 Testing Cursor AI Integration Patterns...")

    # Simulate how Cursor AI would use the memory system
    conversation_examples = [
        {
            "text": "How do we handle authentication in MCP servers?",
            "context": "Architecture discussion about MCP security",
            "category": "architecture",
            "tags": ["mcp", "authentication", "security"],
        },
        {
            "text": "We decided to use environment variables for API keys and Pulumi ESC for secret management.",
            "context": "Security implementation decision",
            "category": "code_decision",
            "tags": ["security", "environment", "pulumi", "secrets"],
        },
        {
            "text": "Fixed the container restart issue by setting missing environment variables.",
            "context": "Bug fix for MCP container stability",
            "category": "bug_solution",
            "tags": ["docker", "containers", "environment", "mcp"],
        },
    ]

    try:
        from backend.mcp.ai_memory_mcp_server import AIMemoryMCPServer

        server = AIMemoryMCPServer()
        await server.initialize_integration()

        stored_memories = []

        # Store example conversations
        for i, example in enumerate(conversation_examples, 1):
            print(f"  📝 Storing example {i}: {example['context']}")
            result = await server._store_conversation(
                {
                    "conversation_text": example["text"],
                    "context": example["context"],
                    "category": example["category"],
                    "tags": example["tags"],
                }
            )

            if result.get("success"):
                stored_memories.append(result.get("memory_id"))
                print(f"    ✅ Stored with ID: {result.get('memory_id')}")
            else:
                print(f"    ❌ Failed to store: {result}")

        # Test recall scenarios
        recall_scenarios = [
            "How do we handle authentication?",
            "Container restart issues",
            "Secret management best practices",
        ]

        print("\n🔍 Testing recall scenarios...")
        for scenario in recall_scenarios:
            print(f"  Query: '{scenario}'")
            result = await server._recall_memory({"query": scenario, "top_k": 2})

            if result.get("success"):
                memories = result.get("memories", [])
                print(f"    ✅ Found {len(memories)} relevant memories")
                for memory in memories:
                    print(
                        f"      • Score: {memory.get('score', 0):.3f} - {memory.get('context', 'No context')}"
                    )
            else:
                print(f"    ❌ Recall failed: {result}")

        # Cleanup
        print("\n🧹 Cleaning up test memories...")
        for memory_id in stored_memories:
            if memory_id:
                await server._delete_memory({"memory_id": memory_id})

        print("✅ Cursor AI integration test completed successfully")
        return True

    except Exception as e:
        print(f"❌ Cursor AI integration test failed: {e}")
        return False


async def generate_cursor_ai_config():
    """Generate configuration for Cursor AI to use AI Memory"""
    print("\n⚙️ Generating Cursor AI Configuration...")

    config = {
        "ai_memory_integration": {
            "enabled": True,
            "auto_store": True,
            "auto_recall": True,
            "server_endpoint": "http://localhost:8090/ai_memory",
            "triggers": {
                "store": [
                    "architecture_decisions",
                    "bug_solutions",
                    "code_patterns",
                    "performance_optimizations",
                    "security_implementations",
                ],
                "recall": [
                    "similar_problems",
                    "past_implementations",
                    "architecture_questions",
                    "debugging_sessions",
                    "code_reviews",
                ],
            },
            "categories": [
                "conversation",
                "code_decision",
                "bug_solution",
                "architecture",
                "workflow",
                "requirement",
                "pattern",
                "api_usage",
            ],
        }
    }

    config_path = project_root / "cursor_ai_memory_config.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"✅ Configuration saved to: {config_path}")
    print("\n📋 Next steps for Cursor AI integration:")
    print("1. Ensure MCP Gateway is running: docker-compose up mcp-gateway")
    print("2. Start AI Memory server: python backend/mcp/ai_memory_mcp_server.py")
    print("3. Configure Cursor AI to use the generated config")
    print("4. Test by having conversations - they should be automatically stored")


async def main():
    """Main test function"""
    print("🧠 AI MEMORY MCP SERVER TEST SUITE")
    print("=" * 50)

    # Test basic functionality
    basic_test = await test_ai_memory_server()

    if basic_test:
        # Test Cursor AI integration patterns
        integration_test = await test_cursor_ai_integration()

        if integration_test:
            # Generate configuration
            await generate_cursor_ai_config()

            print("\n🎉 ALL TESTS PASSED!")
            print("✅ AI Memory MCP Server is ready for Cursor AI integration")
            return True

    print("\n❌ TESTS FAILED")
    print("Please fix the issues above before proceeding")
    return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
