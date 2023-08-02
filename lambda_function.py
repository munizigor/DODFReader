import os
from datetime import datetime
import requests
from local_utils import *

def lambda_handler(event, context):
    BOT_TOKEN=os.getenv("bot_token")
    CHAT_ID=os.getenv("chat_id")
    #Gravar os dados em uma pasta temporaria
    os.chdir('/tmp')
    dodf_data = fetch_dodf_data(URL_DODF_DIA)
    if dodf_data:
        dodf_files = {}
        dodf_name = dodf_data['lstJornalDia'][0].replace("\n", "")
        for organization in ORGANIZATIONS.keys():
            organization_name = ORGANIZATIONS[organization]["name"]
            organization_tags = ORGANIZATIONS[organization]["tags"]
            output_pdf_file = f"{organization} - {dodf_name}"
            dodf_url = dodf_data["json"]["linkJornal"]
            dodf_title = get_dodf_title(organization_name,dodf_data["json"]["tituloSangria"])
            dodf_footer = get_dodf_footer(dodf_url)
            documents_with_tags = extract_documents_with_tags(dodf_data, organization_tags, dodf_title, dodf_footer)
            generate_pdf_from_dict(documents_with_tags, output_pdf_file)
            dodf_files[organization_name]=output_pdf_file

        #Define a URL da API do Telegram
        telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
        for _, path in dodf_files.items():
            with open(path, 'rb') as document:
                # Configura os parâmetros da requisição
                data = {"chat_id": CHAT_ID, 
                        "caption": "Bom dia. Segue resumo do DODF de hoje."}
                files = {"document": document}
                # Faz a requisição à API do Telegram
                response = requests.post(telegram_url, data=data, files=files)
                response.raise_for_status()
        return f"Documentos enviados com sucesso às {datetime.now()}"
    else:
        print("Erro ao obter dados do DODF.")