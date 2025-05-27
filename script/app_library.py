# Catálogo de Livros Inteligente com Agentes de IA

# Imports
import re
import streamlit as st
import pandas as pd
from phi.agent import Agent
from phi.model.groq import Groq
from phi.tools.duckduckgo import DuckDuckGo
from phi.tools.newspaper_tools import NewspaperTools
from dotenv import load_dotenv

# Carrega o arquivo de variáveis de ambiente
load_dotenv()

########## Agentes de IA ##########

# Agente para buscar informações sobre livros
dsa_agente_info_livros = Agent(
    name="Agente de Informações de Livros",
    model=Groq(id="deepseek-r1-distill-llama-70b"),
    tools=[DuckDuckGo(), NewspaperTools()],
    instructions=[
        "Forneça informações concisas sobre o livro incluindo:",
        "- Título e autor",
        "- Sinopse resumida (máximo 5 frases)",
        "- Gênero literário",
        "- Número de páginas",
        "- Preço médio estimado (formato: R$ XXX,XX)",
        "NÃO inclua fontes ou referências externas"
    ],
    show_tool_calls=True,
    markdown=True
)

# Agente para recomendações de livros
dsa_agente_recomendacoes = Agent(
    name="Agente de Recomendações",
    model=Groq(id="deepseek-r1-distill-llama-70b"),
    tools=[DuckDuckGo(), NewspaperTools()],
    instructions=[
        "INSTRUÇÕES ESTRITAS:",
        "1. Recomende EXATAMENTE 10 livros similares ao solicitado",
        "2. Para cada livro, forneça APENAS:",
        "   - Título em negrito",
        "   - Autor",
        "   - Gênero literário",
        "   - Preço médio estimado (formato: R$ XX,XX)",
        "   - Breve resumo sobre o livro (maximo 5 frases)",
        "   - Breve motivo da recomendação (1 frase)",
        "3. Formate como lista markdown simples",
        "4. NÃO mostre seu processo de pensamento",
        "5. NÃO inclua links ou fontes",
        "6. NÃO explique como chegou às recomendações",
        "7. APENAS liste os livros no formato solicitado"
    ],
    show_tool_calls=False,
    markdown=True
)

# Agente coordenador
multi_ai_agent = Agent(
    team=[dsa_agente_info_livros, dsa_agente_recomendacoes],
    model=Groq(id="deepseek-r1-distill-llama-70b"),
    instructions=[
        "Coordene a equipe de agentes para fornecer uma experiência completa ao usuário",
        "Garanta que todas as informações solicitadas sejam fornecidas",
        "Formate a saída de maneira organizada e agradável"
    ],
    show_tool_calls=True,
    markdown=True
)

########## App Web ##########

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Catálogo Inteligente de Livros da Sarah", 
    page_icon="📚", 
    layout="wide",
    menu_items={
        'About': "Catálogo de Livros Inteligente da Sarah, desenvolvido pelo seu namorado"
    }
)

# CSS personalizado
st.markdown("""
<style>
    .stApp {
        background-color: #f5f5f5;
    }
    .title {
        color: #4a4a4a;
        text-align: center;
    }
    .stButton>button {
        background-color: #4a8cff;
        color: white;
        border-radius: 5px;
        padding: 10px 24px;
    }
    .stTextInput>div>div>input {
        border-radius: 5px;
        padding: 10px;
    }
    .book-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .price-card {
        background-color: #f0f8ff;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
    }
    .recommendation-card {
        background-color: #fffaf0;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Barra Lateral com instruções
st.sidebar.title("📚 Catálogo Inteligente de Livros da Sarah")
st.sidebar.markdown("""
### Como Utilizar:

1. Digite o nome do livro no campo principal
2. Clique no botão **Buscar Livro**
3. Aguarde enquanto nossos agentes de IA coletam as informações

### Recursos Disponíveis:
- Informações completas sobre o livro
- Comparação de preços nas principais livrarias
- Recomendações personalizadas de livros similares

### Exemplos:
- 1984 (George Orwell)
- O Senhor dos Anéis
- Harry Potter e a Pedra Filosofal
- Sapiens (Yuval Noah Harari)

Desenvolvido com IA pela Data Science Academy
""")

# Botão de suporte na barra lateral
if st.sidebar.button("✉️ Suporte"):
    st.sidebar.write("Dúvidas ou sugestões? Envie e-mail para: victorfernandes_cpv@outlook.com")

# Título principal
st.title("📚 Catálogo Inteligente de Livros")
st.markdown("""
Encontre informações detalhadas sobre qualquer livro, compare preços nas principais livrarias e descubra novas recomendações literárias.
""")

# Caixa de texto para input do usuário
book_query = st.text_input("Digite o nome do livro (e autor se possível):")

# Se o usuário pressionar o botão, entramos neste bloco
if st.button("Buscar Livro"):
    if book_query:
        # Container principal para os resultados
        main_container = st.container()
        
        with main_container:
            st.subheader(f"Resultados para: {book_query}")
            
            # Seção 1: Informações do Livro
            with st.spinner("Buscando informações sobre o livro..."):
                info_col, _ = st.columns([3, 1])
                with info_col:
                    st.markdown("### 📖 Informações do Livro")
                    book_info_response = dsa_agente_info_livros.run(f"Obtenha informações detalhadas sobre o livro: {book_query}")
                    clean_info = re.sub(r"Running:.*?\n\n", "", book_info_response.content, flags=re.DOTALL)
                    st.markdown(clean_info, unsafe_allow_html=True)
            
            # Seção 3: Recomendações
            with st.spinner("Preparando recomendações personalizadas..."):
                st.markdown("### 🔍 Você Pode Gostar Também")
                recommendations_response = dsa_agente_recomendacoes.run(f"Recomende 10 livros similares a: {book_query}")
                clean_recommendations = re.sub(r"Running:.*?\n\n", "", recommendations_response.content, flags=re.DOTALL)
                st.markdown(clean_recommendations, unsafe_allow_html=True)
    else:
        st.error("Por favor, digite o nome de um livro para buscar.")

# Rodapé
st.markdown("---")
st.markdown("""
**Catálogo Inteligente de Livros** - Desenvolvido pelo seu grande amor <3
📚 Encontre seu próximo livro favorito!
""")