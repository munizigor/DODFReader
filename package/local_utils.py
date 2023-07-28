import requests
import json
from io import BytesIO
from xhtml2pdf import pisa
import unicodedata

bot_token="5144694768:AAFOrRICs066PoDx2Ed5IsC4JRnFNCx4apw"
chat_id="1404598001"

ORGANIZATIONS = {
    "CBMDF": {
        "name": "CORPO DE BOMBEIROS MILITAR DO DISTRITO FEDERAL",
        "tags": ["CBMDF", "QOBM", "QBMG", "BOMBEIRO", "BOMBEIRA", "00053-"]
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
    table, td, tr {
      border: 1px solid black;
      border-collapse: collapse;
    }
    table {
      width: 100%;
    }
    tr, td {
      white-space: nowrap;
    }
    table {
      -pdf-keep-with-next: true;
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
    @page  {
       size: a4;
       background-image: url('background.png');
       background-opacity: 0.05;
        @frame header_frame {           /* Static frame */
            -pdf-frame-content: header_content;
            left: 50pt; width: 512pt; top: 50pt; height: 80pt;
        }
        @frame col1_frame {             /* Content frame 1 */
            left: 44pt; width: 255pt; top: 110pt; height: 632pt;
        }
        @frame col2_frame {             /* Content frame 2 */
            left: 323pt; width: 255pt; top: 110pt; height: 632pt;
        }
        @frame footer_frame {           /* Static frame */
            -pdf-frame-content: footer_content;
            left: 50pt; width: 512pt; top: 792pt; height: 30pt;
            /* Reference: https://xhtml2pdf.readthedocs.io/en/latest/format_html.html?highlight=%40page#named-page-templates*/
        }
    }
  </style>
</head>
"""

def normalize_text(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text) if not unicodedata.combining(c)).upper()

def get_dodf_title(organization, dodf_title):
  return f'''
  <div id="header_content">
    <h1>DODF {dodf_title}</h1>
    <h2>{organization}</h2>
    <h3>PUBLICAÇÕES DE INTERESSE</h3>
  </div>
  '''
def get_dodf_footer(dodf_url):
  return f'''<div id="footer_content">Página <pdf:pagenumber>
      de <pdf:pagecount> - Original disponível em 
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
    
    documents_function = lambda document: f'<p style="text-align:center;"><b>{document["titulo"]}</b></p>{"" if document["preambulo"] is None else document["preambulo"]}{document["texto"]}&nbsp;&nbsp;' if any(normalize_text(item) in normalize_text(document["texto"]) for item in tags) else ""
    documents = map(documents_function,documents_params)
    dodf_body = f'<body>{"".join([item for item in documents if item!=""])}</body>'
    dodf_html = f'<html>{DODF_HEAD}{dodf_title}{dodf_body}{dodf_footer}</html>'
    return dodf_html

def generate_pdf_from_dict(data_dict, output_file):
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(data_dict.encode("utf-8")), result)
    if not pdf.err:
        final_file=result.getvalue()
    with open(output_file,"wb") as dodf:
        dodf.write(final_file)