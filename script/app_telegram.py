import os
import re
from flask import Flask
import threading
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    CallbackContext,
    filters,
)
from phi.agent import Agent
from phi.model.groq import Groq
from phi.tools.googlesearch import GoogleSearch
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


##############################
# GAMBIARRA PRA RODAR NO RENDER
##############################
app = Flask('')

@app.route('/')
def home():
    return "✅ Bot da Sarah está rodando!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = threading.Thread(target=run)
    t.start()


##############################
# AGENTES
##############################

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
            "2. Para cada livro, forneça:",
            "   - Título em negrito",
            "   - Autor",
            "   - Gênero literário",
            "   - Preço médio estimado (formato: R$ XX,XX)",
            "   - Nota do livro de 0 a 5 do site Goodreads",
            "   - Resumo (máximo 5 frases)",
            "   - Breve motivo da recomendação (1 frase)",
            "3. Formate como lista markdown simples",
            "4. NÃO inclua links ou explicações adicionais"
        ],
        show_tool_calls=False,
        markdown=True
    )


##############################
# FUNÇÕES DE PROCESSAMENTO
##############################

async def get_book_info(book_query: str) -> str:
    agent = create_book_info_agent()
    response = agent.run(f"Informações sobre: {book_query}")
    return clean_response(response.content)


async def get_recommendations(book_query: str) -> str:
    agent = create_recommendation_agent()
    response = agent.run(f"Recomende livros similares a: {book_query}")
    return clean_response(response.content)


def clean_response(text: str) -> str:
    text = re.sub(r"Running:.*?\n\n", "", text, flags=re.DOTALL)
    text = re.sub(r"\*\*(.*?)\*\*", r"*\1*", text)
    return text.strip()


def get_send_function(update: Update):
    if update.message:
        return update.message.reply_text
    elif update.callback_query:
        return update.callback_query.message.reply_text
    else:
        raise ValueError("Update não possui message nem callback_query")


##############################
# INTERFACE - BOTÕES
##############################

def main_menu():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📖 Diagnóstico do Livro", callback_data='diagnostico')],
            [InlineKeyboardButton("🌟 Recomendar Livros", callback_data='recomendacao')],
        ]
    )


def post_diagnostico_menu():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🌟 Recomendar livros a partir desse", callback_data='recomendacao')],
            [InlineKeyboardButton("🔄 Recomeçar", callback_data='inicio')],
        ]
    )


def post_recommendation_menu():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔄 Recomeçar", callback_data="inicio")],
        ]
    )


##############################
# HANDLERS
##############################

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    await update.message.reply_text(
        "👋 *Bem-vindo ao Catálogo Inteligente de Livros da Sarah!*\n\n"
        "Escolha uma opção abaixo:",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )


async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'inicio':
        context.user_data.clear()
        await query.edit_message_text(
            "👋 *Menu Principal*\n\nEscolha uma opção:",
            reply_markup=main_menu(),
            parse_mode="Markdown"
        )

    elif query.data == 'diagnostico':
        context.user_data['action'] = 'diagnostico'
        await query.edit_message_text(
            "📖 *Diagnóstico do Livro*\n\nDigite o nome do livro que deseja analisar:",
            parse_mode="Markdown"
        )

    elif query.data == 'recomendacao':
        if 'last_book' in context.user_data:
            await process_recommendation(update, context, context.user_data['last_book'])
        else:
            context.user_data['action'] = 'recomendacao'
            await query.edit_message_text(
                "🌟 *Recomendar Livros*\n\nDigite o nome de um livro para obter recomendações:",
                parse_mode="Markdown"
            )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    action = context.user_data.get('action')

    if not action:
        await update.message.reply_text(
            "❗ Por favor, selecione uma opção no menu primeiro.",
            reply_markup=main_menu()
        )
        return

    book_query = update.message.text
    context.user_data['last_book'] = book_query

    if action == 'diagnostico':
        await process_diagnostico(update, context, book_query)
    elif action == 'recomendacao':
        await process_recommendation(update, context, book_query)


async def process_diagnostico(update: Update, context: ContextTypes.DEFAULT_TYPE, book_query: str):
    send = get_send_function(update)
    processing_msg = await send("🔍 Buscando informações do livro...")

    try:
        info = await get_book_info(book_query)
        await context.bot.edit_message_text(
            chat_id=processing_msg.chat_id,
            message_id=processing_msg.message_id,
            text=f"📖 *Informações do Livro*\n\n{info}",
            parse_mode="Markdown"
        )
        await send(
            "O que deseja fazer agora?",
            reply_markup=post_diagnostico_menu(),
        )
    except Exception as e:
        await send(f"❌ Ocorreu um erro: {str(e)}")


async def process_recommendation(update: Update, context: CallbackContext, book_query: str) -> None:
    send = get_send_function(update)

    processing_msg = await send("📚 Buscando recomendações...")

    try:
        recommendations = await get_recommendations(book_query)

        await send(
            text=f"🌟 *Livros Recomendados*\n\n{recommendations}",
            parse_mode="Markdown"
        )

        await send(
            "O que deseja fazer agora?",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("🔍 Buscar outro livro", callback_data="recomendacao")],
                    [InlineKeyboardButton("🔄 Recomeçar", callback_data="inicio")]
                ]
            )
        )

        await context.bot.delete_message(
            chat_id=processing_msg.chat_id,
            message_id=processing_msg.message_id
        )

    except Exception as e:
        await send(f"❌ Ocorreu um erro: {str(e)}")


##############################
# CONFIGURAÇÃO DO BOT
##############################

def main() -> None:
    keep_alive()  # Ativa a gambiarra para manter o Render feliz

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ajuda", start))

    application.add_handler(CallbackQueryHandler(handle_buttons))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()


if __name__ == "__main__":
    main()
