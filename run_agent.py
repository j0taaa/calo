import sys
from agent.agent import chat_with_tools
from agent.pdf_rag import ensure_pdf_index

PDF_URL = (
    "https://hcip-files.obs.sa-brazil-1.myhuaweicloud.com/HCIP-Cloud%20Service%20Solutions%20Architect%20V3.0%20Training%20Material.pdf"
)


def main() -> None:
    question = " ".join(sys.argv[1:])
    ensure_pdf_index(PDF_URL)
    prompt = (
        "You are given a question that may be a multiple choice single-answer, multiple choice multiple-answer, or true or false. "
        "Always research on the internet and consult the provided document even if you think you know the answer. "
        "Respond only with the letter(s) of the correct option separated by commas or 'True'/'False'. "
        f"Question: {question}"
    )
    print(chat_with_tools(prompt))


if __name__ == "__main__":
    main()
