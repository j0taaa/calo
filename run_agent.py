import sys
from agent.agent import chat_with_tools
from agent.pdf_rag import ensure_pdf_index

PDF_URL = (
    "https://hcip-files.obs.sa-brazil-1.myhuaweicloud.com/HCIP-Cloud%20Service%20Solutions%20Architect%20V3.0%20Training%20Material.pdf"
)


def main() -> None:
    question = " ".join(sys.argv[1:])
    ensure_pdf_index(PDF_URL)
    print(chat_with_tools(question))


if __name__ == "__main__":
    main()
