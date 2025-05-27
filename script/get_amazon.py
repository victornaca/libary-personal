from playwright.sync_api import sync_playwright
import json
from time import sleep

def pegar_livros_com_playwright():
    url = "https://www.amazon.com.br/b?node=13130368011"
    
    livros = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # headless=False para ver o que acontece no navegador
        page = browser.new_page()
        # # Desabilitar o carregamento de imagens e fontes para melhorar o desempenho
        page.route("**/*.{png,jpg,jpeg}", lambda route: route.abort())
        page.goto(url)

        # Aguarda a página carregar inicialmente
        page.wait_for_selector("li.a-carousel-card")
        
        # Rola a página e clica no botão "Ver mais" se necessário
        while True:
            # Extrai os livros da página
            livros_na_pagina = page.query_selector_all("li.a-carousel-card")
            for item in livros_na_pagina:
                nome = item.query_selector("span.dcl-truncate span").inner_text().strip()
                link_img = item.query_selector("img").get_attribute("src")
                preco_novo = item.query_selector("span.a-price .a-offscreen").inner_text().strip()
                preco_antigo_tag = item.query_selector("div.dcl-product-old-price-section .a-text-price .a-offscreen")
                preco_antigo = preco_antigo_tag.inner_text().strip() if preco_antigo_tag else None

                livros.append({
                    "nome_livro": nome,
                    "link_imagem": link_img,
                    "preco_novo": preco_novo,
                    "preco_antigo": preco_antigo
                })

            # Verifica se o botão "Ver mais" está presente usando XPath
            try:
                botao_ver_mais = page.query_selector("//html/body/div[2]/div[2]/div[58]/div/div/div[1]/div/div[2]/div[3]/div/div/div[3]/div")  # XPath para o botão
                if botao_ver_mais:
                    print("Clicando no botão 'Ver mais' para carregar mais livros...")
                    botao_ver_mais.click()
                    sleep(3)  # Aguarda um pouco para os novos itens carregarem
                else:
                    print("Não há mais livros para carregar.")
                    break
            except Exception as e:
                print(f"Erro ao tentar clicar no botão: {e}")
                break

        # Salva os dados extraídos em JSON
        with open("livros_appday_completo.json", "w", encoding="utf-8") as f_out:
            json.dump(livros, f_out, indent=2, ensure_ascii=False)

        print(f"{len(livros)} livros extraídos e salvos em 'livros_appday_completo.json'.")
        browser.close()

if __name__ == "__main__":
    pegar_livros_com_playwright()
