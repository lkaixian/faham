"""User-facing scam-check sentences in bm, en, zh, ta, keyed by a stable code.

English is the source of truth. {placeholders}: d = domain, issuer = agency key,
site = official website, who = agency name. Every code must have all four
languages with the same placeholders (tests enforce it).
zh and ta wording needs native-speaker review before the demo.
"""
from __future__ import annotations

LANGS = ("bm", "en", "zh", "ta")

TEXT: dict[str, dict[str, str]] = {
    # ---- red flags
    "transfer_account": {
        "en": "Asks you to transfer money to a personal or company account",
        "bm": "Meminta anda pindahkan wang ke akaun peribadi atau akaun syarikat",
        "zh": "要求你把钱转到私人或公司户口",
        "ta": "தனிநபர் அல்லது நிறுவனக் கணக்கிற்குப் பணம் அனுப்பச் சொல்கிறது",
    },
    "urgency": {
        "en": "Creates fake urgency",
        "bm": "Mencipta rasa tergesa-gesa yang palsu",
        "zh": "制造虚假的紧迫感",
        "ta": "பொய்யான அவசரத்தை உருவாக்குகிறது",
    },
    "arrest": {
        "en": "Threatens arrest",
        "bm": "Mengugut akan menangkap anda",
        "zh": "以逮捕来威胁",
        "ta": "கைது செய்வோம் என்று மிரட்டுகிறது",
    },
    "tac_otp": {
        "en": "Asks for a TAC, OTP or password",
        "bm": "Meminta TAC, OTP atau kata laluan",
        "zh": "索取 TAC、OTP 或密码",
        "ta": "TAC, OTP அல்லது கடவுச்சொல்லைக் கேட்கிறது",
    },
    "chat_app": {
        "en": "Moves you to a chat app",
        "bm": "Mengajak anda berbual di aplikasi sembang",
        "zh": "引导你转到聊天应用程序",
        "ta": "உங்களை அரட்டைச் செயலிக்கு மாற்றுகிறது",
    },
    "secret": {
        "en": "Asks you to keep it secret",
        "bm": "Meminta anda merahsiakannya",
        "zh": "要求你保密",
        "ta": "இதை ரகசியமாக வைத்திருக்கச் சொல்கிறது",
    },
    "ic_photo": {
        "en": "Asks for photos of your IC",
        "bm": "Meminta gambar kad pengenalan anda",
        "zh": "索取你的身份证照片",
        "ta": "உங்கள் அடையாள அட்டையின் படங்களைக் கேட்கிறது",
    },
    "discount": {
        "en": "Offers an unusual discount",
        "bm": "Menawarkan diskaun yang pelik",
        "zh": "提供不寻常的折扣",
        "ta": "வழக்கத்துக்கு மாறான தள்ளுபடி தருவதாகச் சொல்கிறது",
    },
    "new_account": {
        "en": "Says to pay into a new or changed account",
        "bm": "Menyuruh anda bayar ke akaun baharu atau akaun yang telah ditukar",
        "zh": "叫你付款到新的或已更改的户口",
        "ta": "புதிய அல்லது மாற்றப்பட்ட கணக்கில் பணம் செலுத்தச் சொல்கிறது",
    },
    "hidden_link": {
        "en": "Link uses an '@' or an IP address to hide where it really goes",
        "bm": "Pautan guna '@' atau alamat IP untuk sembunyikan tujuan sebenar",
        "zh": "链接用 '@' 或 IP 地址来隐藏真正的去处",
        "ta": "இணைப்பு உண்மையான இடத்தை மறைக்க '@' அல்லது IP முகவரியைப் பயன்படுத்துகிறது",
    },
    "credential_harvest": {
        "en": "Wants you to 'verify' your account or details",
        "bm": "Mahu anda 'sahkan' akaun atau maklumat anda",
        "zh": "要你“验证”户口或个人资料",
        "ta": "உங்கள் கணக்கு அல்லது விவரங்களை 'சரிபார்க்க' சொல்கிறது",
    },
    "shortener": {
        "en": "Shortened link ({d}) instead of an official site",
        "bm": "Pautan pendek ({d}) dan bukan laman web rasmi",
        "zh": "使用短链接（{d}），不是官方网站",
        "ta": "அதிகாரப்பூர்வ இணையதளத்துக்குப் பதிலாக சுருக்கிய இணைப்பு ({d})",
    },
    "social_links": {
        "en": "Social media links appear. Check they are the agency's real accounts from its own website",
        "bm": "Terdapat pautan media sosial. Semak ia akaun sebenar agensi daripada laman web rasminya",
        "zh": "信中有社交媒体链接。请到该机构官方网站核对这些是否为其真实账号",
        "ta": "சமூக ஊடக இணைப்புகள் உள்ளன. அவை நிறுவனத்தின் உண்மையான கணக்குகளா என அதன் அதிகாரப்பூர்வ இணையதளத்தில் சரிபார்க்கவும்",
    },
    "official_social": {
        "en": "Social account {d} is on our list of this agency's official accounts",
        "bm": "Akaun sosial {d} ada dalam senarai akaun rasmi agensi ini",
        "zh": "社交账号 {d} 在我们的该机构官方账号名单中",
        "ta": "சமூக ஊடகக் கணக்கு {d} இந்த நிறுவனத்தின் அதிகாரப்பூர்வ கணக்குகளின் பட்டியலில் உள்ளது",
    },
    "social_mismatch": {
        "en": "Social account {d} is NOT on our list of this agency's official accounts",
        "bm": "Akaun sosial {d} TIADA dalam senarai akaun rasmi agensi ini",
        "zh": "社交账号 {d} 不在我们的该机构官方账号名单中",
        "ta": "சமூக ஊடகக் கணக்கு {d} இந்த நிறுவனத்தின் அதிகாரப்பூர்வ கணக்குகளின் பட்டியலில் இல்லை",
    },
    "form_link": {
        "en": "Asks you to fill an online form ({d}). Confirm the survey is listed on the agency's own website before entering personal details",
        "bm": "Meminta anda mengisi borang dalam talian ({d}). Sahkan kaji selidik itu ada di laman web rasmi agensi sebelum mengisi butiran peribadi",
        "zh": "要求您填写在线表格（{d}）。填写个人资料前，请先在该机构官方网站确认有此调查",
        "ta": "இணையப் படிவத்தை ({d}) நிரப்பக் கேட்கிறது. தனிப்பட்ட விவரங்களை உள்ளிடும் முன் அந்த ஆய்வு நிறுவனத்தின் இணையதளத்தில் உள்ளதா என உறுதிசெய்யவும்",
    },
    "unofficial_domain": {
        "en": "Unofficial domain {d}",
        "bm": "Domain tidak rasmi {d}",
        "zh": "非官方域名 {d}",
        "ta": "அதிகாரப்பூர்வமற்ற டொமைன் {d}",
    },
    "lookalike": {
        "en": "Looks like an official site but is not ({d})",
        "bm": "Nampak seperti laman web rasmi tetapi bukan ({d})",
        "zh": "看起来像官方网站，但不是（{d}）",
        "ta": "அதிகாரப்பூர்வ இணையதளம் போலத் தெரிகிறது, ஆனால் இல்லை ({d})",
    },
    # ---- good signs
    "official_domain": {
        "en": "Link text shows an official domain {d} (check the real destination yourself)",
        "bm": "Teks pautan menunjukkan domain rasmi {d} (semak sendiri tujuan sebenar pautan)",
        "zh": "链接文字显示官方域名 {d}（请自行查看链接真正的去处）",
        "ta": "இணைப்பு உரை அதிகாரப்பூர்வ டொமைன் {d} எனக் காட்டுகிறது (உண்மையான இடத்தை நீங்களே சரிபார்க்கவும்)",
    },
    "known_pattern": {
        "en": "Wording matches typical {issuer} letters (scammers copy this too)",
        "bm": "Bahasa sepadan dengan surat {issuer} biasa (penipu pun boleh meniru ini)",
        "zh": "措辞与一般的 {issuer} 信件相符（骗子也会模仿）",
        "ta": "சொற்கள் வழக்கமான {issuer} கடிதங்களுடன் பொருந்துகின்றன (மோசடிக்காரர்களும் இதை நகலெடுக்கிறார்கள்)",
    },
    "ref_format": {
        "en": "Reference number in an official-looking format",
        "bm": "Nombor rujukan dalam format yang kelihatan rasmi",
        "zh": "参考编号的格式看起来像官方的",
        "ta": "குறிப்பு எண் அதிகாரப்பூர்வம் போன்ற வடிவில் உள்ளது",
    },
    # ---- info
    "cannot_see": {
        "en": "We only read the text you gave us. We cannot see who really sent it, the real link behind a button, or the email headers.",
        "bm": "Kami hanya baca teks yang anda beri. Kami tidak dapat lihat siapa penghantar sebenar, pautan sebenar di sebalik butang, atau pengepala e-mel.",
        "zh": "我们只读了你给的文字。我们看不到真正的发送者、按钮背后的真实链接，也看不到电邮标头。",
        "ta": "நீங்கள் தந்த உரையை மட்டுமே நாங்கள் படித்தோம். உண்மையில் யார் அனுப்பினார், பொத்தானுக்குப் பின்னால் உள்ள உண்மையான இணைப்பு, மின்னஞ்சல் தலைப்புகள் ஆகியவற்றை எங்களால் பார்க்க முடியாது.",
    },
    "pay_confirmed": {
        "en": "Pay only to an account you have confirmed on the agency's own website or by phone.",
        "bm": "Bayar hanya ke akaun yang anda sudah sahkan di laman web rasmi agensi atau melalui telefon.",
        "zh": "只能付款到你已在机构官方网站上或通过电话确认过的户口。",
        "ta": "நிறுவனத்தின் அதிகாரப்பூர்வ இணையதளத்தில் அல்லது தொலைபேசியில் உறுதிசெய்த கணக்கிற்கு மட்டுமே பணம் செலுத்துங்கள்.",
    },
    # ---- verify yourself
    "type_url": {
        "en": "Type the website address yourself ({site}). Do not click links in the message.",
        "bm": "Taip sendiri alamat laman web ({site}). Jangan klik pautan dalam mesej.",
        "zh": "请自己输入网址（{site}）。不要点击信息里的链接。",
        "ta": "இணையதள முகவரியை நீங்களே தட்டச்சு செய்யுங்கள் ({site}). செய்தியில் உள்ள இணைப்புகளைக் கிளிக் செய்யாதீர்கள்.",
    },
    "call_official": {
        "en": "Find the phone number on {who}'s official site and call it to ask about this letter.",
        "bm": "Cari nombor telefon di laman web rasmi {who} dan telefon untuk bertanya tentang surat ini.",
        "zh": "在 {who} 的官方网站找电话号码，打电话询问这封信。",
        "ta": "{who} அதிகாரப்பூர்வ இணையதளத்தில் தொலைபேசி எண்ணைக் கண்டுபிடித்து, இந்தக் கடிதம் பற்றிக் கேளுங்கள்.",
    },
    "check_ref": {
        "en": "Check the reference number on that site or in the official app (for example MyTax or MyJPJ).",
        "bm": "Semak nombor rujukan di laman web itu atau dalam aplikasi rasmi (contohnya MyTax atau MyJPJ).",
        "zh": "在那个网站或官方应用程序（例如 MyTax 或 MyJPJ）核对参考编号。",
        "ta": "அந்த இணையதளத்தில் அல்லது அதிகாரப்பூர்வ செயலியில் (எ.கா. MyTax அல்லது MyJPJ) குறிப்பு எண்ணைச் சரிபாருங்கள்.",
    },
    "no_pay_tac": {
        "en": "Do not pay or share any TAC/OTP until you have done these steps.",
        "bm": "Jangan bayar atau kongsi TAC/OTP sehingga anda selesai langkah-langkah ini.",
        "zh": "完成这些步骤之前，不要付款，也不要透露任何 TAC/OTP。",
        "ta": "இந்தப் படிகளைச் செய்து முடிக்கும் வரை பணம் செலுத்தவோ TAC/OTP பகிரவோ வேண்டாம்.",
    },
    # ---- email signals (from ingest.py)
    "mail_spf_fail": {
        "en": "The email failed its sender checks (SPF, DKIM or DMARC), so the sender may be faked",
        "bm": "Emel ini gagal semakan penghantar (SPF, DKIM atau DMARC), jadi penghantar mungkin palsu",
        "zh": "这封电邮没有通过发件人验证（SPF、DKIM 或 DMARC），发件人可能是假冒的",
        "ta": "இந்த மின்னஞ்சல் அனுப்புநர் சோதனையில் (SPF, DKIM அல்லது DMARC) தோல்வியடைந்தது, அனுப்புநர் போலியாக இருக்கலாம்",
    },
    "mail_replyto_mismatch": {
        "en": "Replies go to a different address than the sender",
        "bm": "Balasan akan dihantar ke alamat lain, bukan alamat penghantar",
        "zh": "回复会被发送到与发件人不同的地址",
        "ta": "பதில்கள் அனுப்புநரின் முகவரிக்குப் பதிலாக வேறு முகவரிக்குச் செல்லும்",
    },
    "mail_link_mismatch": {
        "en": "A link shows one website but opens a different one",
        "bm": "Satu pautan menunjukkan satu laman web tetapi membuka laman lain",
        "zh": "链接显示的是一个网站，实际打开的却是另一个网站",
        "ta": "ஒரு இணைப்பு ஒரு இணையதளத்தைக் காட்டுகிறது, ஆனால் வேறொன்றைத் திறக்கிறது",
    },
    "mail_display_spoof": {
        "en": "The sender name shows a different website than the real sender address",
        "bm": "Nama penghantar menunjukkan laman web yang berbeza daripada alamat sebenar penghantar",
        "zh": "发件人名称显示的网站与真实发件地址不同",
        "ta": "அனுப்புநர் பெயர் உண்மையான முகவரியிலிருந்து வேறுபட்ட இணையதளத்தைக் காட்டுகிறது",
    },
    # ---- fallback agency name
    "the_agency": {
        "en": "the agency",
        "bm": "agensi",
        "zh": "该机构",
        "ta": "நிறுவனம்",
    },
}


def render(code: str, language: str = "en", **kw: str) -> str:
    """Sentence for `code` in `language` (falls back to English)."""
    return TEXT[code].get(language, TEXT[code]["en"]).format(**kw)
