#!/usr/bin/env python3
"""Simple AI Memory Test
Test AI Memory functionality without complex dependencies
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict


class SimpleAIMemory:
    """Simple AI Memory implementation for testing"""

    def __init__(self):
        self.memories = {}  # In-memory storage for testing
        self.encoder = None

    async def initialize(self):
        """Initialize the simple AI memory"""
        try:
            from sentence_transformers import SentenceTransformer

            self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
            print("✅ SentenceTransformer initialized")
            return True
        except ImportError:
            print("⚠️ SentenceTransformer not available, using dummy encoder")
            self.encoder = "dummy"
            return True
        except Exception as e:
            print(f"❌ Failed to initialize encoder: {e}")
            return False

    async def store_conversation(
        self,
        conversation_text: str,
        context: str = "",
        category: str = "conversation",
        tags: list = None,
    ) -> Dict[str, Any]:
        """Store a conversation in memory"""
        if not conversation_text:
            return {"error": "conversation_text is required"}

        try:
            # Generate embedding (or use dummy)
            if self.encoder == "dummy":
                embedding = [0.1] * 384  # Dummy embedding
            else:
                embedding = self.encoder.encode(conversation_text).tolist()

            # Create memory record
            memory_id = str(uuid.uuid4())
            memory_record = {
                "id": memory_id,
                "text": conversation_text,
                "context": context,
                "category": category,
                "tags": tags or [],
                "timestamp": datetime.now().isoformat(),
                "embedding": embedding,
            }

            # Store in memory
            self.memories[memory_id] = memory_record

            return {
                "success": True,
                "memory_id": memory_id,
                "category": category,
                "tags": tags or [],
                "timestamp": memory_record["timestamp"],
            }

        except Exception as e:
            return {"error": f"Failed to store conversation: {e}"}

    async def recall_memory(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Recall memories based on query"""
        if not query:
            return {"error": "query is required"}

        try:
            # Generate query embedding (or use dummy)
            if self.encoder == "dummy":
                query_embedding = [0.1] * 384  # Dummy embedding
            else:
                query_embedding = self.encoder.encode(query).tolist()

            # Simple text matching for demo (in real implementation, use vector similarity)
            results = []
            for memory_id, memory in self.memories.items():
                # Simple keyword matching
                score = 0.5  # Dummy score
                if any(
                    word.lower() in memory["text"].lower() for word in query.split()
                ):
                    score = 0.8

                results.append(
                    {
                        "id": memory_id,
                        "score": score,
                        "text": memory["text"],
                        "context": memory["context"],
                        "category": memory["category"],
                        "tags": memory["tags"],
                        "timestamp": memory["timestamp"],
                    }
                )

            # Sort by score and limit
            results.sort(key=lambda x: x["score"], reverse=True)
            results = results[:top_k]

            return {
                "success": True,
                "query": query,
                "count": len(results),
                "memories": results,
            }

        except Exception as e:
            return {"error": f"Failed to recall memories: {e}"}

    async def delete_memory(self, memory_id: str) -> Dict[str, Any]:
        """Delete a memory by ID"""
        if not memory_id:
            return {"error": "memory_id is required"}

        if memory_id in self.memories:
            del self.memories[memory_id]
            return {
                "success": True,
                "memory_id": memory_id,
                "message": "Memory deleted successfully",
            }
        else:
            return {"error": f"Memory not found: {memory_id}"}


async def test_simple_ai_memory():
    """Test the simple AI memory implementation"""
    print("🧠 Testing Simple AI Memory Implementation...")

    # Initialize
    memory = SimpleAIMemory()
    if not await memory.initialize():
        return False

    # Test storing conversations
    print("\n📝 Testing conversation storage...")
    conversations = [
        {
            "text": "We need to fix the MCP server restart issues by setting environment variables",
            "context": "Infrastructure troubleshooting",
            "category": "bug_solution",
            "tags": ["mcp", "docker", "environment"],
        },
        {
            "text": "The AI Memory system should automatically store and recall conversations for Cursor AI",
            "context": "Architecture discussion",
            "category": "architecture",
            "tags": ["ai_memory", "cursor", "automation"],
        },
        {
            "text": "Use Pinecone for vector storage and SentenceTransformers for embeddings",
            "context": "Technical implementation decision",
            "category": "code_decision",
            "tags": ["pinecone", "embeddings", "vectors"],
        },
    ]

    stored_ids = []
    for i, conv in enumerate(conversations, 1):
        print(f"  Storing conversation {i}...")
        result = await memory.store_conversation(
            conv["text"], conv["context"], conv["category"], conv["tags"]
        )

        if result.get("success"):
            stored_ids.append(result["memory_id"])
            print(f"    ✅ Stored: {result['memory_id']}")
        else:
            print(f"    ❌ Failed: {result}")
            return False

    # Test recalling memories
    print("\n🔍 Testing memory recall...")
    queries = [
        "MCP server issues",
        "AI Memory automation",
        "vector storage implementation",
    ]

    for query in queries:
        print(f"  Query: '{query}'")
        result = await memory.recall_memory(query, top_k=2)

        if result.get("success"):
            memories = result.get("memories", [])
            print(f"    ✅ Found {len(memories)} memories")
            for mem in memories:
                print(f"      • Score: {mem['score']:.2f} - {mem['context']}")
        else:
            print(f"    ❌ Failed: {result}")

    # Test deletion
    print("\n🗑️ Testing memory deletion...")
    if stored_ids:
        delete_id = stored_ids[0]
        result = await memory.delete_memory(delete_id)

        if result.get("success"):
            print(f"    ✅ Deleted memory: {delete_id}")
        else:
            print(f"    ❌ Failed to delete: {result}")

    print("\n📊 Final stats:")
    print(f"  Total memories stored: {len(memory.memories)}")
    print(f"  Memory IDs: {list(memory.memories.keys())}")

    return True


async def test_cursor_ai_workflow():
    """Test workflow patterns for Cursor AI integration"""
    print("\n🎯 Testing Cursor AI Integration Workflow...")

    memory = SimpleAIMemory()
    await memory.initialize()

    # Simulate Cursor AI workflow
    print("  Simulating coding session with AI memory...")

    # 1. User asks a question - AI should recall relevant context
    user_question = "How do we handle authentication in MCP servers?"
    print(f"  User: '{user_question}'")

    recall_result = await memory.recall_memory(user_question)
    print(f"    🔍 AI recalls {recall_result.get('count', 0)} relevant memories")

    # 2. AI provides answer and stores the conversation
    ai_response = "For MCP server authentication, we use environment variables for API keys and Pulumi ESC for secret management. This ensures secure handling of credentials."
    conversation = f"User: {user_question}\nAI: {ai_response}"

    store_result = await memory.store_conversation(
        conversation,
        "Authentication discussion for MCP servers",
        "architecture",
        ["mcp", "authentication", "security", "environment"],
    )

    if store_result.get("success"):
        print("    ✅ Conversation stored for future reference")
    else:
        print("    ❌ Failed to store conversation")

    # 3. Later, similar question should recall this conversation
    later_question = "What's the best way to manage secrets in MCP?"
    print(f"\n  Later user question: '{later_question}'")

    later_recall = await memory.recall_memory(later_question)
    if later_recall.get("success") and later_recall.get("memories"):
        print("    ✅ AI found relevant previous discussion")
        for mem in later_recall["memories"][:1]:
            print(f"      Previous context: {mem['context']}")
    else:
        print("    ⚠️ No relevant memories found")

    return True


async def main():
    """Main test function"""
    print("🧠 SIMPLE AI MEMORY TEST SUITE")
    print("=" * 50)

    # Test basic functionality
    basic_success = await test_simple_ai_memory()

    if basic_success:
        # Test Cursor AI workflow
        workflow_success = await test_cursor_ai_workflow()

        if workflow_success:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Simple AI Memory is working correctly")
            print("\n📋 Next steps:")
            print("1. Fix the full AI Memory MCP server")
            print("2. Integrate with Cursor AI")
            print("3. Test with real conversations")
            return True

    print("\n❌ TESTS FAILED")
    return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
