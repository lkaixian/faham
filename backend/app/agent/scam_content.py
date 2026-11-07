"""Scam types and the lesson, route and draft text for each, in bm, en, zh, ta.

`detect_scam_type` is rules only. The lesson, route and draft must match the type: a fake LHDN refund
must never get police-summons steps, and a message from no agency never gets an agency letter template.
zh and ta wording needs native-speaker review before the demo.
"""
from __future__ import annotations

import re

SCAM_TYPES = ("macau", "family_impersonation", "parcel", "job", "love", "investment",
              "phishing_refund", "apk_install", "other")

_RULES: list[tuple[str, str]] = [
    ("family_impersonation", r"__family__"),  # set by scam_check, not by regex here
    ("apk_install", r"\.apk\b|install\w*\s+(?:app|aplikasi|file|fail)|pasang\s+(?:app|aplikasi)|muat\s*turun\s+(?:app|aplikasi)|download\s+(?:the\s+)?app|安装.{0,8}(?:应用|程序|apk)|下载.{0,8}(?:应用|程序)|ஆப்ஸை\s*நிறுவ"),
    ("macau", r"waran\s+tangkap|ditangkap|arrest|akaun\s+selamat|safe\s+account|pengubahan\s+wang\s+haram|money\s+laundering|bank\s+negara|jsjk|ccid|mahkamah|逮捕|通缉|洗钱|安全(?:账户|户口)|冻结|பாதுகாப்பான\s*கணக்|பணமோசடி|கைது"),
    ("phishing_refund", r"lebihan\s+bayaran|bayaran\s+balik|refund|rebate|tax\s+return|退税|退款|திரும்பப்\s*பெற|பணம்\s*திரும்ப"),
    ("parcel", r"pos\s*laju|poslaju|parcel|bungkusan|kastam|customs|j&t|dhl|ninja\s*van|courier|包裹|快递|海关|பார்சல்|கூரியர்"),
    ("job", r"kerja\s+(?:sambilan|part[- ]?time|dari\s+rumah)|part[- ]?time|work\s+from\s+home|job\s+offer|tugasan|komisen|commission|兼职|招聘|刷单|வேலை\s*வாய்ப்பு|பகுதி\s*நேர"),
    ("investment", r"pelaburan|melabur|invest|forex|crypto|kripto|keuntungan\s+\d+%|guaranteed\s+return|pulangan\s+terjamin|投资|理财|稳赚|முதலீடு"),
    ("love", r"sayang(?:ku)?\b|my\s+dear|darling|my\s+love|soldier|askar\s+amerika|hadiah\s+(?:tersekat|kastam)|亲爱的|宝贝|அன்பே|காதல்"),
]


def detect_scam_type(low: str, family: bool = False) -> str:
    """Most specific type first. `low` is the lowercased redacted text."""
    if family:
        return "family_impersonation"
    for name, pat in _RULES[1:]:
        if re.search(pat, low):
            return name
    return "other"


LESSON_Q = {
    "bm": "Kenapa saya dapat mesej ini?",
    "en": "Why did I get this message?",
    "zh": "我为什么会收到这条信息？",
    "ta": "எனக்கு ஏன் இந்தச் செய்தி வந்தது?",
}
LETTER_Q = {
    "bm": "Kenapa saya dapat surat ini?",
    "en": "Why did I get this letter?",
    "zh": "我为什么会收到这封信？",
    "ta": "எனக்கு ஏன் இந்தக் கடிதம் வந்தது?",
}

LESSON_A: dict[str, dict[str, str]] = {
    "macau": {
        "en": "Real police, courts, LHDN and banks never ask you to move money to a 'safe account' and never phone to arrest you. Scammers use fear and secrecy so you do not ask anyone.",
        "bm": "Polis, mahkamah, LHDN dan bank sebenar tidak pernah suruh anda pindahkan wang ke 'akaun selamat' atau telefon untuk menangkap anda. Penipu guna rasa takut dan rahsia supaya anda tidak bertanya sesiapa.",
        "zh": "真正的警察、法院、LHDN 和银行绝不会叫你把钱转到“安全账户”，也不会打电话说要逮捕你。骗子利用恐惧和保密，让你不去问别人。",
        "ta": "உண்மையான காவல்துறை, நீதிமன்றம், LHDN, வங்கிகள் 'பாதுகாப்பான கணக்கிற்கு' பணம் மாற்றச் சொல்லாது; கைது செய்வதாக அழைக்கவும் செய்யாது. மோசடிக்காரர்கள் பயத்தையும் ரகசியத்தையும் பயன்படுத்துகிறார்கள்.",
    },
    "family_impersonation": {
        "en": "Scammers pretend to be a child or relative with a 'new number' and a quick money problem. They count on you acting before you call the person.",
        "bm": "Penipu berpura-pura jadi anak atau saudara dengan 'nombor baru' dan masalah wang yang segera. Mereka harap anda bertindak sebelum menelefon orang itu.",
        "zh": "骗子假扮子女或亲人，说换了“新号码”并急需用钱。他们希望你在打电话确认之前就先汇款。",
        "ta": "மோசடிக்காரர்கள் 'புதிய எண்' என்று சொல்லிப் பிள்ளை அல்லது உறவினர் போல நடித்து அவசரமாகப் பணம் கேட்பார்கள். நீங்கள் அவரை அழைக்கும் முன் பணம் அனுப்ப வேண்டும் என்று எதிர்பார்க்கிறார்கள்.",
    },
    "parcel": {
        "en": "Fake courier and customs messages ask for a small fee or your details through a link. Real couriers show your parcel in their own app.",
        "bm": "Mesej kurier dan kastam palsu minta bayaran kecil atau maklumat anda melalui pautan. Kurier sebenar tunjuk bungkusan anda dalam aplikasi mereka sendiri.",
        "zh": "假快递和假海关信息会通过链接要你付小额费用或提供资料。真正的快递公司会在自己的应用程序里显示你的包裹。",
        "ta": "போலி கூரியர், சுங்கச் செய்திகள் இணைப்பு மூலம் சிறு கட்டணம் அல்லது உங்கள் விவரங்களைக் கேட்கும். உண்மையான கூரியர் தங்கள் சொந்தச் செயலியில் உங்கள் பார்சலைக் காட்டும்.",
    },
    "job": {
        "en": "Fake job offers promise easy pay for simple tasks, then ask you to 'top up' or pay a deposit. A real employer never makes you pay to work.",
        "bm": "Tawaran kerja palsu janji bayaran mudah untuk tugasan ringkas, kemudian suruh anda 'top up' atau bayar deposit. Majikan sebenar tidak suruh anda bayar untuk bekerja.",
        "zh": "假工作邀请承诺轻松赚钱，然后要你“充值”或付押金。真正的雇主不会要求你先付钱才能工作。",
        "ta": "போலி வேலை வாய்ப்புகள் எளிய பணிகளுக்கு எளிதாகப் பணம் தருவதாகச் சொல்லி, பிறகு 'டாப் அப்' அல்லது வைப்புத் தொகை கேட்கும். உண்மையான முதலாளி வேலைக்குப் பணம் கட்டச் சொல்லமாட்டார்.",
    },
    "love": {
        "en": "Romance scammers build trust over weeks, then invent a crisis or a gift stuck at customs. Anyone you have not met who asks for money is a warning sign.",
        "bm": "Penipu cinta bina kepercayaan berminggu-minggu, kemudian reka krisis atau hadiah tersekat di kastam. Sesiapa yang belum pernah anda jumpa dan minta wang ialah tanda amaran.",
        "zh": "感情骗子会花几个星期建立信任，然后编造危机或礼物被海关扣留。没见过面的人向你要钱，就是警号。",
        "ta": "காதல் மோசடிக்காரர்கள் வாரக்கணக்கில் நம்பிக்கையை வளர்த்து, பின்னர் நெருக்கடி அல்லது சுங்கத்தில் சிக்கிய பரிசு என்று கதை சொல்வார்கள். நேரில் சந்திக்காத ஒருவர் பணம் கேட்டால் அது எச்சரிக்கை.",
    },
    "investment": {
        "en": "No real investment guarantees high returns. Scams show fake profits first so you invest more, then you cannot withdraw.",
        "bm": "Tiada pelaburan sebenar yang jamin pulangan tinggi. Penipuan tunjuk untung palsu dahulu supaya anda melabur lagi, kemudian anda tidak boleh keluarkan wang.",
        "zh": "没有任何真正的投资能保证高回报。骗局先让你看到假盈利，诱你多投，之后就无法提款。",
        "ta": "எந்த உண்மையான முதலீடும் அதிக லாபத்துக்கு உத்தரவாதம் தராது. மோசடிகள் முதலில் போலி லாபத்தைக் காட்டி மேலும் முதலீடு செய்ய வைக்கும்; பிறகு பணம் எடுக்க முடியாது.",
    },
    "phishing_refund": {
        "en": "Scammers promise a refund or rebate so you open a link and enter bank details or a TAC. Real agencies never make you claim a refund through a chat or a link in a message.",
        "bm": "Penipu janji bayaran balik atau rebat supaya anda buka pautan dan masukkan butiran bank atau TAC. Agensi sebenar tidak suruh anda tuntut bayaran balik melalui sembang atau pautan dalam mesej.",
        "zh": "骗子承诺退款或回扣，引你点开链接并输入银行资料或 TAC。真正的机构不会要你通过聊天或信息里的链接领取退款。",
        "ta": "மோசடிக்காரர்கள் பணம் திரும்பக் கிடைக்கும் என்று சொல்லி இணைப்பைத் திறந்து வங்கி விவரம் அல்லது TAC கொடுக்க வைப்பார்கள். உண்மையான அமைப்புகள் செய்தியில் உள்ள இணைப்பு மூலம் பணம் பெறச் சொல்லாது.",
    },
    "apk_install": {
        "en": "An .apk file or 'install this app' link is a common way to take over your phone and read your bank codes. Only install apps from the official Play Store or App Store.",
        "bm": "Fail .apk atau pautan 'pasang aplikasi ini' ialah cara biasa untuk ambil alih telefon dan baca kod bank anda. Pasang aplikasi dari Play Store atau App Store rasmi sahaja.",
        "zh": ".apk 文件或“安装此应用”的链接是接管你手机并读取银行验证码的常见手法。只从官方 Play Store 或 App Store 安装应用。",
        "ta": ".apk கோப்பு அல்லது 'இந்தச் செயலியை நிறுவுங்கள்' இணைப்பு உங்கள் தொலைபேசியைக் கைப்பற்றி வங்கிக் குறியீடுகளைப் படிக்க ஒரு பொதுவான வழி. அதிகாரப்பூர்வ Play Store அல்லது App Store-இல் மட்டும் நிறுவுங்கள்.",
    },
    "other": {
        "en": "Scammers copy official words and add a short deadline so you act before you think or ask someone.",
        "bm": "Penipu tiru perkataan rasmi dan tambah tarikh akhir yang singkat supaya anda bertindak sebelum berfikir atau bertanya.",
        "zh": "骗子模仿官方用语并加上很短的期限，让你来不及思考或询问别人就行动。",
        "ta": "மோசடிக்காரர்கள் அதிகாரப்பூர்வ சொற்களைப் பின்பற்றி குறுகிய கெடுவைச் சேர்ப்பார்கள்; நீங்கள் யோசிக்கும் முன் செயல்பட வேண்டும் என்பதற்காக.",
    },
}

TERMS = ["Waran tangkap", "NSRC 997", "Domain rasmi"]

FIRST_STEP: dict[str, dict[str, str]] = {
    "macau": {
        "en": "Hang up or stop replying. Real police, courts, LHDN and banks never ask you to move money to a 'safe account'.",
        "bm": "Putuskan panggilan atau berhenti membalas. Polis, mahkamah, LHDN dan bank sebenar tidak pernah suruh pindah wang ke 'akaun selamat'.",
        "zh": "挂断电话或不要再回复。真正的警察、法院、LHDN 和银行绝不会叫你把钱转到“安全账户”。",
        "ta": "அழைப்பைத் துண்டிக்கவும் அல்லது பதில் அனுப்பாதீர்கள். உண்மையான காவல்துறை, நீதிமன்றம், LHDN, வங்கிகள் 'பாதுகாப்பான கணக்கிற்கு' பணம் மாற்றச் சொல்லாது.",
    },
    "family_impersonation": {
        "en": "Call your family member on their OLD number first. Do not transfer anything until you hear their voice.",
        "bm": "Telefon ahli keluarga anda pada nombor LAMA mereka dahulu. Jangan pindah wang sehingga anda dengar suara mereka.",
        "zh": "先打他们的旧号码确认。听到本人声音之前，不要转任何钱。",
        "ta": "முதலில் அவர்களின் பழைய எண்ணை அழைக்கவும். அவர்கள் குரலைக் கேட்கும் வரை எதுவும் அனுப்பாதீர்கள்.",
    },
    "parcel": {
        "en": "Check the parcel yourself in the courier's own app or website. Real couriers do not ask for fees through a chat link.",
        "bm": "Semak bungkusan sendiri dalam aplikasi atau laman web kurier. Kurier sebenar tidak minta bayaran melalui pautan sembang.",
        "zh": "自己到快递公司的应用程序或网站查询包裹。真正的快递不会通过聊天链接收费。",
        "ta": "கூரியரின் சொந்தச் செயலி அல்லது இணையதளத்தில் நீங்களே பார்சலைச் சரிபாருங்கள். உண்மையான கூரியர் அரட்டை இணைப்பு மூலம் கட்டணம் கேட்காது.",
    },
    "job": {
        "en": "Do not join the chat group or pay anything. A real job never asks you to pay first or 'top up' for tasks.",
        "bm": "Jangan sertai kumpulan sembang atau bayar apa-apa. Kerja sebenar tidak suruh anda bayar dahulu atau 'top up' untuk tugasan.",
        "zh": "不要加入聊天群，也不要付任何钱。真正的工作不会要你先付钱或为任务“充值”。",
        "ta": "அரட்டைக் குழுவில் சேராதீர்கள், எதுவும் செலுத்தாதீர்கள். உண்மையான வேலை முதலில் பணம் அல்லது 'டாப் அப்' கேட்காது.",
    },
    "love": {
        "en": "Never send money to someone you have not met in person, however close you feel.",
        "bm": "Jangan hantar wang kepada orang yang belum pernah anda jumpa, walau betapa rapat perasaan anda.",
        "zh": "无论感觉多亲近，都不要给没见过面的人汇款。",
        "ta": "நேரில் சந்திக்காத ஒருவருக்கு எவ்வளவு நெருக்கமாக உணர்ந்தாலும் பணம் அனுப்பாதீர்கள்.",
    },
    "investment": {
        "en": "Do not invest. Check the company on the Securities Commission Malaysia Investor Alert List first.",
        "bm": "Jangan melabur. Semak syarikat itu dahulu dalam Senarai Amaran Pelabur Suruhanjaya Sekuriti Malaysia.",
        "zh": "不要投资。先到马来西亚证券委员会的投资者警示名单查询该公司。",
        "ta": "முதலீடு செய்யாதீர்கள். முதலில் மலேசிய பத்திரங்கள் ஆணையத்தின் முதலீட்டாளர் எச்சரிக்கைப் பட்டியலில் நிறுவனத்தைச் சரிபாருங்கள்.",
    },
    "phishing_refund": {
        "en": "Do not open the link. Type the agency's official website yourself. Real refunds are never claimed through a chat or a link.",
        "bm": "Jangan buka pautan. Taip sendiri laman web rasmi agensi. Bayaran balik sebenar tidak dituntut melalui sembang atau pautan.",
        "zh": "不要打开链接。自己输入该机构的官方网站。真正的退款不会通过聊天或链接领取。",
        "ta": "இணைப்பைத் திறக்காதீர்கள். அமைப்பின் அதிகாரப்பூர்வ இணையதளத்தை நீங்களே தட்டச்சு செய்யுங்கள். உண்மையான பணத் திரும்பல் அரட்டை அல்லது இணைப்பு மூலம் பெறப்படுவதில்லை.",
    },
    "apk_install": {
        "en": "Do not install the file. Delete it. Apps from outside the official Play Store or App Store can take over your phone and bank app.",
        "bm": "Jangan pasang fail itu. Padamkannya. Aplikasi dari luar Play Store atau App Store rasmi boleh mengambil alih telefon dan aplikasi bank anda.",
        "zh": "不要安装该文件，直接删除。官方应用商店以外的应用可能接管你的手机和银行应用。",
        "ta": "கோப்பை நிறுவாதீர்கள்; நீக்கிவிடுங்கள். அதிகாரப்பூர்வ கடைக்கு வெளியே உள்ள செயலிகள் உங்கள் தொலைபேசியையும் வங்கிச் செயலியையும் கைப்பற்றலாம்.",
    },
    "other": {
        "en": "Do not click, reply or pay. Check with the agency using a website or number you find yourself.",
        "bm": "Jangan klik, balas atau bayar. Semak dengan agensi menggunakan laman web atau nombor yang anda cari sendiri.",
        "zh": "不要点击、回复或付款。用你自己查到的网站或号码向该机构核实。",
        "ta": "கிளிக் செய்யவோ பதிலளிக்கவோ பணம் செலுத்தவோ வேண்டாம். நீங்களே கண்டுபிடித்த இணையதளம் அல்லது எண் மூலம் அமைப்பிடம் சரிபாருங்கள்.",
    },
}

COMMON_ONLINE: dict[str, list[str]] = {
    "en": ["Check the number or bank account on Semak Mule (semakmule.rmp.gov.my) by typing it yourself.",
           "If you already paid or shared a TAC, call your bank's 24-hour hotline and NSRC 997 now.",
           "Report it: call NSRC 997, or make a police report."],
    "bm": ["Semak nombor atau akaun bank di Semak Mule (semakmule.rmp.gov.my) dengan menaipnya sendiri.",
           "Jika sudah bayar atau kongsi TAC, telefon talian 24 jam bank anda dan NSRC 997 sekarang.",
           "Lapor: telefon NSRC 997, atau buat laporan polis."],
    "zh": ["自己输入号码或银行户口，到 Semak Mule (semakmule.rmp.gov.my) 查询。",
           "如果已经付款或透露了 TAC，请立刻拨打银行 24 小时热线和 NSRC 997。",
           "举报：拨打 NSRC 997，或报警。"],
    "ta": ["எண் அல்லது வங்கிக் கணக்கை நீங்களே தட்டச்சு செய்து Semak Mule (semakmule.rmp.gov.my)-இல் சரிபாருங்கள்.",
           "ஏற்கனவே பணம் செலுத்தியிருந்தால் அல்லது TAC கொடுத்திருந்தால், உடனே உங்கள் வங்கியின் 24 மணி நேரத் தொலைபேசிக்கும் NSRC 997-க்கும் அழையுங்கள்.",
           "புகார்: NSRC 997-ஐ அழைக்கவும் அல்லது காவல் புகார் செய்யவும்."],
}
COMMON_WALKIN: dict[str, list[str]] = {
    "en": ["Go to the nearest police station to make a report. Bring the screenshots, account numbers and any transfer slip."],
    "bm": ["Pergi ke balai polis terdekat untuk membuat laporan. Bawa tangkap layar, nombor akaun dan slip pindahan."],
    "zh": ["到最近的警局报案。带上截图、户口号码和转账单据。"],
    "ta": ["அருகிலுள்ள காவல் நிலையத்தில் புகார் செய்யுங்கள். திரைப்படங்கள், கணக்கு எண்கள், பரிமாற்ற சீட்டைக் கொண்டு செல்லுங்கள்."],
}
PREPARE_ONLINE: dict[str, list[str]] = {
    "en": ["Screenshots of the message", "Sender's phone number or account number", "Transfer receipt (if you paid)"],
    "bm": ["Tangkap layar mesej", "Nombor telefon atau nombor akaun penghantar", "Resit pindahan (jika sudah bayar)"],
    "zh": ["信息截图", "发送者的电话或户口号码", "转账收据（如已付款）"],
    "ta": ["செய்தியின் திரைப்படங்கள்", "அனுப்பியவரின் தொலைபேசி அல்லது கணக்கு எண்", "பரிமாற்ற ரசீது (செலுத்தியிருந்தால்)"],
}
PREPARE_WALKIN: dict[str, list[str]] = {
    "en": ["IC (original)", "Screenshots or a printout of the message", "Transfer receipt (if any)"],
    "bm": ["Kad pengenalan (asal)", "Tangkap layar atau cetakan mesej", "Resit pindahan (jika ada)"],
    "zh": ["身份证（正本）", "信息截图或打印件", "转账收据（如有）"],
    "ta": ["அடையாள அட்டை (அசல்)", "செய்தியின் திரைப்படம் அல்லது அச்சு", "பரிமாற்ற ரசீது (இருந்தால்)"],
}

SCAM_REPORT_DRAFT = {
    "en": "SCAM REPORT (draft)\nChannel: SMS / WhatsApp / call / email\nWhat it said: [short summary]\nWhat I did: I did not pay and did not click any link.\n[Full name]",
    "bm": "LAPORAN SCAM (draf)\nSaluran: SMS / WhatsApp / panggilan / e-mel\nKandungan: [ringkasan mesej]\nTindakan saya: Tidak membuat bayaran. Tidak klik pautan.\n[Nama penuh]",
    "zh": "诈骗举报（草稿）\n渠道：短信 / WhatsApp / 电话 / 电邮\n内容：[简短摘要]\n我的做法：我没有付款，也没有点击任何链接。\n[全名]",
    "ta": "மோசடிப் புகார் (வரைவு)\nவழி: SMS / WhatsApp / அழைப்பு / மின்னஞ்சல்\nஉள்ளடக்கம்: [சுருக்கம்]\nநான் செய்தது: பணம் செலுத்தவில்லை, இணைப்பைக் கிளிக் செய்யவில்லை.\n[முழுப் பெயர்]",
}
VERIFY_NOTE_DRAFT = {  # sender is not a known agency: a checklist, never an agency letter
    "en": "I am not sure who sent this message, so I will not reply or pay yet.\nBefore acting I will:\n1. Find the organisation's real website or number myself.\n2. Ask them whether they sent it.\n3. Ask a family member or friend.",
    "bm": "Saya tidak pasti siapa yang menghantar mesej ini, jadi saya tidak akan membalas atau membayar dahulu.\nSebelum bertindak saya akan:\n1. Cari laman web atau nombor sebenar organisasi itu sendiri.\n2. Tanya mereka sama ada mereka yang hantar.\n3. Tanya ahli keluarga atau kawan.",
    "zh": "我不确定这条信息是谁发的，所以先不回复也不付款。\n行动之前我会：\n1. 自己查找该机构的真实网站或号码。\n2. 向他们确认是否发过这条信息。\n3. 问问家人或朋友。",
    "ta": "இந்தச் செய்தியை யார் அனுப்பினார் என்று தெரியவில்லை; எனவே இப்போது பதிலளிக்கவோ பணம் செலுத்தவோ மாட்டேன்.\nசெயல்படும் முன்:\n1. அந்த அமைப்பின் உண்மையான இணையதளம் அல்லது எண்ணை நானே கண்டுபிடிப்பேன்.\n2. அவர்கள்தான் அனுப்பினார்களா என்று கேட்பேன்.\n3. குடும்பத்தினர் அல்லது நண்பரிடம் கேட்பேன்.",
}
LETTER_DRAFT = {
    "bm": "Kepada: {agency}\nPerkara: Pertanyaan / Permohonan berkaitan rujukan {ref}\n\nTuan/Puan,\nSaya merujuk kepada notis {ref}{amount}.\n[Nyatakan permohonan anda]\n\nSekian, terima kasih.\n[Nama penuh]",
    "en": "To: {agency}\nSubject: Enquiry / request regarding reference {ref}\n\nDear Sir/Madam,\nI refer to notice {ref}{amount}.\n[State your request]\n\nThank you.\n[Full name]",
    "zh": "致：{agency}\n事由：关于编号 {ref} 的查询/申请\n\n您好，\n我就通知 {ref}{amount} 来函。\n[请写明您的要求]\n\n谢谢。\n[全名]",
    "ta": "பெறுநர்: {agency}\nபொருள்: குறிப்பு எண் {ref} தொடர்பான விசாரணை / கோரிக்கை\n\nஐயா/அம்மையீர்,\nஅறிவிப்பு {ref}{amount} குறித்து எழுதுகிறேன்.\n[உங்கள் கோரிக்கையைக் குறிப்பிடுங்கள்]\n\nநன்றி.\n[முழுப் பெயர்]",
}
AMOUNT_PIECE = {"bm": " berjumlah {a}", "en": " for {a}", "zh": "，金额 {a}", "ta": ", தொகை {a}"}
REMINDER = {"bm": "7 hari sebelum {d}", "en": "7 days before {d}", "zh": "{d} 前 7 天", "ta": "{d}-க்கு 7 நாட்களுக்கு முன்"}


def scam_lesson(scam_type: str, language: str) -> dict:
    t = scam_type if scam_type in LESSON_A else "other"
    return {"question": LESSON_Q[language], "answer": LESSON_A[t][language], "terms": TERMS}


def scam_route(scam_type: str, language: str, source_date: str) -> dict:
    t = scam_type if scam_type in FIRST_STEP else "other"
    return {"online_steps": [FIRST_STEP[t][language]] + COMMON_ONLINE[language],
            "walkin_steps": list(COMMON_WALKIN[language]),
            "prepare_online": list(PREPARE_ONLINE[language]),
            "prepare_walkin": list(PREPARE_WALKIN[language]),
            "source_url": "https://semakmule.rmp.gov.my", "retrieved_at": source_date, "confidence": "Medium"}
