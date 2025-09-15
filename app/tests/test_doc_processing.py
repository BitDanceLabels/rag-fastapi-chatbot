import pytest
from app.doc_processing.services import DocProcessing

@pytest.mark.parametrize("file_id", [
    "id sample",
])
def test_download_pdf(file_id, tmp_path_test: str = "document_test"):
    """Test downloading and chunking a PDF file."""
    output_dir = tmp_path_test

    doc_processor = DocProcessing(chunk_size=256, chunk_overlap=50)
    result = doc_processor.process_pdf(file_id, str(output_dir))

    chunks = list(result)
    assert len(chunks) > 0

