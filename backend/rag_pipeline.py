from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnableLambda, RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from dotenv import load_dotenv
import os
from collections import defaultdict

load_dotenv()

if not os.getenv("GOOGLE_API_KEY"):
    raise EnvironmentError(
        "API_KEY is missing. Please add it to your .env file."
    )

PERSIST_DIR = "sample_articles"
PDF_DIR = "eg_dir"

model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
embed = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
parser = StrOutputParser()

# Only load, split, and embed the PDFs if the vector store doesn't already
# exist on disk. This is the single biggest fix for the quota-exhaustion
# issue -- without it, every run re-embeds the entire corpus from scratch.
if os.path.exists(PERSIST_DIR) and os.listdir(PERSIST_DIR):
    vec_store = Chroma(persist_directory=PERSIST_DIR, embedding_function=embed)
else:
    loader = DirectoryLoader(
        path=PDF_DIR,
        glob="*.pdf",
        loader_cls=PyPDFLoader
    )
    docs = loader.load()
    if not docs:
        raise ValueError("No PDF documents were found.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    # split_documents (not create_documents) preserves metadata -- source
    # filename and page number -- which is what makes citations possible.
    chunks = splitter.split_documents(docs)

    vec_store = Chroma.from_documents(
        documents=chunks,
        embedding=embed,
        persist_directory=PERSIST_DIR
    )

ret = vec_store.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 5, "lambda_mult": 0.5}
)

prompt = PromptTemplate(template='''You are a helpful research assistant.
Answer using only the information in the provided context. You may
reasonably interpret and combine related terms from the context (for
example, treat feature representations like TF-IDF as a form of text
representation technique if the question asks about "embeddings").
If the context truly does not contain relevant information, say "I don't know."

{context}

query : {query}''')


def format_docs(ret_docs):
    return "\n\n".join(doc.page_content for doc in ret_docs)


def retrieve_and_format(query):
    all_sources = vec_store.get()["metadatas"]
    unique_files = set(m["source"] for m in all_sources if m.get("source"))

    docs = []
    for src in unique_files:
        per_doc_retriever = vec_store.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 3, "filter": {"source": src}}
        )
        docs.extend(per_doc_retriever.invoke(query))

    return {"context": format_docs(docs), "source_docs": docs}


parallel_chain = RunnableParallel({
    "query": RunnablePassthrough(),
    "retrieval": RunnableLambda(retrieve_and_format)
})


def group_sources(source_docs):
    grouped = defaultdict(set)
    for doc in source_docs:
        src = os.path.basename(doc.metadata.get("source", "unknown"))
        grouped[src].add(doc.metadata.get("page", "?"))
    return {src: sorted(pages) for src, pages in grouped.items()}


def build_final(inputs):
    answer = (prompt | model | parser).invoke({
        "query": inputs["query"],
        "context": inputs["retrieval"]["context"]
    })
    return {
        "answer": answer,
        "sources": group_sources(inputs["retrieval"]["source_docs"])
    }


main_chain = parallel_chain | RunnableLambda(build_final)

if __name__ == "__main__":
    result = main_chain.invoke(
        "What was the best embedding technique according to these articles "
        "and which model does it work best with?"
    )
    print(result["answer"])
    print("\n--- Sources ---")
    for filename, pages in result["sources"].items():
        page_str = ", ".join(str(p) for p in pages)
        print(f"- {filename} — pages {page_str}")
