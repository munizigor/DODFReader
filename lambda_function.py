import os
from datetime import datetime
import requests
from local_utils import *
import json
from pdf2docx import parse

def lambda_handler(event, context):
    BOT_TOKEN=os.getenv("bot_token")
    TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    ORGANIZATIONS = ORGANIZATIONS_FILE[event["mode"]] if isinstance(event, dict) else ORGANIZATIONS_FILE[json.loads(event).get("mode")]
    #Gravar os dados em uma pasta temporaria
    os.chdir('/tmp')
    dodf_data = fetch_dodf_data(URL_DODF_DIA)
    if dodf_data:
        dodf_files = {}
        dodf_name = dodf_data['lstJornalDia'][0].replace("\n", "")
        for organization in ORGANIZATIONS.keys():
            organization_name = ORGANIZATIONS[organization]["name"]
            organization_tags = ORGANIZATIONS[organization]["tags"]
            organization_chats = ORGANIZATIONS[organization].get("chats", [])
            output_pdf_file = f"{organization} - {dodf_name}"
            dodf_url = dodf_data["json"]["linkJornal"]
            dodf_title = dodf_data["json"]["tituloSangria"]
            dodf_header = get_dodf_title(organization_name, dodf_title)
            dodf_footer = get_dodf_footer(dodf_url)
            documents_with_tags = extract_documents_with_tags(dodf_data, organization_tags, dodf_header, dodf_footer)
            generate_pdf_from_dict(documents_with_tags, output_pdf_file)
            dodf_files[organization_name]=output_pdf_file

            for chat in organization_chats:
                # output_doc_file = output_pdf_file.replace(".pdf",".docx")
                # parse(output_pdf_file, output_doc_file)
                with open(output_pdf_file, 'rb') as document:
                    # Configura os parâmetros da requisição
                    data = {"chat_id": chat, 
                            "caption": f"{organization}\n\nPublicações de Interesse no DODF {dodf_title}"}
                    files = {"document": document}
                    # Faz a requisição à API do Telegram
                    response = requests.post(TELEGRAM_URL, data=data, files=files)
                    response.raise_for_status()
        return f"Documentos enviados com sucesso às {datetime.now()}"
    else:
        print("Erro ao obter dados do DODF.")