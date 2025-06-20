"""Simple integration tests for new modules."""


def test_imports():
    import backend.agents.nl_command_agent as n
    import backend.integrations.browser_automation as b
    import backend.integrations.enhanced_llm_gateway as g
    import backend.integrations.workflow_orchestrator as w
    import backend.knowledge.enhanced_knowledge_manager as k

    assert (
        w is not None
        and g is not None
        and b is not None
        and n is not None
        and k is not None
    )
