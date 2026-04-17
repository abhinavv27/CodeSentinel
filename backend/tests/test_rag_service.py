import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.rag_service import RagService, PointStruct

@pytest.fixture
def mock_qdrant():
    with patch("app.services.rag_service.QdrantClient") as mock:
        client = MagicMock()
        mock.return_value = client
        # Mock get_collections
        client.get_collections.return_value = MagicMock(collections=[])
        yield client

@pytest.fixture
def mock_embedder():
    with patch("app.services.rag_service.get_embedder") as mock:
        embedder = MagicMock()
        mock.return_value = embedder
        # Returns a mock that has a tolist() method returning a list
        mock_vec = MagicMock()
        mock_vec.tolist.return_value = [0.1] * 384
        embedder.encode.return_value = mock_vec
        yield embedder

@pytest.mark.asyncio
async def test_rag_service_retrieve_context(mock_qdrant, mock_embedder):
    # Setup mock search results
    mock_result = MagicMock()
    mock_result.payload = {"content": "print('hello world')"}
    mock_qdrant.search.return_value = [mock_result]
    
    svc = RagService()
    context = await svc.retrieve_context("how to print hello?", top_k=1)
    
    assert len(context) == 1
    assert context[0] == "print('hello world')"
    mock_embedder.encode.assert_called_once()
    mock_qdrant.search.assert_called_once()

def test_rag_service_index_file(mock_qdrant, mock_embedder):
    svc = RagService()
    svc.index_file("test.py", "def hello():\n    print('hi')")
    
    mock_embedder.encode.assert_called()
    mock_qdrant.upsert.assert_called_once()
    args, kwargs = mock_qdrant.upsert.call_args
    assert kwargs["collection_name"] == "codebase"
    assert len(kwargs["points"]) >= 1
    assert isinstance(kwargs["points"][0], PointStruct)

def test_rag_service_ensure_collection_creates_if_missing(mock_qdrant):
    # mock_qdrant.get_collections().collections is already [] from fixture
    RagService()
    mock_qdrant.create_collection.assert_called_once()

def test_rag_service_ensure_collection_skips_if_exists(mock_qdrant):
    mock_collection = MagicMock()
    mock_collection.name = "codebase"
    mock_qdrant.get_collections.return_value = MagicMock(collections=[mock_collection])
    
    RagService()
    mock_qdrant.create_collection.assert_not_called()
