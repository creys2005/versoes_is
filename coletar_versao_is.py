import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd

# URL do Webhook do Discord (substitua pelo seu Webhook)
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1336025851548139692/3nQecQ7_MuNg4Rikzng8AfcPiP-F9QdV_ls_GRSij96CNQ12IWE2l81Zl0xTWtx3AoQM"

def enviar_mensagem_discord(mensagens):
    """Envia mensagens para um canal do Discord via Webhook, respeitando o limite de 2000 caracteres"""
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    mensagem_atual = ""
    for mensagem in mensagens:
        if len(mensagem_atual) + len(mensagem) > 2000:
            requests.post(DISCORD_WEBHOOK_URL, json={"content": mensagem_atual}, headers=headers)
            mensagem_atual = ""
        mensagem_atual += mensagem + "\n"
    
    if mensagem_atual:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": mensagem_atual}, headers=headers)

def coletar_versao_is():
    # Configurar o navegador
    options = Options()
    options.add_argument("--headless")  # Executa sem abrir o navegador
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Inicializar o WebDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # Ler a planilha
    arquivo_planilha = "lista_clientes_is.xlsx"
    df = pd.read_excel(arquivo_planilha, dtype={"Versão": str})  # Garantir que a coluna 'Versão' seja string
    
    # Verificar se as colunas esperadas existem
    if 'Cliente' not in df.columns or 'Link' not in df.columns:
        print("As colunas 'Cliente' e 'Link' não foram encontradas na planilha.")
        return
    
    # Criar a coluna 'Versão' caso não exista
    if 'Versão' not in df.columns:
        df['Versão'] = ''
    
    mensagens_discord = ["📢 **Atualização das Versões do Sistema IS** 📢\n"]
    
    try:
        for index, row in df.iterrows():
            cliente = row['Cliente']
            link = row['Link']
            if pd.notna(link):  # Verifica se o link não é NaN
                driver.get(link)
                
                try:
                    # Aguardar até 15 segundos para que o elemento apareça
                    versao_element = WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.XPATH, "//*[@id='router-out']/app-login/div/div[2]/div/div[2]/div/div/is-footer-versao-sistema/div/u"))
                    )
                    
                    versao_texto = str(versao_element.text.split('\n')[0].strip())  # Pega apenas a primeira linha do resultado e remove espaços extras
                    df.at[index, 'Versão'] = versao_texto  # Atualiza a célula corretamente
                    print(f"Versão do Sistema IS para {cliente} ({link}): {versao_texto}")
                    
                    mensagens_discord.append(f"🔹 **[{cliente}]({link})** → `{versao_texto}`")
                except Exception as e:
                    df.at[index, 'Versão'] = "Erro ao coletar"
                    print(f"Erro ao coletar a versão do sistema para {cliente} ({link}):", e)
                    mensagens_discord.append(f"⚠️ **[{cliente}]({link})** → `Erro ao coletar`")
        
    finally:
        driver.quit()
    
    # Salvar a planilha original com as atualizações
    df.to_excel(arquivo_planilha, index=False)
    print(f"Processo concluído. Planilha atualizada: {arquivo_planilha}.")
    
    # Enviar as mensagens para o Discord respeitando o limite de 2000 caracteres
    enviar_mensagem_discord(mensagens_discord)

if __name__ == "__main__":
    coletar_versao_is()
