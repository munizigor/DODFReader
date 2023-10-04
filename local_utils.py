import requests
import json
from weasyprint import HTML, CSS
from bs4 import BeautifulSoup
import unicodedata

with open('./organizations.json') as org_file:
  ORGANIZATIONS_FILE = json.load(org_file)

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

STYLESHEET = CSS(string="""
                 
     table {
    table-layout: fixed;
    border-collapse: collapse;
    width: 100%;
    font-size: 4pt;
    border: 1px solid #000;
  }

  th, td {
    border: 1px solid #000;
    padding: 8px;
    text-align: left;
    page-break-inside: avoid;
    overflow-wrap: break-word; /* ou word-wrap: break-word; */
  }

  @page {
    size: A4;
    font-size: 6pt;
    @bottom-right {
      content: counter(page) "/" counter(pages);
    }
    @bottom-center {
      content: "@AutoClipping - Criado por Ten-Cel. Muniz - CBMDF";
    }
  }

  .container {
    padding-top: 40px;
    column-count: 2;
    column-gap: 20px;
    overflow-wrap: break-word;
    font-size: min(3vw, 6pt);
  }

  .organization p{
    color: red;
    font-weight: bold;
  }

  p {
    margin: 0;
    font-size: 7pt;
    line-height: 1.2;
    -pdf-keep-with-next: true;
  }

  td p {
    margin: 1px 0;
  }

  h1, h2, h3 {
    text-align: center;
    margin: 0;
  }

  h1 { font-size: 12pt; }
  h2 { font-size: 10pt; }
  h3 { font-size: 8pt; }

  .footer_content {
    padding-top: 20px;
    font-size: 6pt;
    text-align: center;
  }
""")

DODF_HEAD = """
<head>
  <meta charset="UTF-8">
  <style>

    
  </style>

</head>
"""

def normalize_text(text):
    if text:
      return ''.join(c for c in unicodedata.normalize('NFD', text) if not unicodedata.combining(c)).upper()
    else:
      return ""

format_paragraph = lambda paragraph, tags: f'<span class="organization">{paragraph}</span>' if any(normalize_text(tag) in normalize_text(paragraph) for tag in tags) else paragraph

def insert_span(html_str, target_names, className):
    soup = BeautifulSoup(html_str, 'html.parser')

    for p in soup.find_all('p', text=lambda t: any(normalize_text(name) in normalize_text(t) for name in target_names)):
        if p.parent.class_ != className:
            span_tag = soup.new_tag('span', attrs={'class': className})
            p.wrap(span_tag)

    return str(soup)

def get_dodf_title(organization, dodf_title):
  return f'''
  <div id="header_content">
    <h1>DODF {dodf_title}</h1>
    <span class="organization"><h2>{organization}</h2></span>
    <h3>PUBLICAÇÕES DE INTERESSE</h3>
  </div>
  '''
def get_dodf_footer(dodf_url):
  return f'''<div class="footer_content">
    <p>Publicação original disponível em <a href="{dodf_url}">{dodf_url}</a></p>
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
    parsed_documents = lambda document, tags: f'<p style="text-align:center;"><b>{document["titulo"]}</b></p>{"" if document["preambulo"] is None else document["preambulo"]}' + ''.join([x for x in document["texto"]]) + '&nbsp;&nbsp;' if any(normalize_text(item) in normalize_text(document["texto"]) for item in tags) else ""
    documents = map(lambda document: parsed_documents(document, tags), documents_params)
    dodf_body = f'<body>{"".join([item for item in documents if item!=""])}</body>'
    dodf_body = insert_span(dodf_body, tags, "organization")
    dodf_html = f'<html>{DODF_HEAD}{dodf_title}<div class="container">{dodf_body}</div>{dodf_footer}</html>'
    return dodf_html

def generate_pdf_from_dict(data_dict, output_file):
    html_data = data_dict.encode("utf-8")
    pdf = HTML(string=html_data).write_pdf(stylesheets=[STYLESHEET])

    with open(output_file, "wb") as pdf_file:
        pdf_file.write(pdf)