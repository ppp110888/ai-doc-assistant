import re


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    cleaned_lines = []

    for line in text.splitlines():
        line = re.sub(r"[ \t]+", " ", line)
        cleaned_lines.append(line.strip())

    cleaned_text = "\n".join(cleaned_lines)
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)

    return cleaned_text.strip()

def split_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if overlap < 0:
        raise ValueError("overlap must not be negative")

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    cleaned_text = clean_text(text)

    if not cleaned_text:
        return []

    chunks = []
    start = 0

    while start < len(cleaned_text):
        end = min(start + chunk_size, len(cleaned_text))
        chunks.append(cleaned_text[start:end])

        if end == len(cleaned_text):
            break

        start = end - overlap

    return chunks