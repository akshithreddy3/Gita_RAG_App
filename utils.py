from typing import Iterable


def chunk_preview(text: str, n: int = 160) -> str:


text = " ".join(text.split())
return (text[:n] + "…") if len(text) > n else text


def print_topk(docs: Iterable, k: int = 3):


for i, d in enumerate(list(docs)[:k], 1):
src = d.metadata.get("source")
page = d.metadata.get("page_num")
print(f"{i}. {src} – p.{page} :: {chunk_preview(d.page_content)}")
