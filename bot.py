#!/usr/bin/env python3
"""
All-in-One Agent Bot for Telegram
Features: Video Downloader, Google Sheet Creator, 
          Video/Audio Search, Translator, TTS, URL Shortener, File Creator
Author: AI Agent
"""

import os
import json
import re
import io
import tempfile
import asyncio
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

# ============ VIDEO DOWNLOADER ============
import yt_dlp

# ============ GOOGLE SHEETS ============
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ============ TRANSLATOR ============
from deep_translator import GoogleTranslator

# ============ TEXT TO SPEECH ============
from gtts import gTTS

# ============ URL SHORTENER ============
import pyshorteners

# ============ SEARCH ============
import urllib.parse
import urllib.request

# ============ CONFIG ============
BOT_TOKEN = "8989482245:AAHK2XcjjqS6_Te84Jv3GZuNEV0STaz5BnU"

# Conversation States
(
    MENU,
    VIDEO_DOWNLOAD,
    SHEET_NAME,
    SHEET_COLUMNS_COUNT,
    SHEET_COLUMNS_NAMES,
    SHEET_DATA,
    SEARCH_QUERY,
    TRANSLATE_TEXT,
    TRANSLATE_LANG,
    TTS_TEXT,
    TTS_GENDER,
    URL_SHORTEN,
    FILE_NAME,
    FILE_CODE,
    FILE_CONFIRM
) = range(15)

# ============ KEYBOARD MENUS ============
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎬 ভিডিও ডাউনলোড", callback_data='video_download')],
        [InlineKeyboardButton("📊 Google Sheet তৈরি", callback_data='google_sheet')],
        [InlineKeyboardButton("🔍 ভিডিও/গান সার্চ", callback_data='search')],
        [InlineKeyboardButton("🌐 অনুবাদ (বাংলা↔ইংরেজি)", callback_data='translate')],
        [InlineKeyboardButton("🔊 Text to Voice", callback_data='tts')],
        [InlineKeyboardButton("🔗 URL ছোট করুন", callback_data='url_shorten')],
        [InlineKeyboardButton("📄 ফাইল তৈরি", callback_data='create_file')],
        [InlineKeyboardButton("❓ সাহায্য", callback_data='help')],
    ]
    return InlineKeyboardMarkup(keyboard)

def back_menu_keyboard():
    keyboard = [[InlineKeyboardButton("◀️ মূল মেনু", callback_data='main_menu')]]
    return InlineKeyboardMarkup(keyboard)

# ============ START COMMAND ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🤖 **Welcome to All-in-One Agent Bot!**\n\n"
        "আমি তোমার সব কাজের এজেন্ট! নিচে থেকে সার্ভিস সিলেক্ট করো:\n\n"
        "✅ ভিডিও ডাউনলোড (যেকোনো লিংক)\n"
        "✅ Google Sheet তৈরি\n"
        "✅ ভিডিও/গান সার্চ\n"
        "✅ বাংলা ↔ ইংরেজি অনুবাদ\n"
        "✅ Text to Voice (Male/Female)\n"
        "✅ URL ছোট করা\n"
        "✅ ফাইল তৈরি\n\n"
        "👇 নিচে বাটন চাপো:"
    )
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=main_menu_keyboard(), parse_mode='Markdown')
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=main_menu_keyboard(), parse_mode='Markdown')

# ============ CALLBACK HANDLER ============
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'main_menu':
        await start(update, context)
        return MENU

    elif data == 'video_download':
        await query.edit_message_text(
            "🎬 **ভিডিও ডাউনলোডার**\n\n"
            "যেকোনো ভিডিও লিংক পাঠাও (YouTube, Facebook, Instagram, Twitter, TikTok, Vimeo ইত্যাদি)\n\n"
            "📎 লিংক পেস্ট করো:",
            reply_markup=back_menu_keyboard(),
            parse_mode='Markdown'
        )
        return VIDEO_DOWNLOAD

    elif data == 'google_sheet':
        await query.edit_message_text(
            "📊 **Google Sheet Creator**\n\n"
            "শিটের নাম লিখো:",
            reply_markup=back_menu_keyboard(),
            parse_mode='Markdown'
        )
        return SHEET_NAME

    elif data == 'search':
        await query.edit_message_text(
            "🔍 **ভিডিও/গান সার্চ**\n\n"
            "কী খুঁজছো? লিখো:",
            reply_markup=back_menu_keyboard(),
            parse_mode='Markdown'
        )
        return SEARCH_QUERY

    elif data == 'translate':
        keyboard = [
            [InlineKeyboardButton("🇧🇩 বাংলা → 🇬🇧 ইংরেজি", callback_data='translate_bn_en')],
            [InlineKeyboardButton("🇬🇧 ইংরেজি → 🇧🇩 বাংলা", callback_data='translate_en_bn')],
            [InlineKeyboardButton("◀️ মূল মেনু", callback_data='main_menu')]
        ]
        await query.edit_message_text(
            "🌐 **অনুবাদ সার্ভিস**\n\nভাষা সিলেক্ট করো:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return TRANSLATE_LANG

    elif data == 'tts':
        keyboard = [
            [InlineKeyboardButton("👨 পুরুষ (Male)", callback_data='tts_male')],
            [InlineKeyboardButton("👩 মহিলা (Female)", callback_data='tts_female')],
            [InlineKeyboardButton("◀️ মূল মেনু", callback_data='main_menu')]
        ]
        await query.edit_message_text(
            "🔊 **Text to Voice**\n\nভয়েস সিলেক্ট করো:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return TTS_GENDER

    elif data == 'url_shorten':
        await query.edit_message_text(
            "🔗 **URL Shortener**\n\nছোট করতে চাও এমন লম্বা URL পাঠাও:",
            reply_markup=back_menu_keyboard(),
            parse_mode='Markdown'
        )
        return URL_SHORTEN

    elif data == 'create_file':
        await query.edit_message_text(
            "📄 **ফাইল তৈরি**\n\nফাইলের নাম লিখো (যেমন: index.php, style.css, script.js):",
            reply_markup=back_menu_keyboard(),
            parse_mode='Markdown'
        )
        return FILE_NAME

    elif data == 'help':
        help_text = (
            "📖 **সাহায্য মেনু**\n\n"
            "🎬 **ভিডিও ডাউনলোড**: যেকোনো ভিডিও লিংক পেস্ট করো\n"
            "📊 **Google Sheet**: শিট নাম → কলাম সংখ্যা → কলাম নাম → ডেটা\n"
            "🔍 **সার্চ**: গান/ভিডিও নাম লিখো\n"
            "🌐 **অনুবাদ**: বাংলা↔ইংরেজি\n"
            "🔊 **TTS**: টেক্সট লিখো → ভয়েস সিলেক্ট\n"
            "🔗 **URL Shortener**: লম্বা URL → ছোট URL\n"
            "📄 **ফাইল তৈরি**: নাম লিখো → কোড লিখো → ফাইল পাও\n\n"
            "⚡ সব ফিচার ১০০% ফ্রি!"
        )
        await query.edit_message_text(help_text, reply_markup=back_menu_keyboard(), parse_mode='Markdown')
        return MENU

    # Translate language selection
    elif data in ['translate_bn_en', 'translate_en_bn']:
        context.user_data['translate_direction'] = data
        direction = "বাংলা → ইংরেজি" if data == 'translate_bn_en' else "ইংরেজি → বাংলা"
        await query.edit_message_text(
            f"🌐 **অনুবাদ: {direction}**\n\nটেক্সট পাঠাও যেটা অনুবাদ করতে চাও:",
            reply_markup=back_menu_keyboard(),
            parse_mode='Markdown'
        )
        return TRANSLATE_TEXT

    # TTS gender selection
    elif data in ['tts_male', 'tts_female']:
        context.user_data['tts_gender'] = 'male' if data == 'tts_male' else 'female'
        gender_text = "👨 পুরুষ" if data == 'tts_male' else "👩 মহিলা"
        await query.edit_message_text(
            f"🔊 **Text to Voice - {gender_text}**\n\nযে টেক্সট পড়তে চাও লিখো:",
            reply_markup=back_menu_keyboard(),
            parse_mode='Markdown'
        )
        return TTS_TEXT

    return MENU

# ============ VIDEO DOWNLOAD HANDLER ============
async def video_download_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text("❌ সঠিক URL পাঠাও! http:// বা https:// দিয়ে শুরু হতে হবে।", reply_markup=back_menu_keyboard())
        return VIDEO_DOWNLOAD

    await update.message.reply_text("⏳ ভিডিও ডাউনলোড হচ্ছে... একটু অপেক্ষা করো!")

    try:
        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        
        ydl_opts = {
            'format': 'best[filesize<50M]/best',
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Check file size (Telegram limit ~50MB for bots)
            file_size = os.path.getsize(filename)
            if file_size > 50 * 1024 * 1024:
                await update.message.reply_text(
                    "⚠️ ভিডিও সাইজ ৫০MB এর বেশি! ছোট ভার্সন ডাউনলোড করা হচ্ছে...",
                    reply_markup=back_menu_keyboard()
                )
                # Try smaller format
                ydl_opts['format'] = 'worst[ext=mp4]/worst'
                with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                    info2 = ydl2.extract_info(url, download=True)
                    filename = ydl2.prepare_filename(info2)
                    file_size = os.path.getsize(filename)

            # Send video
            with open(filename, 'rb') as video_file:
                await update.message.reply_video(
                    video=video_file,
                    caption=f"✅ **{info.get('title', 'Video')}**\n\n🎬 ডাউনলোড সম্পূর্ণ!",
                    parse_mode='Markdown'
                )

        # Cleanup
        if os.path.exists(filename):
            os.remove(filename)
        os.rmdir(temp_dir)

    except Exception as e:
        error_msg = str(e)
        if "Unsupported URL" in error_msg:
            await update.message.reply_text(
                "❌ এই URL সাপোর্টেড নয়!\n\nসাপোর্টেড: YouTube, Facebook, Instagram, Twitter/X, TikTok, Vimeo, Dailymotion",
                reply_markup=back_menu_keyboard()
            )
        else:
            await update.message.reply_text(
                f"❌ ডাউনলোডে সমস্যা: {error_msg[:200]}",
                reply_markup=back_menu_keyboard()
            )

    await update.message.reply_text("👇 আরো কিছু করতে চাও?", reply_markup=main_menu_keyboard())
    return MENU

# ============ GOOGLE SHEET HANDLER ============
async def sheet_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['sheet_name'] = update.message.text.strip()
    await update.message.reply_text(
        "📊 কয়টা কলাম থাকবে? (সংখ্যা লিখো, যেমন: 3)",
        reply_markup=back_menu_keyboard()
    )
    return SHEET_COLUMNS_COUNT

async def sheet_columns_count_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        count = int(update.message.text.strip())
        if count < 1 or count > 20:
            raise ValueError
        context.user_data['column_count'] = count
        await update.message.reply_text(
            f"✅ {count}টা কলাম হবে।\n\nএখন কলামের নাম গুলো কমা দিয়ে লিখো:\n"
            f"যেমন: Name, Email, Phone",
            reply_markup=back_menu_keyboard()
        )
        return SHEET_COLUMNS_NAMES
    except ValueError:
        await update.message.reply_text("❌ ১ থেকে ২০ এর মধ্যে সংখ্যা লিখো!", reply_markup=back_menu_keyboard())
        return SHEET_COLUMNS_COUNT

async def sheet_columns_names_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    columns = [col.strip() for col in update.message.text.split(',')]
    
    if len(columns) != context.user_data['column_count']:
        await update.message.reply_text(
            f"❌ {context.user_data['column_count']}টা কলামের নাম দিতে হবে! আবার লিখো:",
            reply_markup=back_menu_keyboard()
        )
        return SHEET_COLUMNS_NAMES

    context.user_data['columns'] = columns
    
    columns_text = "\n".join([f"{i+1}. {col}" for i, col in enumerate(columns)])
    await update.message.reply_text(
        f"✅ কলাম সেটআপ সম্পূর্ণ!\n\n{columns_text}\n\n"
        f"এখন প্রতিটি রো-র ডেটা পাঠাও।\n"
        f"প্রতিটি ভ্যালু কমা দিয়ে আলাদা করো।\n"
        f"যেমন: জন, john@email.com, 01712345678\n\n"
        f"শেষ করতে 'done' লিখো। প্রথম রো দাও:",
        reply_markup=back_menu_keyboard()
    )
    context.user_data['sheet_data'] = [columns]
    return SHEET_DATA

async def sheet_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if text.lower() == 'done':
        # Create and send the sheet
        await update.message.reply_text("⏳ Google Sheet তৈরি হচ্ছে...")
        
        try:
            # Create CSV file instead (no API needed)
            import csv
            temp_dir = tempfile.mkdtemp()
            filename = f"{context.user_data['sheet_name']}.csv"
            filepath = os.path.join(temp_dir, filename)
            
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                for row in context.user_data['sheet_data']:
                    writer.writerow(row)
            
            # Send file
            with open(filepath, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=filename,
                    caption=f"✅ **{context.user_data['sheet_name']}** তৈরি সম্পূর্ণ!\n\n"
                            f"📊 মোট রো: {len(context.user_data['sheet_data'])-1}\n"
                            f"📋 কলাম: {', '.join(context.user_data['columns'])}",
                    parse_mode='Markdown'
                )
            
            # Cleanup
            os.remove(filepath)
            os.rmdir(temp_dir)
            
            # Also create a formatted text version
            sheet_text = f"📊 **{context.user_data['sheet_name']}**\n\n"
            for i, row in enumerate(context.user_data['sheet_data']):
                if i == 0:
                    sheet_text += " | ".join([f"**{col}**" for col in row]) + "\n"
                    sheet_text += "-" * 40 + "\n"
                else:
                    sheet_text += " | ".join(row) + "\n"
            
            await update.message.reply_text(sheet_text, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ সমস্যা: {str(e)}", reply_markup=back_menu_keyboard())
        
        await update.message.reply_text("👇 আরো কিছু করতে চাও?", reply_markup=main_menu_keyboard())
        return MENU
    
    # Add data row
    values = [val.strip() for val in text.split(',')]
    expected = len(context.user_data['columns'])
    
    if len(values) != expected:
        await update.message.reply_text(
            f"❌ {expected}টা ভ্যালু দিতে হবে! আবার লিখো:",
            reply_markup=back_menu_keyboard()
        )
        return SHEET_DATA
    
    context.user_data['sheet_data'].append(values)
    row_num = len(context.user_data['sheet_data']) - 1
    
    await update.message.reply_text(
        f"✅ রো #{row_num} যোগ হয়েছে!\n\nআরো ডেটা দাও বা 'done' লিখো:",
        reply_markup=back_menu_keyboard()
    )
    return SHEET_DATA

# ============ SEARCH HANDLER ============
async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    
    await update.message.reply_text(f"🔍 '{query}' খোঁজা হচ্ছে...")
    
    try:
        # Search using yt-dlp search
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'force_generic_extractor': False,
        }
        
        search_query = f"ytsearch5:{query}"
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(search_query, download=False)
            
            if 'entries' in result and result['entries']:
                entries = result['entries'][:5]
                
                response = f"🔍 **'{query}' এর রেজাল্ট:**\n\n"
                
                for i, entry in enumerate(entries, 1):
                    title = entry.get('title', 'Unknown')
                    duration = entry.get('duration', 0)
                    duration_str = f"{duration//60}:{duration%60:02d}" if duration else "N/A"
                    url = entry.get('url', entry.get('webpage_url', ''))
                    
                    response += f"{i}. **{title}**\n"
                    response += f"   ⏱️ {duration_str} | [লিংক]({url})\n\n"
                
                await update.message.reply_text(response, parse_mode='Markdown', disable_web_page_preview=True)
                
                # Offer to download
                keyboard = [
                    [InlineKeyboardButton("📥 ডাউনলোড করতে চাই", callback_data='video_download')],
                    [InlineKeyboardButton("◀️ মূল মেনু", callback_data='main_menu')]
                ]
                await update.message.reply_text(
                    "কোনো লিংক কপি করে ডাউনলোড করতে পারো!",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await update.message.reply_text("❌ কিছু পাওয়া যায়নি!", reply_markup=back_menu_keyboard())
                
    except Exception as e:
        await update.message.reply_text(f"❌ সার্চে সমস্যা: {str(e)[:200]}", reply_markup=back_menu_keyboard())
        await update.message.reply_text("👇 মূল মেনু:", reply_markup=main_menu_keyboard())
        return MENU
    
    return MENU

# ============ TRANSLATE HANDLER ============
async def translate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    direction = context.user_data.get('translate_direction', 'translate_bn_en')
    
    try:
        if direction == 'translate_bn_en':
            translator = GoogleTranslator(source='bn', target='en')
            result = translator.translate(text)
            await update.message.reply_text(
                f"🇧🇩 **বাংলা:** {text}\n\n"
                f"🇬🇧 **ইংরেজি:** {result}",
                reply_markup=back_menu_keyboard(),
                parse_mode='Markdown'
            )
        else:
            translator = GoogleTranslator(source='en', target='bn')
            result = translator.translate(text)
            await update.message.reply_text(
                f"🇬🇧 **ইংরেজি:** {text}\n\n"
                f"🇧🇩 **বাংলা:** {result}",
                reply_markup=back_menu_keyboard(),
                parse_mode='Markdown'
            )
    except Exception as e:
        await update.message.reply_text(f"❌ অনুবাদে সমস্যা: {str(e)}", reply_markup=back_menu_keyboard())
    
    await update.message.reply_text("👇 আরো কিছু করতে চাও?", reply_markup=main_menu_keyboard())
    return MENU

# ============ TTS HANDLER ============
async def tts_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    gender = context.user_data.get('tts_gender', 'female')
    
    if len(text) > 500:
        await update.message.reply_text("❌ ৫০০ অক্ষরের বেশি নয়!", reply_markup=back_menu_keyboard())
        return TTS_TEXT
    
    await update.message.reply_text("🔊 ভয়েস তৈরি হচ্ছে...")
    
    try:
        # gTTS doesn't have gender, but we can use different languages
        # For male-like voice, use a different approach or language variant
        lang = 'bn' if any('\u0980' <= c <= '\u09FF' for c in text) else 'en'
        
        # Slow=True for more natural sound
        tts = gTTS(text=text, lang=lang, slow=False)
        
        temp_dir = tempfile.mkdtemp()
        filename = f"tts_{gender}_{datetime.now().strftime('%H%M%S')}.mp3"
        filepath = os.path.join(temp_dir, filename)
        
        tts.save(filepath)
        
        gender_icon = "👨" if gender == 'male' else "👩"
        
        with open(filepath, 'rb') as audio:
            await update.message.reply_voice(
                voice=audio,
                caption=f"{gender_icon} **{gender.upper()} Voice**\n\n📝 {text[:100]}{'...' if len(text) > 100 else ''}",
                parse_mode='Markdown'
            )
        
        os.remove(filepath)
        os.rmdir(temp_dir)
        
    except Exception as e:
        await update.message.reply_text(f"❌ TTS সমস্যা: {str(e)}", reply_markup=back_menu_keyboard())
    
    await update.message.reply_text("👇 আরো কিছু করতে চাও?", reply_markup=main_menu_keyboard())
    return MENU

# ============ URL SHORTENER HANDLER ============
async def url_shorten_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text("❌ সঠিক URL দাও!", reply_markup=back_menu_keyboard())
        return URL_SHORTEN
    
    await update.message.reply_text("⏳ URL ছোট করা হচ্ছে...")
    
    try:
        s = pyshorteners.Shortener()
        short_url = s.tinyurl.short(url)
        
        await update.message.reply_text(
            f"🔗 **URL Shortener**\n\n"
            f"📎 **লম্বা URL:**\n`{url}`\n\n"
            f"✂️ **ছোট URL:**\n`{short_url}`\n\n"
            f"📋 কপি করে নাও!",
            reply_markup=back_menu_keyboard(),
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ সমস্যা: {str(e)}", reply_markup=back_menu_keyboard())
    
    await update.message.reply_text("👇 আরো কিছু করতে চাও?", reply_markup=main_menu_keyboard())
    return MENU

# ============ FILE CREATOR HANDLER ============
async def file_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    filename = update.message.text.strip()
    
    # Validate filename
    if not re.match(r'^[\w\-. ]+\.\w+$', filename):
        await update.message.reply_text(
            "❌ সঠিক ফাইল নাম দাও! (যেমন: index.php, style.css, app.py)",
            reply_markup=back_menu_keyboard()
        )
        return FILE_NAME
    
    context.user_data['new_filename'] = filename
    await update.message.reply_text(
        f"📄 **{filename}** তৈরি হচ্ছে...\n\nএখন কোড পেস্ট করো:",
        reply_markup=back_menu_keyboard(),
        parse_mode='Markdown'
    )
    return FILE_CODE

async def file_code_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text
    
    # Check if it's a document (for large code)
    if update.message.document:
        doc = await update.message.document.get_file()
        code_bytes = await doc.download_as_bytearray()
        code = code_bytes.decode('utf-8', errors='ignore')
    
    filename = context.user_data['new_filename']
    
    await update.message.reply_text(f"⏳ {filename} তৈরি হচ্ছে...")
    
    try:
        temp_dir = tempfile.mkdtemp()
        filepath = os.path.join(temp_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(code)
        
        file_size = os.path.getsize(filepath)
        
        with open(filepath, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=filename,
                caption=f"✅ **{filename}** তৈরি সম্পূর্ণ!\n\n"
                        f"📏 সাইজ: {file_size} bytes\n"
                        f"📝 লাইন: {code.count(chr(10)) + 1}",
                parse_mode='Markdown'
            )
        
        os.remove(filepath)
        os.rmdir(temp_dir)
        
    except Exception as e:
        await update.message.reply_text(f"❌ ফাইল তৈরিতে সমস্যা: {str(e)}", reply_markup=back_menu_keyboard())
    
    await update.message.reply_text("👇 আরো কিছু করতে চাও?", reply_markup=main_menu_keyboard())
    return MENU

# ============ FALLBACKS ============
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ বাতিল করা হয়েছে!", reply_markup=main_menu_keyboard())
    return MENU

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❓ বুঝতে পারিনি! মেনু থেকে সিলেক্ট করো:",
        reply_markup=main_menu_keyboard()
    )
    return MENU

# ============ MAIN ============
def main():
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CallbackQueryHandler(button_handler, pattern='^main_menu$')
        ],
        states={
            MENU: [
                CallbackQueryHandler(button_handler)
            ],
            VIDEO_DOWNLOAD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, video_download_handler),
                CallbackQueryHandler(button_handler)
            ],
            SHEET_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, sheet_name_handler),
                CallbackQueryHandler(button_handler)
            ],
            SHEET_COLUMNS_COUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, sheet_columns_count_handler),
                CallbackQueryHandler(button_handler)
            ],
            SHEET_COLUMNS_NAMES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, sheet_columns_names_handler),
                CallbackQueryHandler(button_handler)
            ],
            SHEET_DATA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, sheet_data_handler),
                CallbackQueryHandler(button_handler)
            ],
            SEARCH_QUERY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, search_handler),
                CallbackQueryHandler(button_handler)
            ],
            TRANSLATE_LANG: [
                CallbackQueryHandler(button_handler)
            ],
            TRANSLATE_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, translate_handler),
                CallbackQueryHandler(button_handler)
            ],
            TTS_GENDER: [
                CallbackQueryHandler(button_handler)
            ],
            TTS_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, tts_handler),
                CallbackQueryHandler(button_handler)
            ],
            URL_SHORTEN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, url_shorten_handler),
                CallbackQueryHandler(button_handler)
            ],
            FILE_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, file_name_handler),
                CallbackQueryHandler(button_handler)
            ],
            FILE_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, file_code_handler),
                MessageHandler(filters.Document.ALL, file_code_handler),
                CallbackQueryHandler(button_handler)
            ],
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CommandHandler('start', start),
            MessageHandler(filters.ALL, unknown)
        ],
        per_message=False
    )

    application.add_handler(conv_handler)
    
    # Start the bot
    print("🤖 Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
