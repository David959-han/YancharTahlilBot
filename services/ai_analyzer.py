import re
import httpx
from config import OPENROUTER_API_KEY

_VALID_TAGS = {"b", "i", "u", "s", "code", "pre", "a"}

def _sanitize(text: str) -> str:
    """Telegram qo'llab-quvvatlamaydigan HTML teglarni olib tashlaydi."""
    def fix(m):
        tag = m.group(1).lstrip("/").split()[0].lower()
        return m.group(0) if tag in _VALID_TAGS else ""
    return re.sub(r"<(/?[a-zA-Z][a-zA-Z0-9]*)(?:\s[^>]*)?>", fix, text)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

_FREE_MODELS = [
    "google/gemma-4-27b-it:free",
    "google/gemma-4-26b-a4b-it:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "liquid/lfm-2.5-1.2b-instruct:free",
]


def _build_prompt(coin_data: dict) -> str:
    return f"""Sen 10 yillik tajribaga ega kripto treydersan. Do'sting senden {coin_data['name']} ({coin_data['symbol']}) haqida maslahat so'rayapti.

Ma'lumotlar:
Narx: {coin_data.get('current_price_fmt', '')}
1 soat: {coin_data.get('change_1h', 'N/A')} | 24 soat: {coin_data.get('change_24h', 'N/A')} | 7 kun: {coin_data.get('change_7d', 'N/A')}
24s yuqori: {coin_data.get('high_24h_fmt', '')} | 24s past: {coin_data.get('low_24h_fmt', '')}
Hajm: {coin_data.get('volume_fmt', '')} | ATH dan: {coin_data.get('ath_change', 'N/A')}

O'ZBEK tilida yoz. Telegram HTML formatidan foydalanasan (<b>qalin</b> uchun).

Quyidagi ANIQ FORMAT bo'yicha yoz:

📊 <b>Holat:</b> [1-2 jumla: hozir narx qanday harakatda, muhim raqamlarga tayanib ayt]

Keyin ma'lumotlarga qarab faqat BITTA signal tanlaysan:

Agar sotib olish imkoni bo'lsa:
📗 <b>Sotib olishni o'ylab ko'ring.</b>
<b>Sababi:</b> [aniq raqamlarga asoslanib tushuntiр: masalan, narx 7 kunda necha foiz o'zgardi, 24s pastdan qancha uzoqlashdi, hajm qanday — 2-3 aniq sabab]

Agar sotish kerak bo'lsa:
📕 <b>Sotishni o'ylab ko'ring.</b>
<b>Sababi:</b> [aniq raqamlarga asoslanib tushuntiр: masalan, narx 24 soatda necha foiz tushdi, 24s yuqoridan qancha pastladi, trend qanday — 2-3 aniq sabab]

Agar kutish kerak bo'lsa:
🟡 <b>Hozircha kutib turing.</b>
<b>Sababi:</b> [aniq raqamlarga asoslanib tushuntiр: masalan, narx 24s yuqori va pastining o'rtasida turibdi, 1 soatlik harakat kichik, yo'nalish noaniq — 2-3 aniq sabab]

Javob oxirida ALBATTA:
⚠️ <i>Men sun'iy intellektman, xato qilish ehtimolim bor. Yakuniy qaror doim sizning o'zingizda qoladi.</i>"""


def _rule_based_analysis(coin_data: dict) -> str:
    """OpenRouter kaliti bo'lmasa ishlaydigan oddiy tahlil."""
    name = coin_data.get("name", "")
    symbol = coin_data.get("symbol", "")

    def pct(key):
        val = coin_data.get(key, "N/A")
        if val == "N/A":
            return 0.0
        try:
            return float(str(val).replace("📈", "").replace("📉", "").replace("%", "").replace("+", "").strip())
        except Exception:
            return 0.0

    h1 = pct("change_1h")
    h24 = pct("change_24h")
    d7 = pct("change_7d")

    if h24 >= 5:
        holat = f"{name} kuchli o'sishda — 24 soatda {coin_data.get('change_24h')} ko'tarildi."
    elif h24 >= 1:
        holat = f"{name} mo''tadil o'sishda — 24 soatda {coin_data.get('change_24h')} yuqoriga harakat qilmoqda."
    elif h24 <= -5:
        holat = f"{name} kuchli tushishda — 24 soatda {coin_data.get('change_24h')} pasaydi."
    elif h24 <= -1:
        holat = f"{name} tushish tendensiyasida — 24 soatda {coin_data.get('change_24h')} pasaydi."
    else:
        holat = f"{name} barqaror holda — 24 soatda o'zgarish minimal ({coin_data.get('change_24h')})."

    if d7 > 0 and h24 > 0:
        kuch = "Haftalik va kunlik trend bir xil yo'nalishda — bullish signal kuchli."
    elif d7 < 0 and h24 < 0:
        kuch = "Haftalik va kunlik trend pasayishda — bearish bosim davom etmoqda."
    elif d7 > 0 and h24 < 0:
        kuch = "Haftalik trend yuqoriga, lekin kunlik tushish kuzatilmoqda — ehtiyot bo'lish kerak."
    else:
        kuch = "Aralash signallar — bozor yo'nalishi noaniq."

    if h24 >= 3 and h1 >= 0:
        signal = "📗 SOTIB OL"
    elif h24 <= -3 and h1 <= 0:
        signal = "📕 SOT"
    else:
        signal = "🟡 KUTING"

    ath = coin_data.get("ath_change", "")
    ath_text = f"ATH dan {ath} pastda." if ath else ""

    return f"{holat}\n{kuch} {ath_text}\n\nSignal: {signal}"


async def analyze_coin(coin_data: dict) -> str:
    if not OPENROUTER_API_KEY:
        return _rule_based_analysis(coin_data)

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "messages": [{"role": "user", "content": _build_prompt(coin_data)}],
        "max_tokens": 400,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            for model in _FREE_MODELS:
                body["model"] = model
                resp = await client.post(OPENROUTER_URL, json=body, headers=headers)
                if resp.status_code == 200:
                    raw = resp.json()["choices"][0]["message"]["content"].strip()
                    return _sanitize(raw)
    except Exception:
        pass

    return _rule_based_analysis(coin_data)
