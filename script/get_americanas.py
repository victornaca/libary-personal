import requests
from bs4 import BeautifulSoup
import json
import time

# Lista para armazenar todos os livros
livros = []

# Conjunto para armazenar nomes dos livros já adicionados (evita duplicatas)
titulos_ja_processados = set()

# Loop de páginas (ajuste o range se quiser mais páginas)
for page in range(5):
    url = f"https://www.americanas.com.br/livros?page={page}"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # Pega o script com o JSON bruto da aplicação
    next_data_script = soup.find("script", id="__NEXT_DATA__")
    
    if next_data_script:
        json_data = json.loads(next_data_script.string)
        
        # Navegar na estrutura até os produtos
        produtos = json_data["props"]["pageProps"]["data"]["search"]["products"]["edges"]

        for item in produtos:
            node = item["node"]
            nome = node.get("isVariantOf", {}).get("name", None)

            if not nome or nome.upper() in titulos_ja_processados:
                continue  # Pula se o nome estiver ausente ou já processado
            
            nome = nome.upper()
            titulos_ja_processados.add(nome)

            categorias = node.get("categories", [])
            categoria_tratada = None
            if categorias:
                try:
                    categoria_tratada = categorias[0].split("/")[2].replace("-", " ").upper()
                except IndexError:
                    categoria_tratada = None

            offers = node.get("offers", {}).get("offers", [])
            preco_antigo = None
            preco_novo = None
            if offers:
                preco_antigo = offers[0].get("listPrice", None)
                preco_novo = offers[0].get("price", preco_antigo)

            imagem_url = node.get("image", [{}])[0].get("url", None)

            livro = {
                "nome_livro": nome,
                "categoria": categoria_tratada,
                "preco_antigo": preco_antigo,
                "preco_novo": preco_novo,
                "imagem_url": imagem_url
            }

            livros.append(livro)

    print(f"Página {page} processada.")
    print(f"Total de livros coletados: {len(livros)}")
    time.sleep(1)  # Delay entre as páginas

# Salvar os livros em JSON
with open("livros_americanas.json", "w", encoding="utf-8") as file:
    json.dump(livros, file, ensure_ascii=False, indent=4)

print("Dados salvos em 'livros_americanas.json'")
