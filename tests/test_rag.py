from app.rag_service import LocalRAG
from langchain_core.runnables import RunnableLambda


def test_demo_documents_load():
    rag = LocalRAG(docs_dir="sample_docs", use_ai=False)
    assert len(rag.documents) >= 3
    assert len(rag.chunks) > 0


def test_security_question_answered_from_docs():
    rag = LocalRAG(docs_dir="sample_docs", use_ai=False)
    answer = rag.answer("What should we do with customer data and public AI tools?")
    assert "customer data" in answer["answer"].lower()
    assert answer["sources"]


def test_pricing_question_answered():
    rag = LocalRAG(docs_dir="sample_docs", use_ai=False)
    answer = rag.answer("What are the pricing tiers?")
    assert "$29" in answer["answer"] or "pricing" in answer["answer"].lower()


def test_no_question_returns_empty():
    rag = LocalRAG(docs_dir="sample_docs", use_ai=False)
    result = rag.search("")
    assert result == []


def test_answer_exposes_rag_trace_without_api_key():
    rag = LocalRAG(docs_dir="sample_docs", use_ai=False)
    result = rag.answer("What are the pricing tiers?")
    assert result["provider"] == "deterministic-fallback"
    assert result["retrieval"]["grounded"] is True
    assert result["retrieval"]["retrieved_chunks"] > 0


def test_gemini_generation_uses_retrieved_context():
    def fake_llm(prompt_value):
        rendered = " ".join(str(message.content) for message in prompt_value.to_messages())
        assert "Retrieved context:" in rendered
        assert "product_overview.md" in rendered
        return type("FakeResponse", (), {"content": "Starter is $29/user/month [1]."})()

    rag = LocalRAG(docs_dir="sample_docs", llm=RunnableLambda(fake_llm))
    result = rag.answer("What are the pricing tiers?")
    assert result["provider"] == "langchain-gemini"
    assert result["answer"] == "Starter is $29/user/month [1]."


def test_gemini_brief_uses_the_document_library():
    def fake_llm(prompt_value):
        rendered = " ".join(str(message.content) for message in prompt_value.to_messages())
        assert "Create an executive brief" in rendered
        assert "company_policy.txt" in rendered
        return type("FakeResponse", (), {"content": "Executive summary [1]."})()

    rag = LocalRAG(docs_dir="sample_docs", llm=RunnableLambda(fake_llm))
    result = rag.generate_brief()
    assert result["provider"] == "langchain-gemini"
    assert result["brief"] == "Executive summary [1]."
