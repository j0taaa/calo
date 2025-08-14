import argparse
import os
import sys

from dotenv import load_dotenv

from agent.pdf_rag import ensure_pdf_index, query_pdf, build_context_snippet
from agent.agent import chat_with_tools, direct_response_with_high_reasoning
from agent.web_tools import search_web

PDF_URL = (
    "https://hcip-files.obs.sa-brazil-1.myhuaweicloud.com/HCIP-Cloud%20Service%20Solutions%20Architect%20V3.0%20Training%20Material.pdf"
)


def cmd_setup_pdf() -> None:
    ensure_pdf_index(PDF_URL)
    print("PDF downloaded and indexed.")


def cmd_ask(question: str) -> None:
    answer = chat_with_tools(question)
    print("\n=== Answer ===\n")
    print(answer)


def cmd_test() -> None:
    print("1) Ensuring PDF index...")
    ensure_pdf_index(PDF_URL)
    print("   OK")

    print("2) Querying PDF index (sanity check)...")
    chunks = query_pdf("What is the scope of the HCIP Cloud Service Solutions Architect training?", top_k=3)
    for c in chunks:
        print(f" - chunk {c.chunk_id} score={c.score:.2f} len={len(c.text)}")
    print("   OK")

    print("3) Web search (DuckDuckGo)...")
    results = search_web("OpenAI latest model announcement", num_results=3)
    for r in results:
        print(f" - {r['title']} | {r['url']}")
    print("   OK")

    print("4) OpenAI direct response with high reasoning effort...")
    resp = direct_response_with_high_reasoning("What is 17 * 23? Show brief reasoning.")
    if resp is None:
        print("   Skipped (set OPENAI_API_KEY to run this test).")
    else:
        print("\n" + resp + "\n")
        print("   OK")


if __name__ == "__main__":
    load_dotenv(dotenv_path="/workspace/.env", override=True)

    parser = argparse.ArgumentParser(description="GPT-5 Agent CLI")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("setup-pdf", help="Download and index the PDF")

    ask_p = sub.add_parser("ask", help="Ask a question using tools")
    ask_p.add_argument("--q", required=True, help="Your question")

    sub.add_parser("test", help="Run quick integration tests")

    args = parser.parse_args()

    if args.cmd == "setup-pdf":
        cmd_setup_pdf()
    elif args.cmd == "ask":
        cmd_ask(args.q)
    elif args.cmd == "test":
        cmd_test()
    else:
        parser.print_help()
        sys.exit(1)