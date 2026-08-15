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
