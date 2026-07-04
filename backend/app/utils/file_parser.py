from pathlib import Path


def extract_text(file_path: Path | str, filename: str = "") -> str:
    """Extract text from PDF, DOCX, or plain text files."""
    file_path = Path(file_path)
    suffix = file_path.suffix.lower() if file_path.suffix else Path(filename).suffix.lower()

    if suffix == ".pdf":
        return _extract_pdf(file_path)
    elif suffix in (".docx", ".doc"):
        return _extract_docx(file_path)
    elif suffix in (".txt", ".md", ".text"):
        return file_path.read_text(encoding="utf-8", errors="replace")
    else:
        raise ValueError(f"不支持的文件格式: {suffix}，请上传 PDF、DOCX 或 TXT 文件。")


def _extract_pdf(path: Path) -> str:
    import pdfplumber

    text_parts: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    if not text_parts:
        raise ValueError("无法从 PDF 中提取文本，文件可能是扫描件或图片。请尝试直接粘贴简历内容。")
    return "\n\n".join(text_parts)


def _extract_docx(path: Path) -> str:
    from docx import Document

    doc = Document(str(path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    if not paragraphs:
        raise ValueError("文档中没有找到文本内容。")
    return "\n".join(paragraphs)
