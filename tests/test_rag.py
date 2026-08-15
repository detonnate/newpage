from app.rag_service import LocalRAG


def test_demo_documents_load():
    rag = LocalRAG(docs_dir="sample_docs")
    assert len(rag.documents) >= 3
    assert len(rag.chunks) > 0


def test_security_question_answered_from_docs():
    rag = LocalRAG(docs_dir="sample_docs")
    answer = rag.answer("What should we do with customer data and public AI tools?")
    assert "customer data" in answer["answer"].lower()
    assert answer["sources"]


def test_pricing_question_answered():
    rag = LocalRAG(docs_dir="sample_docs")
    answer = rag.answer("What are the pricing tiers?")
    assert "$29" in answer["answer"] or "pricing" in answer["answer"].lower()


def test_no_question_returns_empty():
    rag = LocalRAG(docs_dir="sample_docs")
    result = rag.search("")
    assert result == []


def test_answer_exposes_rag_trace_without_api_key():
    rag = LocalRAG(docs_dir="sample_docs", gemini_client=None)
    result = rag.answer("What are the pricing tiers?")
    assert result["provider"] == "deterministic-fallback"
    assert result["retrieval"]["grounded"] is True
    assert result["retrieval"]["retrieved_chunks"] > 0


def test_gemini_generation_uses_retrieved_context():
    class FakeResponse:
        text = "Starter is $29/user/month [1]."

    class FakeModels:
        def generate_content(self, **kwargs):
            assert "Retrieved context:" in kwargs["contents"]
            assert "product_overview.md" in kwargs["contents"]
            return FakeResponse()

    class FakeClient:
        models = FakeModels()

    rag = LocalRAG(docs_dir="sample_docs", gemini_client=FakeClient())
    result = rag.answer("What are the pricing tiers?")
    assert result["provider"] == "gemini"
    assert result["answer"] == "Starter is $29/user/month [1]."
