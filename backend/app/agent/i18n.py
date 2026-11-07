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
    # ---- file checks (filecheck.py). zh and ta are drafts for native review
    "file_script": {
        "en": "A program or script file (.exe, .vbs, .bat and similar). Real agencies do not send letters in this form",
        "bm": "Fail program atau skrip (.exe, .vbs, .bat dan seumpamanya). Agensi sebenar tidak menghantar surat dalam bentuk ini",
        "zh": "程序或脚本文件（.exe、.vbs、.bat 等）。真正的机构不会用这种文件发送信函",
        "ta": "நிரல் அல்லது ஸ்கிரிப்ட் கோப்பு (.exe, .vbs, .bat போன்றவை). உண்மையான அமைப்புகள் கடிதங்களை இப்படி அனுப்புவதில்லை",
    },
    "file_script_disguised": {
        "en": "A program or script made to look like a document, or sent over chat. This is a common way to take over a computer",
        "bm": "Program atau skrip yang dibuat menyerupai dokumen, atau dihantar melalui sembang. Ini cara biasa untuk menguasai komputer",
        "zh": "伪装成文档的程序或脚本，或通过聊天发送。这是控制电脑的常见手法",
        "ta": "ஆவணம் போலத் தோன்றும்படி செய்யப்பட்ட நிரல் அல்லது ஸ்கிரிப்ட், அல்லது அரட்டையில் வந்தது. கணினியைக் கைப்பற்றும் பொதுவான வழி இது",
    },
    "file_apk": {
        "en": "An Android app file (.apk). Real apps come from Google Play, not from a message",
        "bm": "Fail aplikasi Android (.apk). Aplikasi sebenar datang dari Google Play, bukan dari mesej",
        "zh": "安卓应用文件（.apk）。正规应用来自 Google Play，而不是来自信息",
        "ta": "ஆண்ட்ராய்டு செயலி கோப்பு (.apk). உண்மையான செயலிகள் Google Play-யிலிருந்து வரும், செய்தியிலிருந்து அல்ல",
    },
    "file_encrypted": {
        "en": "The archive is password protected, so Tulen cannot see what is inside",
        "bm": "Arkib ini dilindungi kata laluan, jadi Tulen tidak dapat melihat isinya",
        "zh": "压缩包有密码保护，Tulen 无法查看里面的内容",
        "ta": "இந்தக் காப்பகம் கடவுச்சொல்லால் பாதுகாக்கப்பட்டுள்ளது, அதனால் உள்ளே என்ன இருக்கிறது என்பதை Tulen பார்க்க முடியாது",
    },
    "file_unreadable": {
        "en": "Tulen could not read this file properly. Scam files sometimes break checkers on purpose",
        "bm": "Tulen tidak dapat membaca fail ini dengan betul. Fail penipuan kadangkala sengaja merosakkan pemeriksa",
        "zh": "Tulen 无法正常读取此文件。诈骗文件有时故意让检查工具出错",
        "ta": "இந்தக் கோப்பை Tulen சரியாகப் படிக்க முடியவில்லை. மோசடிக் கோப்புகள் சில நேரம் வேண்டுமென்றே சரிபார்ப்பைக் குலைக்கும்",
    },
    "file_disk_image": {
        "en": "A disk image or shortcut file (.iso, .img, .lnk). Official letters never come in these",
        "bm": "Fail imej cakera atau pintasan (.iso, .img, .lnk). Surat rasmi tidak datang dalam bentuk ini",
        "zh": "磁盘映像或快捷方式文件（.iso、.img、.lnk）。正式信函不会用这些格式",
        "ta": "வட்டு பிம்பம் அல்லது குறுக்குவழிக் கோப்பு (.iso, .img, .lnk). அதிகாரப்பூர்வ கடிதங்கள் இப்படி வருவதில்லை",
    },
    "file_name_trick": {
        "en": "The file name uses hidden characters to look like something else",
        "bm": "Nama fail menggunakan aksara tersembunyi supaya kelihatan seperti fail lain",
        "zh": "文件名使用了隐藏字符，让它看起来像另一种文件",
        "ta": "கோப்பின் பெயர் மறைந்த எழுத்துகளைப் பயன்படுத்தி வேறு கோப்பு போலத் தோன்றுகிறது",
    },
    "file_lure_name": {
        "en": "The file name copies an agency, bank, parcel or invitation, a common lure",
        "bm": "Nama fail meniru agensi, bank, bungkusan atau jemputan, umpan yang biasa",
        "zh": "文件名冒充机构、银行、包裹或请柬，这是常见的诱饵",
        "ta": "கோப்பின் பெயர் ஒரு அமைப்பு, வங்கி, பார்சல் அல்லது அழைப்பிதழைப் போல நடிக்கிறது; இது பொதுவான தூண்டில்",
    },
    "file_apk_perms": {
        "en": "This app asks for sensitive powers, such as reading your text messages or drawing over other apps. An app sent in a message has not been checked by Google Play",
        "bm": "Aplikasi ini meminta kuasa sensitif, seperti membaca mesej teks anda atau melukis di atas aplikasi lain. Aplikasi yang dihantar dalam mesej tidak disemak oleh Google Play",
        "zh": "此应用要求敏感权限，例如读取你的短信或覆盖在其他应用上方。通过信息发来的应用没有经过 Google Play 审核",
        "ta": "இந்தச் செயலி உங்கள் குறுஞ்செய்திகளைப் படிப்பது அல்லது பிற செயலிகளின் மேல் வரைவது போன்ற முக்கிய அதிகாரங்களைக் கேட்கிறது. செய்தியில் வந்த செயலியை Google Play சரிபார்க்கவில்லை",
    },
    "file_apk_takeover": {
        "en": "This app asks for the powers scam apps use to read TAC codes and control your phone (text messages, screen control, overlays)",
        "bm": "Aplikasi ini meminta kuasa yang digunakan aplikasi penipuan untuk membaca kod TAC dan mengawal telefon anda (mesej teks, kawalan skrin, tindihan)",
        "zh": "此应用要求诈骗应用常用的权限，用来读取 TAC 验证码并控制你的手机（短信、屏幕控制、覆盖层）",
        "ta": "இந்தச் செயலி மோசடிச் செயலிகள் TAC குறியீடுகளைப் படிக்கவும் தொலைபேசியைக் கட்டுப்படுத்தவும் பயன்படுத்தும் அதிகாரங்களைக் கேட்கிறது (குறுஞ்செய்தி, திரைக் கட்டுப்பாடு, மேல்படலம்)",
    },
    "file_apk_brand": {
        "en": "The app uses the name of a bank or agency, but it is not that organisation's known app",
        "bm": "Aplikasi ini menggunakan nama bank atau agensi, tetapi bukan aplikasi yang diketahui milik organisasi itu",
        "zh": "此应用使用了银行或机构的名称，但它不是该机构已知的应用",
        "ta": "இந்தச் செயலி ஒரு வங்கி அல்லது அமைப்பின் பெயரைப் பயன்படுத்துகிறது, ஆனால் அது அந்த அமைப்பின் அறியப்பட்ட செயலி அல்ல",
    },
    "file_macro": {
        "en": "This Office file contains, or probably contains, macros: small programs that run when it is opened. A real letter does not need them",
        "bm": "Fail Office ini mengandungi, atau mungkin mengandungi, makro: atur cara kecil yang berjalan apabila dibuka. Surat sebenar tidak memerlukannya",
        "zh": "此 Office 文件含有或可能含有宏：打开时会自动运行的小程序。真正的信函不需要宏",
        "ta": "இந்த Office கோப்பில் மேக்ரோக்கள் உள்ளன அல்லது இருக்கலாம்: திறக்கும்போது தானாக ஓடும் சிறு நிரல்கள். உண்மையான கடிதத்துக்கு இவை தேவையில்லை",
    },
    "file_macro_hidden": {
        "en": "A file with macros that is named like a plain document and came by chat or a link, a common way to hide it",
        "bm": "Fail bermakro yang dinamakan seperti dokumen biasa dan diterima melalui sembang atau pautan, cara biasa untuk menyembunyikannya",
        "zh": "含有宏的文件被取名成普通文档，并通过聊天或链接发来，这是常见的隐藏手法",
        "ta": "மேக்ரோ உள்ள கோப்பு சாதாரண ஆவணம் போலப் பெயரிடப்பட்டு அரட்டை அல்லது இணைப்பு வழியாக வந்துள்ளது; இது மறைக்கும் பொதுவான வழி",
    },
    "file_office_remote": {
        "en": "This document pulls something from another website or runs a command when opened (a remote template or a DDE field)",
        "bm": "Dokumen ini mengambil sesuatu dari laman web lain atau menjalankan arahan apabila dibuka (templat jauh atau medan DDE)",
        "zh": "此文档在打开时会从其他网站获取内容或运行命令（远程模板或 DDE 字段）",
        "ta": "இந்த ஆவணம் திறக்கும்போது வேறொரு இணையதளத்திலிருந்து ஒன்றை இழுக்கிறது அல்லது கட்டளையை இயக்குகிறது (தொலை வார்ப்புரு அல்லது DDE புலம்)",
    },
    "file_archive_closed": {
        "en": "This kind of archive (.rar, .7z) is not opened by Tulen, so we cannot tell what is inside. Ask the sender what it is, and scan it with your phone or computer security app before opening",
        "bm": "Jenis arkib ini (.rar, .7z) tidak dibuka oleh Tulen, jadi kami tidak dapat tahu isinya. Tanya penghantar apa ia, dan imbas dengan aplikasi keselamatan telefon atau komputer anda sebelum membukanya",
        "zh": "Tulen 不会打开这类压缩包（.rar、.7z），所以无法得知里面是什么。请向发送者确认内容，并在打开前用手机或电脑的安全软件扫描",
        "ta": "இந்த வகைக் காப்பகத்தை (.rar, .7z) Tulen திறப்பதில்லை, அதனால் உள்ளே என்ன இருக்கிறது என்று சொல்ல முடியாது. அனுப்பியவரிடம் அது என்ன என்று கேளுங்கள்; திறப்பதற்கு முன் உங்கள் தொலைபேசி அல்லது கணினியின் பாதுகாப்புச் செயலியால் சோதியுங்கள்",
    },
    "file_zip_tricks": {
        "en": "The archive is built in an unusual way (odd paths, overlapping or appended parts) that hides its contents from checkers",
        "bm": "Arkib dibina dengan cara luar biasa (laluan pelik, bahagian bertindih atau ditambah) untuk menyembunyikan isinya daripada pemeriksa",
        "zh": "压缩包的结构不寻常（路径异常、部分重叠或被附加），用来向检查工具隐藏内容",
        "ta": "காப்பகம் வழக்கத்துக்கு மாறாக உருவாக்கப்பட்டுள்ளது (விசித்திரமான பாதைகள், ஒன்றன் மேல் ஒன்று அல்லது சேர்க்கப்பட்ட பகுதிகள்), உள்ளடக்கத்தைச் சரிபார்ப்பிலிருந்து மறைக்க",
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
    "guaranteed_returns": {
        "en": "Promises guaranteed or very high profit (real investments cannot)",
        "bm": "Menjanjikan untung dijamin atau sangat tinggi (pelaburan sebenar tidak boleh)",
        "zh": "承诺保证赚钱或超高回报（真正的投资做不到）",
        "ta": "உறுதியான அல்லது மிக அதிக லாபம் என்று வாக்களிக்கிறது (உண்மையான முதலீடு இப்படி இருக்காது)",
    },
    "advance_fee": {
        "en": "Asks you to pay a deposit or fee first to start or register",
        "bm": "Minta anda bayar deposit atau yuran dahulu untuk mula atau mendaftar",
        "zh": "要你先付押金或费用才能开始或登记",
        "ta": "தொடங்க அல்லது பதிவு செய்ய முதலில் வைப்புத் தொகை அல்லது கட்டணம் கேட்கிறது",
    },
    "romance_money": {
        "en": "A stranger far away asks you to send money, or to use a friend's account",
        "bm": "Orang tidak dikenali di tempat jauh minta anda hantar wang, atau guna akaun kawannya",
        "zh": "远方的陌生人要你汇款，或汇到他朋友的户口",
        "ta": "தொலைவிலுள்ள அறிமுகமில்லாதவர் பணம் அனுப்பச் சொல்கிறார், அல்லது நண்பரின் கணக்கைப் பயன்படுத்தச் சொல்கிறார்",
    },
    "prize_win": {
        "en": "Says you won a prize you never entered for (a classic scam opening)",
        "bm": "Kata anda menang hadiah yang tidak pernah anda sertai (cara biasa penipu)",
        "zh": "说你中了从没参加过的奖（典型骗局开场）",
        "ta": "நீங்கள் பங்கேற்காத பரிசை வென்றதாகக் கூறுகிறது (பொதுவான மோசடி தொடக்கம்)",
    },
    "safe_account": {
        "en": "Mentions a 'safe account' (real authorities never use one)",
        "bm": "Menyebut 'akaun selamat' (pihak berkuasa sebenar tidak pernah guna)",
        "zh": "提到“安全账户”（真正的执法机构从不使用）",
        "ta": "'பாதுகாப்பான கணக்கு' என்கிறது (உண்மையான அதிகாரிகள் இதைப் பயன்படுத்துவதில்லை)",
    },
    "laundering": {
        "en": "Accuses you of money laundering or a crime",
        "bm": "Menuduh anda terlibat pengubahan wang haram atau jenayah",
        "zh": "指控你涉嫌洗钱或犯罪",
        "ta": "பணமோசடி அல்லது குற்றத்தில் ஈடுபட்டதாகக் குற்றம் சாட்டுகிறது",
    },
    "account_frozen": {
        "en": "Threatens to freeze your account",
        "bm": "Mengugut akan membekukan akaun anda",
        "zh": "威胁要冻结你的户口",
        "ta": "உங்கள் கணக்கை முடக்குவோம் என்று மிரட்டுகிறது",
    },
    "family_impersonation": {
        "en": "Pretends to be a family member with a new number and asks for money",
        "bm": "Berpura-pura ahli keluarga dengan nombor baru dan minta wang",
        "zh": "假扮家人，说换了新号码并要钱",
        "ta": "புதிய எண்ணுடன் குடும்ப உறுப்பினர் போல நடித்துப் பணம் கேட்கிறது",
    },
    "call_old_number": {
        "en": "Call this person on their OLD number first, before sending any money",
        "bm": "Telefon orang ini pada nombor LAMA mereka dahulu, sebelum menghantar sebarang wang",
        "zh": "汇款之前，先打这个人的旧号码确认",
        "ta": "பணம் அனுப்பும் முன், முதலில் அவரின் பழைய எண்ணை அழைக்கவும்",
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
    # ---- agent signals (the AI picks a category and quotes the letter; the sentence is ours)
    "ai_payment_demand": {
        "en": "Asks for payment in an unusual way, such as gift cards, crypto, cash handover or an unofficial account",
        "bm": "Meminta bayaran dengan cara luar biasa, seperti kad hadiah, kripto, serahan tunai atau akaun tidak rasmi",
        "zh": "要求以不寻常的方式付款，例如礼品卡、加密货币、当面交现金或非官方户口",
        "ta": "அசாதாரண வழியில் பணம் கேட்கிறது, எ.கா. பரிசு அட்டைகள், கிரிப்டோ, ரொக்கம் கொடுத்தல் அல்லது அதிகாரப்பூர்வமற்ற கணக்கு",
    },
    "ai_threat": {
        "en": "Uses threats or heavy pressure to make you act at once",
        "bm": "Menggunakan ugutan atau tekanan berat supaya anda bertindak segera",
        "zh": "用威胁或强大压力逼您立刻行动",
        "ta": "உடனே செயல்பட வைக்க மிரட்டல் அல்லது கடும் அழுத்தம் கொடுக்கிறது",
    },
    "ai_credential": {
        "en": "Asks for a password, TAC, OTP, IC photo or online banking login",
        "bm": "Meminta kata laluan, TAC, OTP, gambar IC atau log masuk perbankan dalam talian",
        "zh": "要求提供密码、TAC、OTP、身份证照片或网上银行登入资料",
        "ta": "கடவுச்சொல், TAC, OTP, அடையாள அட்டைப் படம் அல்லது இணைய வங்கி உள்நுழைவைக் கேட்கிறது",
    },
    "ai_remote_access": {
        "en": "Asks you to install an app or give remote access to your phone or computer",
        "bm": "Meminta anda memasang aplikasi atau memberi akses jauh kepada telefon atau komputer anda",
        "zh": "要求您安装应用程序或让对方远程控制您的手机或电脑",
        "ta": "செயலியை நிறுவவும் அல்லது உங்கள் தொலைபேசி, கணினியை தொலைவிலிருந்து இயக்க அனுமதிக்கவும் கேட்கிறது",
    },
    "ai_impersonation": {
        "en": "Claims to be an official body, but the details do not fit (wrong office, law or channel)",
        "bm": "Mendakwa badan rasmi, tetapi butirannya tidak sepadan (pejabat, undang-undang atau saluran yang salah)",
        "zh": "自称官方机构，但细节对不上（机构、法律或渠道不对）",
        "ta": "அதிகாரப்பூர்வ அமைப்பு என்று கூறுகிறது, ஆனால் விவரங்கள் பொருந்தவில்லை (தவறான அலுவலகம், சட்டம் அல்லது வழி)",
    },
    "ai_too_good": {
        "en": "Promises a refund, prize or discount that you did not ask for",
        "bm": "Menjanjikan bayaran balik, hadiah atau diskaun yang anda tidak pohon",
        "zh": "承诺您没有申请过的退款、奖品或折扣",
        "ta": "நீங்கள் கேட்காத பணத் திரும்ப, பரிசு அல்லது தள்ளுபடியை வாக்களிக்கிறது",
    },
    "ai_secrecy": {
        "en": "Asks you to keep it secret or not to tell family or your bank",
        "bm": "Meminta anda merahsiakannya atau tidak memberitahu keluarga atau bank anda",
        "zh": "要求您保密，或不要告诉家人或银行",
        "ta": "ரகசியமாக வைத்திருக்கவும் அல்லது குடும்பத்தினர், வங்கிக்குச் சொல்ல வேண்டாம் எனவும் கேட்கிறது",
    },
    "ai_chat_move": {
        "en": "Moves you to a private chat to carry on",
        "bm": "Mengalihkan anda ke sembang peribadi untuk diteruskan",
        "zh": "把您引到私人聊天继续沟通",
        "ta": "தொடர உங்களைத் தனிப்பட்ட அரட்டைக்கு மாற்றுகிறது",
    },
    "ai_inconsistent": {
        "en": "Contains details that contradict each other",
        "bm": "Mengandungi butiran yang bercanggah antara satu sama lain",
        "zh": "内容里的细节互相矛盾",
        "ta": "ஒன்றுக்கொன்று முரணான விவரங்கள் உள்ளன",
    },
    "ai_new_domain": {
        "en": "The website in the message was registered only recently, which is common for scam sites",
        "bm": "Laman web dalam mesej baru didaftarkan, yang biasa bagi laman penipuan",
        "zh": "信息中的网站是最近才注册的，这在诈骗网站中很常见",
        "ta": "செய்தியில் உள்ள இணையதளம் சமீபத்தில்தான் பதிவு செய்யப்பட்டது; மோசடித் தளங்களில் இது பொதுவானது",
    },
    "ai_official_mismatch": {
        "en": "What the message says does not match the agency's own website (for example how it takes payment)",
        "bm": "Apa yang dinyatakan mesej tidak sepadan dengan laman web rasmi agensi (contohnya cara ia menerima bayaran)",
        "zh": "信息所说的与该机构官方网站不符（例如收款方式）",
        "ta": "செய்தி கூறுவது நிறுவனத்தின் சொந்த இணையதளத்துடன் பொருந்தவில்லை (எ.கா. பணம் பெறும் முறை)",
    },
    "report_h": {
        "en": "Scam report (draft)",
        "bm": "Laporan penipuan (draf)",
        "zh": "诈骗举报（草稿）",
        "ta": "மோசடி புகார் (வரைவு)",
    },
    "report_intro": {
        "en": "I received a message that claims to be from {who}. It looks like a scam. What looks wrong:",
        "bm": "Saya menerima mesej yang mendakwa daripada {who}. Ia kelihatan seperti penipuan. Perkara yang mencurigakan:",
        "zh": "我收到一条自称来自 {who} 的信息，看起来是诈骗。可疑之处：",
        "ta": "{who} அனுப்பியதாகக் கூறும் செய்தி எனக்கு வந்தது. இது மோசடி போலத் தெரிகிறது. சந்தேகத்துக்குரியவை:",
    },
    "report_outro": {
        "en": "I have not paid, clicked any link or shared any TAC or OTP. Please report it to the National Scam Response Centre (NSRC) on 997 and to your bank.",
        "bm": "Saya tidak membayar, mengklik pautan atau berkongsi TAC atau OTP. Sila laporkan kepada Pusat Respons Scam Kebangsaan (NSRC) di 997 dan bank anda.",
        "zh": "我没有付款、点击链接或透露 TAC 或 OTP。请向全国诈骗应对中心（NSRC）997 和您的银行举报。",
        "ta": "நான் பணம் செலுத்தவில்லை, இணைப்புகளைக் கிளிக் செய்யவில்லை, TAC அல்லது OTP ஐப் பகிரவில்லை. தயவுசெய்து NSRC 997 மற்றும் உங்கள் வங்கிக்குப் புகாரளிக்கவும்.",
    },
    "prompt_injection": {
        "en": "Tries to give instructions to an AI checker, which real letters never do",
        "bm": "Cuba memberi arahan kepada penyemak AI, sesuatu yang tidak dibuat oleh surat sebenar",
        "zh": "试图对 AI 检查工具下指令，真正的信件不会这样做",
        "ta": "AI சரிபார்ப்பிக்குக் கட்டளையிட முயல்கிறது; உண்மையான கடிதங்கள் இப்படிச் செய்யாது",
    },
    "family_warning_h": {
        "en": "Message to warn your family",
        "bm": "Mesej untuk memberi amaran kepada keluarga",
        "zh": "提醒家人的信息",
        "ta": "குடும்பத்தினருக்கு எச்சரிக்கை செய்தி",
    },
    "family_warning": {
        "en": "Scam warning: I received a message that looks like a scam. Please do not pay, do not click any link and do not share any TAC or OTP. If you got the same message, call NSRC 997.",
        "bm": "Amaran penipuan: Saya menerima mesej yang kelihatan seperti penipuan. Jangan bayar, jangan klik sebarang pautan dan jangan kongsi TAC atau OTP. Jika anda menerima mesej yang sama, hubungi NSRC 997.",
        "zh": "诈骗提醒：我收到一条看起来像诈骗的信息。请不要付款、不要点击任何链接，也不要透露 TAC 或 OTP。如果您也收到同样的信息，请拨打 NSRC 997。",
        "ta": "மோசடி எச்சரிக்கை: மோசடி போலத் தோன்றும் செய்தி எனக்கு வந்தது. பணம் செலுத்த வேண்டாம், இணைப்புகளைக் கிளிக் செய்ய வேண்டாம், TAC அல்லது OTP ஐப் பகிர வேண்டாம். உங்களுக்கும் இதே செய்தி வந்தால் NSRC 997 ஐ அழைக்கவும்.",
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
