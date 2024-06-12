from flask import render_template, request, Blueprint
from whoosh.qparser import QueryParser, MultifieldParser, FuzzyTermPlugin
from whoosh.query import Phrase, TermRange
from whoosh import scoring,highlight, qparser
from whoosh.index import open_dir
from whoosh.query import Term, Or, Regex, And
from codedig.index import index_code

bp = Blueprint("codedig", __name__)

@bp.route("/")
def search():
    modes = ['code', 'documentation']
    return render_template("search.html", modes=modes)

@bp.route("/results", methods=["POST", "GET"])
def handle_search():
    mode = request.form.get("mode")
    query_text = request.form["query"]
    selected_language = request.form.get("language", None)
    if mode == "code":
       return code_search(mode, query_text, selected_language)
    elif mode == "documentation":
       return docs_search(mode, query_text)
    else:
        return render_template("search.html", error="Select search mode.")
    
def code_search(mode, query_text, selected_language):
    ix = open_dir(dirname="indexdir", indexname="codeindex")
    searcher = ix.searcher(weighting=scoring.BM25F(field_boosts={"content": 1.5, "description": 1}))
    parser = MultifieldParser(["content", "description"], schema=ix.schema, group=qparser.OrGroup)
    
    parser.add_plugin(FuzzyTermPlugin())
    query_with_fuzzy = " ".join([word+"~2/3" for word in query_text.split() if len(word) > 2])
    query = parser.parse(query_with_fuzzy)
    if selected_language and selected_language != "all":
        lang_query = MultifieldParser(["language"], ix.schema).parse(selected_language)
        query = And([query, lang_query])
    results = searcher.search(query)
    my_fragmenter = highlight.SentenceFragmenter(maxchars=100)
    results.fragmenter = my_fragmenter
    search_results = []
    for hit in results:
        result = {}
        filepath = hit["filename"]
        filepath = filepath.lstrip("../")
        linenumber = hit.get('startline')
        result['linenumber'] = list(range(linenumber, linenumber+10))
        result["filepath"] = filepath
        result['language'] = hit['language']
        result['description'] = hit.highlights("description")
        result["full_desc"] = hit["description"]
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
            start_line = linenumber  #
            end_line = min(len(lines), linenumber + 10)  # Show 3 lines after the match
            code_snippet = "".join(lines[start_line:end_line])
            result["filepath"] = filepath.lstrip("../base/code").replace("\\", "/")
            result['content'] = code_snippet
            search_results.append(result)

    return render_template(
        "search.html",
        query=query_text,
        results=search_results,
        selected_language=selected_language, 
        languages = get_unique_languages(ix),
        mode = mode,
        docs = None,
        code = True
    )

def docs_search(mode, query_text):
    ix = open_dir(dirname="indexdir", indexname="docsindex")
    searcher = ix.searcher(weighting=scoring.BM25F(field_boosts={"title": 2, "content": 1.0}))
    parser =  MultifieldParser(["content", "title"], ix.schema, group=qparser.OrGroup)
    parser.add_plugin(FuzzyTermPlugin())
    query_with_fuzzy = " ".join([word+"~2/3" for word in query_text.split() if len(word) > 2])
    query =parser.parse(query_with_fuzzy)
    results = searcher.search(query)
    docs_fragmenter = highlight.ContextFragmenter(maxchars=100, surround=50)
    results.fragmenter.charlimit = None
    results.fragmenter = docs_fragmenter
    search_results = []
    for hit in results:
        result = {}
        result["title"] = hit["title"]
        result["link"] = hit["link"]
        result["content"] = hit.highlights("content")
        search_results.append(result)
    
    return render_template(
        "search.html",
        query=query_text,
        results=search_results,
        selected_language=None,
        languages=None,
        mode=mode,
        docs=True,
        code=None
    )

@bp.route("/index")
def index():
    if request.form.get("folderpath") is None:
        return render_template("index.html")
    folder_path = request.form.get("folderpath")
    # index_code(folder_path)
    return render_template("index.html", message="Indexing completed.")
    
def get_unique_languages(ix):
    with ix.reader() as reader:
        # Use field_terms to get unique language terms
        unique_languages = set(reader.field_terms("language"))
        unique_languages =[lang.strip() for lang in unique_languages]
    return unique_languages


