import pytest
from pydantic import ValidationError

from src.models.schemas import (
    ChatRequest, 
    ChatResponse, 
    SourceDocument, 
    HealthResponse
)


class TestChatRequest:
    """ChatRequest スキーマのテスト"""
    
    def test_valid_chat_request(self):
        """有効なChatRequestが正しく作成されることをテスト"""
        request = ChatRequest(question="テストの質問です")
        assert request.question == "テストの質問です"
        assert request.max_results == 3  # デフォルト値
    
    def test_chat_request_with_custom_max_results(self):
        """カスタムmax_resultsが正しく設定されることをテスト"""
        request = ChatRequest(question="質問", max_results=5)
        assert request.question == "質問"
        assert request.max_results == 5
    
    def test_chat_request_empty_question_fails(self):
        """空の質問でValidationErrorが発生することをテスト"""
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(question="")
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
    
    def test_chat_request_missing_question_fails(self):
        """質問が欠如している場合にValidationErrorが発生することをテスト"""
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest()
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("question",) for error in errors)
    
    def test_max_results_boundary_values(self):
        """max_resultsの境界値をテスト"""
        # 最小値 (1)
        request = ChatRequest(question="質問", max_results=1)
        assert request.max_results == 1
        
        # 最大値 (10)
        request = ChatRequest(question="質問", max_results=10)
        assert request.max_results == 10
    
    def test_max_results_invalid_values(self):
        """max_resultsの無効な値でValidationErrorが発生することをテスト"""
        # 0以下
        with pytest.raises(ValidationError):
            ChatRequest(question="質問", max_results=0)
        
        with pytest.raises(ValidationError):
            ChatRequest(question="質問", max_results=-1)
        
        # 10より大きい
        with pytest.raises(ValidationError):
            ChatRequest(question="質問", max_results=11)


class TestSourceDocument:
    """SourceDocument スキーマのテスト"""
    
    def test_valid_source_document(self):
        """有効なSourceDocumentが正しく作成されることをテスト"""
        doc = SourceDocument(
            content="ドキュメントの内容",
            section="セクション名"
        )
        assert doc.content == "ドキュメントの内容"
        assert doc.section == "セクション名"
        assert doc.metadata == {}  # デフォルト値
    
    def test_source_document_with_metadata(self):
        """メタデータ付きのSourceDocumentをテスト"""
        metadata = {"score": 0.95, "source": "test.md"}
        doc = SourceDocument(
            content="内容",
            section="セクション",
            metadata=metadata
        )
        assert doc.metadata == metadata
    
    def test_source_document_missing_required_fields(self):
        """必須フィールドが欠如している場合のValidationErrorをテスト"""
        # content が欠如
        with pytest.raises(ValidationError) as exc_info:
            SourceDocument(section="セクション")
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("content",) for error in errors)
        
        # section が欠如
        with pytest.raises(ValidationError) as exc_info:
            SourceDocument(content="内容")
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("section",) for error in errors)
    
    def test_source_document_empty_strings(self):
        """空文字列のフィールドをテスト"""
        # 空文字列は許可される（必要に応じて）
        doc = SourceDocument(content="", section="")
        assert doc.content == ""
        assert doc.section == ""


class TestChatResponse:
    """ChatResponse スキーマのテスト"""
    
    def test_valid_chat_response(self):
        """有効なChatResponseが正しく作成されることをテスト"""
        sources = [
            SourceDocument(content="内容1", section="セクション1"),
            SourceDocument(content="内容2", section="セクション2")
        ]
        response = ChatResponse(
            answer="回答です",
            sources=sources,
            confidence=0.85
        )
        
        assert response.answer == "回答です"
        assert len(response.sources) == 2
        assert response.confidence == 0.85
    
    def test_chat_response_empty_sources(self):
        """空のソースリストを持つChatResponseをテスト"""
        response = ChatResponse(
            answer="回答",
            sources=[],
            confidence=0.0
        )
        
        assert response.answer == "回答"
        assert response.sources == []
        assert response.confidence == 0.0
    
    def test_confidence_boundary_values(self):
        """confidenceの境界値をテスト"""
        # 最小値 (0.0)
        response = ChatResponse(
            answer="回答",
            sources=[],
            confidence=0.0
        )
        assert response.confidence == 0.0
        
        # 最大値 (1.0)
        response = ChatResponse(
            answer="回答",
            sources=[],
            confidence=1.0
        )
        assert response.confidence == 1.0
    
    def test_confidence_invalid_values(self):
        """confidenceの無効な値でValidationErrorが発生することをテスト"""
        source = SourceDocument(content="内容", section="セクション")
        
        # 0.0未満
        with pytest.raises(ValidationError):
            ChatResponse(
                answer="回答",
                sources=[source],
                confidence=-0.1
            )
        
        # 1.0より大きい
        with pytest.raises(ValidationError):
            ChatResponse(
                answer="回答",
                sources=[source],
                confidence=1.1
            )
    
    def test_chat_response_missing_required_fields(self):
        """必須フィールドが欠如している場合のValidationErrorをテスト"""
        source = SourceDocument(content="内容", section="セクション")
        
        # answer が欠如
        with pytest.raises(ValidationError) as exc_info:
            ChatResponse(sources=[source], confidence=0.5)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("answer",) for error in errors)
        
        # confidence が欠如
        with pytest.raises(ValidationError) as exc_info:
            ChatResponse(answer="回答", sources=[source])
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("confidence",) for error in errors)


class TestHealthResponse:
    """HealthResponse スキーマのテスト"""
    
    def test_valid_health_response(self):
        """有効なHealthResponseが正しく作成されることをテスト"""
        response = HealthResponse(
            status="healthy",
            version="0.1.0",
            vector_store_ready=True
        )
        
        assert response.status == "healthy"
        assert response.version == "0.1.0"
        assert response.vector_store_ready is True
    
    def test_health_response_unhealthy_status(self):
        """不健全な状態のHealthResponseをテスト"""
        response = HealthResponse(
            status="unhealthy",
            version="0.1.0",
            vector_store_ready=False
        )
        
        assert response.status == "unhealthy"
        assert response.vector_store_ready is False
    
    def test_health_response_missing_required_fields(self):
        """必須フィールドが欠如している場合のValidationErrorをテスト"""
        # status が欠如
        with pytest.raises(ValidationError) as exc_info:
            HealthResponse(version="0.1.0", vector_store_ready=True)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("status",) for error in errors)
        
        # version が欠如
        with pytest.raises(ValidationError) as exc_info:
            HealthResponse(status="healthy", vector_store_ready=True)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("version",) for error in errors)
        
        # vector_store_ready が欠如
        with pytest.raises(ValidationError) as exc_info:
            HealthResponse(status="healthy", version="0.1.0")
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("vector_store_ready",) for error in errors)


@pytest.mark.parametrize("confidence,expected", [
    (0.0, 0.0),
    (0.25, 0.25),
    (0.5, 0.5),
    (0.75, 0.75),
    (1.0, 1.0),
])
def test_confidence_parameter_values(confidence, expected):
    """様々なconfidence値をパラメータ化テストで検証"""
    source = SourceDocument(content="内容", section="セクション")
    response = ChatResponse(
        answer="回答",
        sources=[source],
        confidence=confidence
    )
    assert response.confidence == expected


@pytest.mark.parametrize("max_results", [1, 2, 3, 5, 8, 10])
def test_max_results_valid_range(max_results):
    """有効なmax_results値をパラメータ化テストで検証"""
    request = ChatRequest(question="テスト質問", max_results=max_results)
    assert request.max_results == max_results