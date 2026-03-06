import os
import re
import unicodedata
import discord
from discord.ext import commands
from collections import Counter
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")

DICT_URLS = [
    "https://raw.githubusercontent.com/duyetdev/vietnamese-wordlist/master/Viet74K.txt",
    "https://raw.githubusercontent.com/duyetdev/vietnamese-wordlist/master/Viet39K.txt",
    "https://raw.githubusercontent.com/stopwords-iso/stopwords-vi/master/stopwords-vi.txt",
]

def normalize(text):
    return unicodedata.normalize("NFC", text.strip().lower())

dictionary = set()
for url in DICT_URLS:
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            for w in r.text.split("\n"):
                w = normalize(w)
                if w:
                    dictionary.add(w)
    except:
        pass

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

letters_index = {}
for word in dictionary:
    key = "".join(sorted(word.replace(" ", "")))
    letters_index.setdefault(key, []).append(word)

def find_one_word(letters):
    key = "".join(sorted(letters))
    return letters_index.get(key, [])

def find_two_words(letters):
    total = Counter(letters)
    words = list(dictionary)
    results = set()
    for w1 in words:
        c1 = Counter(w1.replace(" ", ""))
        if c1 - total:
            continue
        remain = total - c1
        for w2 in words:
            if Counter(w2.replace(" ", "")) == remain:
                if w1 <= w2:
                    results.add(f"{w1} {w2}")
    return sorted(results)

def find_words(letters_raw):
    letters = normalize(letters_raw.replace("/", "").replace(" ", ""))
    found = find_one_word(letters)
    if found:
        return found
    return find_two_words(letters)

def extract_text(message):
    parts = [message.content or ""]
    for embed in message.embeds:
        if embed.title:
            parts.append(embed.title)
        if embed.description:
            parts.append(embed.description)
        for field in embed.fields:
            if field.name:
                parts.append(field.name)
            if field.value:
                parts.append(field.value)
        if embed.footer and embed.footer.text:
            parts.append(embed.footer.text)
    return "\n".join(parts)

@bot.event
async def on_ready():
    print(bot.user)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    full_text = extract_text(message)
    match = re.search(r"Từ cần đoán: \*\*(.*?)\*\* \(gồm \d+ ký tự\)", full_text)
    if match:
        letters_raw = match.group(1)
        found = find_words(letters_raw)
        if found:
            for w in found:
                await message.channel.send(f"`{w}`")
        else:
            await message.channel.send("không có")
    await bot.process_commands(message)

@bot.command(name="tim")
async def tim_chu(ctx, *, letters_raw: str):
    found = find_words(letters_raw)
    if found:
        for w in found:
            await ctx.send(w)
    else:
        await ctx.send("không có")

bot.run(BOT_TOKEN)
