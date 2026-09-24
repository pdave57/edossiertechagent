#!/usr/bin/env python3
"""
Extract text from NATIONAL-POLICY-ON-EDUCATION.pdf using pypdf and langchain-text-splitters
"""
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import json

pdf_path = "/home/learn2earn/projects/edossiertechagent/documents/NATIONAL-POLICY-ON-EDUCATION.pdf"

print(f"Reading PDF: {pdf_path}")
reader = PdfReader(pdf_path)
print(f"Total pages: {len(reader.pages)}")

all_text = ""
for i, page in enumerate(reader.pages):
    text = page.extract_text()
    if text and text.strip():
        all_text += f"\n--- PAGE {i+1} ---\n{text}\n"
    if i < 5:
        print(f"Page {i+1}: {len(text) if text else 0} chars")

print(f"\nTotal extracted text: {len(all_text)} characters")

# Save raw text
with open("/tmp/policy_raw_text.txt", "w") as f:
    f.write(all_text)
print("Raw text saved to /tmp/policy_raw_text.txt")

# Chunk using langchain-text-splitters
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", ". ", " ", ""],
    length_function=len,
)

chunks = splitter.split_text(all_text)
print(f"\nSplit into {len(chunks)} chunks")

# Save chunks
chunk_data = []
for i, chunk in enumerate(chunks):
    chunk_data.append({
        "index": i,
        "content": chunk,
        "length": len(chunk)
    })

with open("/tmp/policy_chunks.json", "w") as f:
    json.dump(chunk_data, f, indent=2)
print("Chunks saved to /tmp/policy_chunks.json")

# Print first few chunks
for i, chunk in enumerate(chunks[:3]):
    print(f"\n--- Chunk {i} ({len(chunk)} chars) ---")
    print(chunk[:500])