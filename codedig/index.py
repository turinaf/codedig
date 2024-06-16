from whoosh import index, fields, scoring
from whoosh.analysis import RegexAnalyzer
from whoosh.filedb.filestore import FileStorage
import json
import os 
from codedig.lang import lang
from tqdm import tqdm
from codedig.sample import sample_prompt, sample_ans
from codedig.glm_api import CHATCHLM_API_KEY
import time
from zhipuai import ZhipuAI
from codedig.glm_api import CHATCHLM_API_KEY
client = ZhipuAI(api_key=CHATCHLM_API_KEY) 

if not os.path.exists("indexdir"):
    os.makedirs("indexdir")
storage = FileStorage("indexdir")

def index_code(folder_path):
    schema = fields.Schema(
        filename=fields.TEXT(stored=True),
        content=fields.TEXT(stored=False),
        description=fields.TEXT(stored=True),
        startline=fields.NUMERIC(numtype=int, stored=True),
        language=fields.TEXT(stored=True)  
    )
    storage = FileStorage("indexdir")
    ix = storage.create_index(schema, indexname="codeindex")
    writer = ix.writer()
    counter = 0
    for root, _, files in tqdm(os.walk(folder_path), desc="Indexing code"):
        for file in files:
            filepath = os.path.join(root, file)
            if "__pycache__" in filepath:
                continue
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.readlines()
                    
                    language = determine_language(filepath)
                    if language is None:
                        continue
                    counter += 1
                    annotated_content = []
                    file_name = filepath.split("\\")[-1].split(".")[0]
                    for i in range(0, len(content), 10):
                        json_data ={}
                        chunk = content[i:i+10]
                        json_data['content'] = chunk
                        code_snippet = "".join(chunk)
                        description = explain_code_snippet(code_snippet, language)
                        
                        json_data['description'] = description
                        json_data['language'] = language
                        json_data['filename'] = filepath
                        json_data['startline'] = i+1
                        annotated_content.append(json_data)
                        writer.add_document(filename=filepath, 
                                            startline=i+1,
                                            content="".join(chunk), 
                                            description=description,
                                            language=language,
                                            )
                        time.sleep(1)
                    print("Indexed content of: ", file_name)
                    # save incase a problem occurs
                    # with open(f"annotated_code/{counter}_{file_name}.json", "w") as f:
                    #     json.dump(annotated_content, f, indent=4)
                        
            except UnicodeDecodeError:
                    continue
    print("Committing...")
    writer.commit()
    print(f"Indexed {counter} code files")
    
def determine_language(filepath):
    extension = filepath.split(".")[-1]
    if extension in lang:
        return lang[extension][0].lower()
    else:
        return None

def explain_code_snippet(code_snippet, language):
    prompt =f"The following is {language} code snippet from code base, please explain it in less than 10 sentences in English. The description should explain what the code does overall, without using specific variable names or function names. The code:\n\n{code_snippet}"
    response = client.chat.completions.create(
    model="glm-4", 
        messages=[
            {"role": "user", "content": sample_prompt},
            {"role": "assistant", "content": sample_ans},
            {"role": "user", "content": prompt},

        ],
    )
    return response.choices[0].message.content

def index_docs(folder_path):
    schema = fields.Schema(
    title=fields.TEXT(stored=True),
    link=fields.TEXT(stored=True),
    content=fields.TEXT(stored=True), 
    )
    ix = storage.create_index(schema, indexname="docsindex")
    writer = ix.writer()
    counter = 0
    for root, _, files in tqdm(os.walk(folder_path), desc="Indexing documents"):
        for file in files:
            filepath = os.path.join(root, file)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "content" in data:
                        title = data['title']
                        link = data['link']
                        content = data['content']
                        writer.add_document(title=title, 
                                            link=link,
                                            content=content
                                            )
                        counter += 1
            except UnicodeDecodeError:
                    print(f"Could not read file: {filepath} due to UnicodeDecodeError. Skipping this file.")

    writer.commit()
    print(f"Indexed {counter} documents")

if __name__ == "__main__":
    index_code("path/to/codebase")
    index_docs("path/to/docs") 
