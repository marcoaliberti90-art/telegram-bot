import sqlite3
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters, ContextTypes
)

TOKEN = os.getenv("BOT_TOKEN")

# ---------------- DB ----------------
def init_db():
    conn = sqlite3.connect("db.sqlite3")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS interventi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_veicolo TEXT,
        cv TEXT,
        categoria TEXT,
        altezza TEXT,
        codice TEXT,
        serial_smontato TEXT,
        serial_montato TEXT,
        data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

def salva_db(data):
    conn = sqlite3.connect("db.sqlite3")
    c = conn.cursor()

    c.execute("""
    INSERT INTO interventi
    (id_veicolo, cv, categoria, altezza, codice, serial_smontato, serial_montato)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("id"),
        data.get("cv"),
        data.get("categoria"),
        data.get("altezza"),
        data.get("codice"),
        data.get("smontato"),
        data.get("montato")
    ))

    conn.commit()
    conn.close()

# ---------------- STATI ----------------
(ID, CV, K, ALTEZZA, CODICE,
 SERIAL_SMONTATO, SERIAL_MONTATO,
 CATEGORIA, SERIAL_SCELTA) = range(9)

# ---------------- KEYBOARDS ----------------
def kb_cv():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("CV1", callback_data="CV1"),
         InlineKeyboardButton("CV2", callback_data="CV2")]
    ])

def kb_k():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("K1", callback_data="K1"),
         InlineKeyboardButton("K2", callback_data="K2")],
        [InlineKeyboardButton("K3", callback_data="K3"),
         InlineKeyboardButton("K4", callback_data="K4")],
        [InlineKeyboardButton("K5", callback_data="K5"),
         InlineKeyboardButton("NO KATIUM", callback_data="NO")]
    ])

def kb_altezza():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Alto", callback_data="ALTO"),
         InlineKeyboardButton("Basso", callback_data="BASSO")]
    ])

def kb_codice():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("318301", callback_data="318301")],
        [InlineKeyboardButton("561051", callback_data="561051")],
        [InlineKeyboardButton("561052", callback_data="561052")]
    ])

def kb_si_no():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("SI", callback_data="SI"),
         InlineKeyboardButton("NO", callback_data="NO")]
    ])

# ---------------- FLOW ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("🔧 Inserisci ID veicolo:")
    return ID

async def id_veicolo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["id"] = update.message.text
    await update.message.reply_text("Seleziona CV:", reply_markup=kb_cv())
    return CV

async def cv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["cv"] = query.data
    await query.edit_message_text("Categoria:", reply_markup=kb_k())
    return K

async def k(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    scelta = query.data
    context.user_data["categoria"] = scelta

    if scelta == "NO":
        await query.edit_message_text("Inserisci categoria pezzo:")
        return CATEGORIA

    await query.edit_message_text("Altezza:", reply_markup=kb_altezza())
    return ALTEZZA

async def altezza(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["altezza"] = query.data
    await query.edit_message_text("Codice:", reply_markup=kb_codice())
    return CODICE

async def codice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    codice = query.data
    context.user_data["codice"] = codice

    if codice in ["561051", "561052"]:
        await query.edit_message_text("Seriale SMONTATO:")
        return SERIAL_SMONTATO

    salva_db(context.user_data)
    await query.edit_message_text("✅ Salvato")
    return ConversationHandler.END

async def serial_smontato(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["smontato"] = update.message.text
    await update.message.reply_text("Seriale MONTATO:")
    return SERIAL_MONTATO

async def serial_montato(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["montato"] = update.message.text
    salva_db(context.user_data)
    await update.message.reply_text("✅ Salvato")
    return ConversationHandler.END

async def categoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["categoria"] = update.message.text
    await update.message.reply_text("Vuoi inserire seriali?", reply_markup=kb_si_no())
    return SERIAL_SCELTA

async def serial_scelta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "SI":
        await query.edit_message_text("Seriale SMONTATO:")
        return SERIAL_SMONTATO

    salva_db(context.user_data)
    await query.edit_message_text("✅ Salvato")
    return ConversationHandler.END

# ---------------- MAIN ----------------
def main():
    init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ID: [MessageHandler(filters.TEXT, id_veicolo)],
            CV: [CallbackQueryHandler(cv)],
            K: [CallbackQueryHandler(k)],
            ALTEZZA: [CallbackQueryHandler(altezza)],
            CODICE: [CallbackQueryHandler(codice)],
            SERIAL_SMONTATO: [MessageHandler(filters.TEXT, serial_smontato)],
            SERIAL_MONTATO: [MessageHandler(filters.TEXT, serial_montato)],
            CATEGORIA: [MessageHandler(filters.TEXT, categoria)],
            SERIAL_SCELTA: [CallbackQueryHandler(serial_scelta)],
        },
        fallbacks=[]
    )

    app.add_handler(conv)

    print("Bot avviato...")
    app.run_polling()

if __name__ == "__main__":
    main()
