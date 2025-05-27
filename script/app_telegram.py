import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from phi.agent import Agent
from phi.model.groq import Groq
from phi.tools.googlesearch import GoogleSearch
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configurações
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

########## Agentes de IA (mesmos do Streamlit) ##########

def create_book_info_agent():
    return Agent(
        name="Agente de Informações de Livros",
        model=Groq(id="deepseek-r1-distill-llama-70b"),
        tools=[GoogleSearch()],
        instructions=[
            "Forneça informações concisas sobre o livro incluindo:",
            "- Título e autor",
            "- Sinopse resumida (máximo 5 frases)",
            "- Gênero literário",
            "- Número de páginas",
            "- Nota do livro de 0 a 5 do site Goodreads",
            "- Preço médio estimado (formato: R$ XXX,XX)",
            "NÃO inclua fontes ou referências externas"
        ],
        show_tool_calls=False,
        markdown=True
    )

def create_recommendation_agent():
    return Agent(
        name="Agente de Recomendações",
        model=Groq(id="deepseek-r1-distill-llama-70b"),
        tools=[GoogleSearch()],
        instructions=[
        "INSTRUÇÕES ESTRITAS:",
        "1. Recomende EXATAMENTE 5 livros similares ao solicitado",
        "2. Para cada livro, forneça APENAS:",
        "   - Título em negrito",
        "   - Autor",
        "   - Gênero literário",
        "   - Preço médio estimado (formato: R$ XX,XX)",
        "   - Nota do livro de 0 a 5 do site Goodreads",
        "   - Resumo sobre o livro (maximo 5 frases)",
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

########## Funções de Processamento ##########

async def get_book_info(book_query: str) -> str:
    agent = create_book_info_agent()
    response = agent.run(f"Informações sobre: {book_query}")
    return clean_response(response.content)

async def get_recommendations(book_query: str) -> str:
    agent = create_recommendation_agent()
    response = agent.run(f"Recomende livros similares a: {book_query}")
    return clean_response(response.content)

def clean_response(text: str) -> str:
    """Remove metadados e formata para Telegram"""
    text = re.sub(r"Running:.*?\n\n", "", text, flags=re.DOTALL)
    text = re.sub(r"\*\*(.*?)\*\*", r"*\1*", text)  # Markdown para Telegram
    return text.strip()

########## Handlers do Telegram ##########

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "📚 *Catálogo Inteligente de Livros da Sarah*\n\n"
        "Envie o nome de um livro que deseja pesquisar!\n"
        "Exemplos:\n- 1984 (George Orwell)\n- O Senhor dos Anéis\n- Sapiens",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: CallbackContext) -> None:
    book_query = update.message.text
    if not book_query:
        await update.message.reply_text("Por favor, digite o nome de um livro.")
        return
    
    try:
        # Envia status de processamento
        processing_msg = await update.message.reply_text("🔍 Procurando informações...")
        
        # Obtém informações do livro
        book_info = await get_book_info(book_query)
        await context.bot.edit_message_text(
            chat_id=processing_msg.chat_id,
            message_id=processing_msg.message_id,
            text=f"📖 *Informações do Livro*\n\n{book_info}",
            parse_mode="Markdown"
        )
        
        # Obtém recomendações
        rec_msg = await update.message.reply_text("📚 Buscando recomendações...")
        recommendations = await get_recommendations(book_query)
        await context.bot.edit_message_text(
            chat_id=rec_msg.chat_id,
            message_id=rec_msg.message_id,
            text=f"🌟 *Livros Recomendados*\n\n{recommendations}",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ocorreu um erro: {str(e)}")

########## Configuração do Bot ##########

def main() -> None:
    application = Application.builder().token(TOKEN).build()
    
    # Comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ajuda", start))
    
    # Mensagens de texto
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Inicia o bot
    application.run_polling()

if __name__ == "__main__":
    main()