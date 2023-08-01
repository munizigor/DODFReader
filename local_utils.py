import requests
import json
from weasyprint import HTML
from bs4 import BeautifulSoup
import unicodedata

ORGANIZATIONS = {
    "CBMDF": {
        "name": "CORPO DE BOMBEIROS MILITAR DO DISTRITO FEDERAL",
        "tags": ["CBMDF", "QOBM", "QBMG", "BOMBEIRO", "BOMBEIRA", "00053-"]
    },
    "DEFESA CIVIL": {
        "name": "SUBSECRETARIA DE DEFESA CIVIL",
        "tags": ["DEFESA CIVIL", "SEGURANCA PUBLICA"]
    },
    "PMDF": {
        "name": "POLÍCIA MILITAR DO DISTRITO FEDERAL",
        "tags": ["PMDF", "QOPM", "QPPMC", "POLICIAL MILITAR", "POLICIA MILITAR"]
    },
    "SSP-DF": {
        "name": "SECRETARIA DE SEGURANÇA PÚBLICA",
        "tags": [
            "SOPI",
            "OPERACOES INTEGRADAS",
            "SEGURANCA PUBLICA",
            "SSP",
            "00050-",
            "SANDRO AVELAR",
            "SANDRO TORRES AVELAR",
            "CINTIA QUEIROZ DE CASTRO"
        ]
    }
}


URL_DODF_DIA = "https://dodf.df.gov.br/index/jornal-json"

HEADERS = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "document",
            "Host": "dodf.df.gov.br",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
}

DODF_HEAD = """
<head>
  <meta charset="UTF-8">
  <style>
    .container{
      padding-top: 20px;
      column-count: 2;
      column-gap: 20px;
    }
    table, td, tr {
      border: 1px solid black;
      border-collapse: collapse;
    }
    table {
      table-layout: fixed;
      width: 100%;
      word-wrap: break-word;
      margin-bottom: 15px;
      margin-top: 15px;
    }
    
    p {
      margin: 0;
      font-size: 6pt;
      -pdf-keep-with-next: true;
    }
    td p {
      margin: 1;
      margin-top: 2;
    }
    h1, h2, h3 {
      text-align:center;
      margin: 0;
    }
    h1{font-size: 12pt;}
    h2{font-size: 10pt;}
    h3{font-size: 8pt;}
    
    .footer_content{
      padding-top: 20px;
      font-size: 6pt;
      text-align:center;
    }
    }
  </style>
</head>
"""

def normalize_text(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text) if not unicodedata.combining(c)).upper()

format_paragraph = lambda paragraph, tags: f'<b style="color: red;>{paragraph}</b>' if any(normalize_text(tag) in normalize_text(paragraph) for tag in tags) else paragraph

# def documents_function(document, tags):
#     document = next(iter(document.values()))
#     paragraphs = document["texto"].split("<p>")
#     formatted_paragraphs = [format_paragraph(p, tags) for p in paragraphs]
#     formatted_text = "<p>".join(formatted_paragraphs)
#     print(formatted_text)
#     return f'<p style="text-align:center;"><b>{document["titulo"]}</b></p>{"" if document["preambulo"] is None else document["preambulo"]}{formatted_text}&nbsp;&nbsp;'
    

def get_dodf_title(organization, dodf_title):
  return f'''
  <div id="header_content">
    <h1>DODF {dodf_title}</h1>
    <h2>{organization}</h2>
    <h3>PUBLICAÇÕES DE INTERESSE</h3>
  </div>
  '''
def get_dodf_footer(dodf_url):
  return f'''<div class="footer_content">Original disponível em 
      <a href="{dodf_url}">{dodf_url}</a>
  </div>'''


def fetch_dodf_data(url):
    response = requests.get(url, headers=HEADERS)
    if not response.ok:
        return None
    return json.loads(response.text)

def extract_documents_with_tags(dodf_data, tags, dodf_title, dodf_footer):
    documents_dict = {}
    secoes = dodf_data["json"]["INFO"]
    documents_dict = dict()
    for secao in secoes.keys():
      orgaos = secoes[secao]
      for orgao in orgaos.keys():
        document = orgaos[orgao]["documentos"]
        documents_dict = {**documents_dict, **document}
    documents_params = documents_dict.values()
    # parsed_documents = lambda document: f'<p style="text-align:center;"><b>{document["titulo"]}</b></p>{"" if document["preambulo"] is None else document["preambulo"]}{document["texto"]}&nbsp;&nbsp;' if any(normalize_text(item) in normalize_text(document["texto"]) for item in tags) else ""
    # parsed_documents = documents_function(document, tags)
    # print(document["texto"].split("<p>"))
    parsed_documents = lambda document, tags: f'<p style="text-align:center;"><b>{document["titulo"]}</b></p>{"" if document["preambulo"] is None else document["preambulo"]}' + ''.join([format_paragraph(p, tags) for p in list(str(x) for x in BeautifulSoup(document["texto"]).find_all('p'))]) + '&nbsp;&nbsp;' if any(normalize_text(item) in normalize_text(document["texto"]) for item in tags) else ""
    # documents = map(parsed_documents,documents_params)
    documents = map(lambda document: parsed_documents(document, tags), documents_params)
    # print(parsed_documents)
    dodf_body = f'<body>{"".join([item for item in documents if item!=""])}</body>'
    dodf_html = f'<html>{DODF_HEAD}{dodf_title}<div class="container">{dodf_body}</div>{dodf_footer}</html>'
    return dodf_html

def generate_pdf_from_dict(data_dict, output_file):
    html_data = data_dict.encode("utf-8")
    pdf = HTML(string=html_data).write_pdf()

    with open(output_file, "wb") as pdf_file:
        pdf_file.write(pdf)