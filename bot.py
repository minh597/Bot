import re
import unicodedata
import discord
from discord.ext import commands
from collections import Counter
import requests

# ==============================
# CẤU HÌNH BOT
# ==============================
BOT_TOKEN = "MTQ3ODMxMjY3MTQ0NjE3NTg1Nw.GwwSvu.mp97ZQEVFUeAazb7d502YPxpysq7MpJUS1QHe0"

DICT_URLS = [
    "https://raw.githubusercontent.com/duyetdev/vietnamese-wordlist/master/Viet74K.txt",
    "https://raw.githubusercontent.com/duyetdev/vietnamese-wordlist/master/Viet39K.txt",
    "https://raw.githubusercontent.com/stopwords-iso/stopwords-vi/master/stopwords-vi.txt",
]

def normalize(text):
    return unicodedata.normalize("NFC", text.strip().lower())

# ==============================
# TẢI TỪ ĐIỂN
# ==============================
print("Đang tải từ điển...")
dictionary = set()
for url in DICT_URLS:
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            count_before = len(dictionary)
            for w in r.text.split("\n"):
                w = normalize(w)
                if w:
                    dictionary.add(w)
            print(f"✅ {url.split('/')[-1]}: +{len(dictionary) - count_before} từ")
        else:
            print(f"⚠️ Lỗi HTTP {r.status_code}: {url}")
    except Exception as e:
        print(f"⚠️ Không tải được {url}: {e}")

print(f"Tổng từ điển: {len(dictionary)} từ.")

# ==============================
# SETUP BOT
# ==============================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ==============================
# TÌM 1 TỪ 2 TIẾNG (ưu tiên)
# ==============================
def find_one_word(letters):
    total = Counter(letters)
    results = []
    for word in dictionary:
        if word.count(" ") != 1:
            continue
        if Counter(word.replace(" ", "")) == total:
            results.append(word)
    return sorted(results)

# ==============================
# TÌM 2 TỪ GHÉP (fallback)
# ==============================
def find_two_words(letters):
    total = Counter(letters)
    candidates = []
    for word in dictionary:
        w = word.replace(" ", "")
        if len(w) >= len(letters):
            continue
        if not (Counter(w) - total):
            candidates.append(word)

    results = set()
    for w1 in candidates:
        c1 = Counter(w1.replace(" ", ""))
        remain = total - c1
        for w2 in candidates:
            if Counter(w2.replace(" ", "")) == remain:
                if w1 <= w2:
                    results.add(f"{w1} {w2}")
    return sorted(results)

# ==============================
# HÀM CHÍNH: ưu tiên 1 từ, fallback 2 từ
# ==============================
def find_words(letters_raw):
    letters = normalize(letters_raw.replace("/", "").replace(" ", ""))
    found = find_one_word(letters)
    if found:
        return found
    return find_two_words(letters)

# ==============================
# HÀM GOM TEXT TỪ MESSAGE (content + embed)
# ==============================
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

# ==============================
# SỰ KIỆN: BOT SẴN SÀNG
# ==============================
@bot.event
async def on_ready():
    print(f"✅ Bot đã online: {bot.user}")

# ==============================
# SỰ KIỆN: ĐỌC TIN NHẮN (KỂ CẢ BOT KHÁC + EMBED)
# ==============================
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

# ==============================
# LỆNH THỦ CÔNG: !tim <bộ chữ>
# ==============================
@bot.command(name="tim")
async def tim_chu(ctx, *, letters_raw: str):
    found = find_words(letters_raw)
    if found:
        for w in found:
            await ctx.send(w)
    else:
        await ctx.send("không có")

# ==============================
# CHẠY BOT
# ==============================
bot.run(BOT_TOKEN)
