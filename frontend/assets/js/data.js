/* =========================================================
   Tulen: example content
   ALL LETTERS BELOW ARE FICTIONAL SAMPLES. No real names,
   IC numbers, accounts or cases. Procedures are illustrative
   and must be retrieved from official sites at runtime.
   Chinese / Tamil text: have a native speaker review before demo.
   ========================================================= */

/* Translations of English (or BM) strings used in the sample data, keyed by the original text.
   Order: [bm, en, zh, ta]; null = keep the key. zh and ta need native review.
   Route steps and the "kenapa" paragraphs of the sample letters stay English only. */
const X = (bm, zh, ta) => [bm, null, zh, ta];
const TR = {
  /* sample checks */
  "Issuer matches official domain hasil.gov.my": X("Pengirim sepadan dengan domain rasmi hasil.gov.my", "发件方与官方网域 hasil.gov.my 相符", "அனுப்பியவர் அதிகாரப்பூர்வ இணையதளமான hasil.gov.my உடன் பொருந்துகிறது"),
  "Reference number follows the expected pattern": X("Nombor rujukan mengikut corak yang betul", "参考编号的格式正确", "குறிப்பு எண் சரியான வடிவத்தில் உள்ளது"),
  "Payment only through an official channel (ByrHASIL / MyTax)": X("Bayaran hanya melalui saluran rasmi (ByrHASIL / MyTax)", "只通过官方渠道（ByrHASIL / MyTax）付款", "அதிகாரப்பூர்வ வழியில் (ByrHASIL / MyTax) மட்டுமே பணம் செலுத்தச் சொல்கிறது"),
  "No personal bank account, no shortened link, no threat of arrest": X("Tiada akaun bank peribadi, tiada pautan pendek, tiada ugutan tangkap", "没有私人银行户口、没有短链接、没有逮捕威胁", "தனிப்பட்ட வங்கிக் கணக்கு, சுருக்க இணைப்பு, கைது மிரட்டல் எதுவும் இல்லை"),
  "Issuer matches official domain jpj.gov.my": X("Pengirim sepadan dengan domain rasmi jpj.gov.my", "发件方与官方网域 jpj.gov.my 相符", "அனுப்பியவர் அதிகாரப்பூர்வ இணையதளமான jpj.gov.my உடன் பொருந்துகிறது"),
  "Vehicle and offence details are specific and checkable in MyJPJ": X("Butiran kenderaan dan kesalahan jelas dan boleh disemak dalam MyJPJ", "车辆和违例的详情很具体，可以在 MyJPJ 查证", "வாகனம் மற்றும் குற்ற விவரங்கள் தெளிவாக உள்ளன; MyJPJ-இல் சரிபார்க்கலாம்"),
  "Payment only through official JPJ channels": X("Bayaran hanya melalui saluran rasmi JPJ", "只通过 JPJ 官方渠道付款", "JPJ அதிகாரப்பூர்வ வழிகளில் மட்டுமே பணம் செலுத்தச் சொல்கிறது"),
  "No request for bank login, TAC or personal transfer": X("Tidak minta log masuk bank, TAC atau pindahan wang peribadi", "没有要求银行登入资料、TAC 或私人转账", "வங்கி உள்நுழைவு, TAC அல்லது தனிப்பட்ட பணப் பரிமாற்றம் கேட்கவில்லை"),
  "Issuer matches official domain ptptn.gov.my": X("Pengirim sepadan dengan domain rasmi ptptn.gov.my", "发件方与官方网域 ptptn.gov.my 相符", "அனுப்பியவர் அதிகாரப்பூர்வ இணையதளமான ptptn.gov.my உடன் பொருந்துகிறது"),
  "Points to the official myPTPTN app, not a link": X("Menunjuk ke aplikasi rasmi myPTPTN, bukan pautan", "指引您使用官方的 myPTPTN 应用程序，而不是链接", "இணைப்பு அல்ல, அதிகாரப்பூர்வ myPTPTN செயலியைக் காட்டுகிறது"),
  "Offers restructuring, no 'today only' discount": X("Tawar penstrukturan semula, tiada diskaun “hari ini sahaja”", "提供重组还款，没有“今天限定”折扣", "மறுசீரமைப்பை வழங்குகிறது; “இன்று மட்டும்” தள்ளுபடி இல்லை"),
  "No transfer to a personal account": X("Tiada pindahan ke akaun peribadi", "没有要求转账到私人户口", "தனிப்பட்ட கணக்குக்குப் பணம் அனுப்பச் சொல்லவில்லை"),
  "Asks you to transfer money to a company or personal account": X("Minta anda pindah wang ke akaun syarikat atau peribadi", "要求您转账到公司或私人户口", "நிறுவனக் கணக்கு அல்லது தனிப்பட்ட கணக்குக்குப் பணம் அனுப்பச் சொல்கிறது"),
  "Shortened link (bit.ly) instead of an official .gov.my site": X("Pautan pendek (bit.ly), bukan laman rasmi .gov.my", "用的是短链接（bit.ly），不是官方 .gov.my 网站", "அதிகாரப்பூர்வ .gov.my தளம் அல்ல, சுருக்க இணைப்பு (bit.ly)"),
  "Threatens arrest within 24 hours to make you panic": X("Ugut tangkap dalam 24 jam supaya anda panik", "威胁24小时内逮捕，让您慌张", "நீங்கள் பயப்பட 24 மணி நேரத்தில் கைது என மிரட்டுகிறது"),
  "Contact is a WhatsApp number and asks you to keep it secret": X("Hubungi melalui WhatsApp dan suruh rahsiakan", "叫您通过 WhatsApp 联络，并要您保密", "WhatsApp-இல் தொடர்புகொள்ளச் சொல்லி, ரகசியமாக வைக்கச் சொல்கிறது"),
  "Reference number does not match any official format": X("Nombor rujukan tidak sepadan dengan format rasmi", "参考编号不符合任何官方格式", "குறிப்பு எண் எந்த அதிகாரப்பூர்வ வடிவத்துக்கும் பொருந்தவில்லை"),
  /* sample fields, labels */
  "Tax assessment": X("Taksiran cukai", "税务评估", "வரி மதிப்பீடு"),
  "Speed camera summons": X("Saman kamera laju", "测速摄像罚单", "வேகக் கேமரா சம்மன்"),
  "Repayment reminder": X("Peringatan bayaran balik", "还款提醒", "திருப்பிச் செலுத்த நினைவூட்டல்"),
  "Demand + threat": X("Tuntutan dan ugutan", "催缴加威胁", "கட்டணக் கோரிக்கையும் மிரட்டலும்"),
  "Unverified": X("Tidak disahkan", "未经证实", "உறுதிசெய்யப்படவில்லை"),
  "24 hours": X("24 jam", "24小时", "24 மணி நேரம்"),
  "Not valid format": X("Format tidak sah", "格式无效", "செல்லாத வடிவம்"),
  "No deadline - this is not a real demand": X("Tiada tarikh akhir: ini bukan tuntutan sebenar", "没有期限：这不是真正的催缴", "கடைசி தேதி இல்லை: இது உண்மையான கோரிக்கை அல்ல"),
  "example data, not live": X("data contoh, bukan data langsung", "示例数据，非实时", "எடுத்துக்காட்டுத் தரவு, நேரடித் தரவு அல்ல"),
  "High": X("Tinggi", "高", "உயர்"), "Medium": X("Sederhana", "中", "நடுத்தர"), "Low": X("Rendah", "低", "குறைவு"),
  "Kenapa saya dapat surat ini?": [null, "Why did I get this letter?", "我为什么会收到这封信？", "எனக்கு ஏன் இந்தக் கடிதம் வந்தது?"],
  "Kenapa saya dapat mesej ini?": [null, "Why did I get this message?", "我为什么会收到这个信息？", "எனக்கு ஏன் இந்தச் செய்தி வந்தது?"],
  "Notis Taksiran": [null, "Assessment notice", "评税通知", "மதிப்பீட்டு அறிவிப்பு"],
  "Notis Saman": [null, "Summons notice", "罚单通知", "சம்மன் அறிவிப்பு"],
  "Notis Peringatan": [null, "Reminder notice", "提醒通知", "நினைவூட்டல் அறிவிப்பு"],
  "Suspicious notice": ["Notis mencurigakan", null, "可疑通知", "சந்தேகத்துக்குரிய அறிவிப்பு"],
  "Pemula": [null, "Beginner", "初学者", "தொடக்க நிலை"], "Celik Surat": [null, "Letter Savvy", "识信达人", "கடிதம் அறிந்தவர்"],
  "Bijak Surat": [null, "Letter Wise", "信件通", "கடிதத் திறமையாளர்"], "Pakar Tulen": [null, "Tulen Expert", "Tulen 专家", "Tulen நிபுணர்"],
  /* glossary sources and practice labels */
  "General": X("Umum", "一般", "பொது"), "Scam": X("Penipuan", "诈骗", "மோசடி"), "Court / PDRM": ["Mahkamah / PDRM", null, "法庭 / PDRM", "நீதிமன்றம் / PDRM"],
  "Email": X("E-mel", "电邮", "மின்னஞ்சல்"), "App": X("Aplikasi", "应用程序", "செயலி"), "Letter": X("Surat", "信件", "கடிதம்"), "Chat": X("Sembang", "聊天", "அரட்டை"),
  "MyJPJ (official app notification)": X("MyJPJ (pemberitahuan aplikasi rasmi)", "MyJPJ（官方应用程序通知）", "MyJPJ (அதிகாரப்பூர்வச் செயலி அறிவிப்பு)"),
  "Majlis Perbandaran (letter by post)": X("Majlis Perbandaran (surat pos)", "市政局（邮寄信件）", "நகராண்மைக் கழகம் (அஞ்சல் கடிதம்)"),
  "Mahkamah Majistret (letter by registered post)": X("Mahkamah Majistret (surat pos berdaftar)", "裁判法庭（挂号信）", "மாஜிஸ்திரேட் நீதிமன்றம் (பதிவு அஞ்சல் கடிதம்)"),
  "Insurans (renewal notice)": X("Insurans (notis pembaharuan)", "保险公司（续保通知）", "காப்பீடு (புதுப்பிப்பு அறிவிப்பு)"),
  /* practice clues */
  "Domain is not hasil.gov.my": X("Domain bukan hasil.gov.my", "网域不是 hasil.gov.my", "இணையதளப் பெயர் hasil.gov.my அல்ல"),
  "Asks for bank login": X("Minta log masuk bank", "要求银行登入资料", "வங்கி உள்நுழைவைக் கேட்கிறது"),
  "2-hour pressure": X("Tekanan 2 jam", "限2小时内，施加压力", "2 மணி நேர அவசரம்"),
  "Inside the official app": X("Dalam aplikasi rasmi", "在官方应用程序内", "அதிகாரப்பூர்வ செயலிக்குள்"),
  "No link to click": X("Tiada pautan untuk diklik", "没有要点击的链接", "கிளிக் செய்ய இணைப்பு இல்லை"),
  "No transfer to an account": X("Tiada pindahan ke akaun", "没有要求转账到户口", "கணக்குக்குப் பணம் அனுப்பச் சொல்லவில்லை"),
  "'Today only' discount": X("Diskaun “hari ini sahaja”", "“今天限定”折扣", "“இன்று மட்டும்” தள்ளுபடி"),
  "Personal account of an 'officer'": X("Akaun peribadi seorang “pegawai”", "“官员”的私人户口", "“அதிகாரி” ஒருவரின் தனிப்பட்ட கணக்கு"),
  "Sent from a mobile number": X("Dihantar dari nombor telefon bimbit", "从手机号码发出", "கைப்பேசி எண்ணிலிருந்து வந்தது"),
  "Regular council bill": X("Bil majlis yang biasa", "一般的市政局账单", "வழக்கமான மன்றக் கட்டணச் சீட்டு"),
  "Official portal or counter": X("Portal atau kaunter rasmi", "官方入口网站或柜台", "அதிகாரப்பூர்வ இணையதளம் அல்லது கவுண்டர்"),
  "Reasonable deadline": X("Tarikh akhir yang munasabah", "期限合理", "நியாயமான கடைசி தேதி"),
  "Banks never ask for your TAC": X("Bank tidak pernah minta TAC anda", "银行绝不会向您索取 TAC", "வங்கிகள் உங்கள் TAC-ஐ ஒருபோதும் கேட்காது"),
  "Fear of frozen account": X("Menakutkan dengan akaun dibekukan", "用户口被冻结来吓您", "கணக்கு முடக்கப்படும் என்ற பயம்"),
  "Asks you to share a code": X("Minta anda beri satu kod", "要您透露验证码", "ஒரு குறியீட்டைத் தரச் சொல்கிறது"),
  "Asks you to attend, not to pay": X("Suruh anda hadir, bukan bayar", "要求您出席，而不是付款", "வரச் சொல்கிறது, பணம் கட்டச் சொல்லவில்லை"),
  "Points to the official registry": X("Tunjuk ke pejabat pendaftar yang rasmi", "指引您联络官方登记处", "அதிகாரப்பூர்வப் பதிவகத்தைக் காட்டுகிறது"),
  "Verifiable case details": X("Butiran kes boleh disemak", "案件详情可以查证", "வழக்கு விவரங்களைச் சரிபார்க்கலாம்"),
  "Routine renewal": X("Pembaharuan biasa", "例行续保", "வழக்கமான புதுப்பிப்பு"),
  "Registered agent / official site": X("Ejen berdaftar / laman rasmi", "注册代理或官方网站", "பதிவு பெற்ற முகவர் / அதிகாரப்பூர்வ தளம்"),
  "No threat": X("Tiada ugutan", "没有威胁", "மிரட்டல் இல்லை"),
  "Agencies don't ask for IC photos on WhatsApp": X("Agensi tidak minta gambar IC melalui WhatsApp", "机构不会通过 WhatsApp 要求身份证照片", "நிறுவனங்கள் WhatsApp-இல் அடையாள அட்டைப் படம் கேட்காது"),
  "Asks for bank details": X("Minta butiran bank", "索取银行资料", "வங்கி விவரங்களைக் கேட்கிறது"),
  "Unverified 'officer'": X("“Pegawai” yang tidak disahkan", "身份未经证实的“官员”", "உறுதிசெய்யப்படாத “அதிகாரி”"),
  /* glossary definitions */
  "Assessment - the official calculation of how much tax you owe for a year.": X("Pengiraan rasmi berapa cukai yang anda perlu bayar untuk setahun.", "官方计算您一年需要缴多少税。", "ஓராண்டுக்கு நீங்கள் எவ்வளவு வரி செலுத்த வேண்டும் என்ற அதிகாரப்பூர்வக் கணக்கு."),
  "Potongan Cukai Bulanan - monthly tax your employer deducts from your salary in advance.": X("Potongan Cukai Bulanan: cukai yang majikan potong dari gaji anda setiap bulan, lebih awal.", "每月扣税：雇主每个月先从您的薪水扣除的税款。", "மாதாந்திர வரிப் பிடித்தம்: உங்கள் முதலாளி ஒவ்வொரு மாதமும் சம்பளத்திலிருந்து முன்கூட்டியே பிடிக்கும் வரி."),
  "Year of assessment - the year of income being taxed (YA 2025 = income earned in 2025).": X("Tahun pendapatan yang dikenakan cukai (TT 2025 = pendapatan tahun 2025).", "被征税的收入所属年份（评税年2025 = 2025年的收入）。", "வரி போடப்படும் வருமானத்தின் ஆண்டு (2025 மதிப்பீட்டு ஆண்டு = 2025-இல் ஈட்டிய வருமானம்)."),
  "An increase (penalty) added when tax is not paid by the due date.": X("Tambahan (denda) yang dikenakan jika cukai tidak dibayar sebelum tarikh akhir.", "税款没有在到期日前缴付时，会加上的附加费（罚款）。", "வரியைக் கடைசி தேதிக்குள் செலுத்தாவிட்டால் சேர்க்கப்படும் கூடுதல் தொகை (அபராதம்)."),
  "Appeal - a formal request to review a decision you disagree with, within a set time.": X("Permintaan rasmi untuk menyemak semula keputusan yang anda tidak setuju, dalam tempoh yang ditetapkan.", "在规定期限内，正式要求重新审查您不同意的决定。", "நீங்கள் ஏற்காத முடிவை, குறிப்பிட்ட காலத்துக்குள் மீண்டும் பார்க்கச் சொல்லும் முறையான கோரிக்கை."),
  "Summons - an official notice of an offence that requires action.": X("Notis rasmi tentang satu kesalahan. Anda perlu bertindak.", "关于违例的正式通知，您必须处理。", "குற்றம் பற்றிய அதிகாரப்பூர்வ அறிவிப்பு. நீங்கள் நடவடிக்கை எடுக்க வேண்டும்."),
  "Compound - a fine you can pay to settle an offence without going to court.": X("Denda yang boleh dibayar untuk selesaikan kesalahan tanpa pergi ke mahkamah.", "缴付后就能了结违例、不用上法庭的罚款。", "நீதிமன்றம் செல்லாமல் குற்றத்தைத் தீர்க்கச் செலுத்தும் அபராதம்."),
  "Registered owner - the person whose name the vehicle is registered under.": X("Orang yang namanya didaftarkan pada kenderaan itu.", "车辆登记在其名下的人。", "வாகனம் யாருடைய பெயரில் பதிவாகியுள்ளதோ அவர்."),
  "Automated speed and red-light camera system that records the vehicle plate.": X("Sistem kamera automatik untuk laju dan lampu merah. Ia merakam nombor plat kenderaan.", "自动测速和闯红灯摄像系统，会拍下车牌号码。", "வேகம் மற்றும் சிவப்பு விளக்கை மீறுவதைத் தானாகப் பதிவு செய்யும் கேமரா அமைப்பு. அது வாகன எண் பலகையைப் பதிவு செய்யும்."),
  "Arrears - payments that are overdue.": X("Bayaran yang sudah lewat.", "已经过期未缴的款项。", "செலுத்த வேண்டிய தேதி கடந்தும் செலுத்தாத பணம்."),
  "Repayment - paying back a loan by instalments.": X("Membayar balik pinjaman sedikit demi sedikit setiap bulan.", "分期把贷款还清。", "கடனைத் தவணை முறையில் திருப்பிக் கட்டுதல்."),
  "Restructuring - formally changing your repayment schedule.": X("Menukar jadual bayaran balik anda secara rasmi.", "正式更改您的还款计划。", "உங்கள் திருப்பிச் செலுத்தும் அட்டவணையை முறைப்படி மாற்றுதல்."),
  "Arrest warrant - issued by a court, never 'cancelled' by paying a stranger.": X("Dikeluarkan oleh mahkamah. Ia tidak boleh dibatalkan dengan membayar kepada orang yang tidak dikenali.", "由法庭发出。向陌生人付钱是无法“取消”的。", "நீதிமன்றம் வழங்குவது. தெரியாத ஒருவருக்குப் பணம் கொடுத்து அதை “ரத்து” செய்ய முடியாது."),
  "National Scam Response Centre hotline - call quickly if money was taken by a scam.": X("Talian Pusat Respons Scam Kebangsaan. Telefon segera jika wang anda diambil oleh penipu.", "国家诈骗回应中心热线。如果钱被骗走，请马上拨打。", "தேசிய மோசடி பதில் மையத்தின் உதவி எண். மோசடியில் பணம் போனால் உடனே அழைக்கவும்."),
  "Official domain - Malaysian government sites end in .gov.my.": X("Laman web kerajaan Malaysia berakhir dengan .gov.my.", "马来西亚政府网站的网址以 .gov.my 结尾。", "மலேசிய அரசாங்க இணையதளங்கள் .gov.my என்று முடியும்."),
  "Notice - an official written message telling you something you must know or do.": X("Mesej bertulis rasmi yang memberitahu perkara yang anda perlu tahu atau buat.", "正式的书面信息，告诉您需要知道或要做的事。", "நீங்கள் தெரிந்துகொள்ள அல்லது செய்ய வேண்டியதைச் சொல்லும் அதிகாரப்பூர்வ எழுத்துச் செய்தி.")
};

window.FAHAM_DATA = {
  tr: TR,
  languages: {
    bm: { label: "BM", name: "Bahasa Melayu", speech: "ms-MY" },
    en: { label: "EN", name: "English", speech: "en-GB" },
    zh: { label: "中文", name: "中文", speech: "zh-CN" },
    ta: { label: "தமிழ்", name: "தமிழ்", speech: "ta-IN" }
  },

  /* ---------- Fictional example letters for the checker ---------- */
  letters: [
    {
      id: "lhdn",
      short: "LHDN",
      kind: "Notis Taksiran",
      issuer: "Lembaga Hasil Dalam Negeri Malaysia (LHDN)",
      issuerShort: "LHDN · hasil.gov.my",
      title: "NOTIS TAKSIRAN CUKAI PENDAPATAN - TAHUN TAKSIRAN 2025",
      ref: "LHDN/SAMPEL/TT2025/0001",
      date: "1 November 2026",
      to: "AHMAD BIN CONTOH",
      body: [
        "Tuan/Puan,",
        "Dimaklumkan bahawa <mark>taksiran</mark> cukai pendapatan bagi <mark>Tahun Taksiran 2025</mark> telah dibuat ke atas tuan/puan.",
        "Baki cukai kena dibayar: <mark>RM 1,240.00</mark>. Bayaran hendaklah dijelaskan dalam tempoh 30 hari, iaitu sebelum <mark>15 Disember 2026</mark>.",
        "Kegagalan membuat bayaran dalam tempoh tersebut boleh menyebabkan <mark>kenaikan</mark> dikenakan ke atas baki cukai. Bayaran boleh dibuat melalui saluran rasmi ByrHASIL di portal MyTax.",
        "Sekiranya tuan/puan tidak bersetuju dengan taksiran ini, <mark>rayuan</mark> boleh dikemukakan dalam tempoh yang ditetapkan."
      ],
      fields: { Issuer: "LHDN", Type: "Tax assessment", Amount: "RM 1,240.00", Deadline: "15 Dec 2026", Reference: "LHDN/SAMPEL/…0001", Urgency: "Medium · 39 days" },
      scam: {
        genuine: true, score: 94,
        checks: [
          "Issuer matches official domain hasil.gov.my",
          "Reference number follows the expected pattern",
          "Payment only through an official channel (ByrHASIL / MyTax)",
          "No personal bank account, no shortened link, no threat of arrest"
        ]
      },
      explain: {
        bm: ["Surat ini kelihatan seperti surat LHDN. Selepas anda isi e-Filing, LHDN dapati cukai yang dipotong dari gaji anda (PCB) belum cukup untuk tahun 2025.", "Anda perlu bayar baki RM 1,240 sebelum 15 Disember 2026. Jika tidak setuju dengan jumlah ini, anda boleh buat rayuan."],
        en: ["This looks like a normal LHDN letter. After you filed your e-Filing, LHDN found that the tax deducted from your salary (PCB) did not cover all of your 2025 tax.", "You need to pay the balance of RM 1,240 before 15 December 2026. If you disagree with the amount, you can file an appeal."],
        zh: ["这看起来像内陆税收局（LHDN）的信件。您提交报税后，税局发现2025年从薪水中扣除的税款（PCB）不足。", "您需要在2026年12月15日之前缴付余额 RM 1,240。如果不同意此金额，可以提出上诉。"],
        ta: ["இது LHDN கடிதம் போலத் தெரிகிறது. நீங்கள் e-Filing செய்த பிறகு, 2025-க்கு உங்கள் சம்பளத்திலிருந்து பிடிக்கப்பட்ட வரி (PCB) போதவில்லை என்று LHDN கண்டறிந்தது.", "மீதமுள்ள RM 1,240-ஐ 15 டிசம்பர் 2026-க்கு முன் செலுத்த வேண்டும். தொகையில் உடன்பாடு இல்லையெனில் மேல்முறையீடு செய்யலாம்."]
      },
      kenapa: {
        q: "Kenapa saya dapat surat ini?",
        a: "Your employer deducts tax every month (PCB) based on an estimate. If you had side income, a bonus, or changed jobs, the estimate can fall short. When you file e-BE/e-Filing, LHDN compares what you owe with what was deducted, and sends this notice for the gap.",
        rule: "Rule behind it: income tax is assessed per year of assessment; unpaid balances after the due date can attract an increase (penalty)."
      },
      terms: ["Taksiran", "PCB", "Tahun Taksiran", "Kenaikan", "Rayuan"],
      route: {
        online: {
          steps: ["Open the official MyTax portal (mytax.hasil.gov.my) and log in with your IC number.", "Choose ByrHASIL → Bayaran (payment) and select FPX online banking or card.", "Enter your income tax number, year of assessment 2025 and the amount RM 1,240.00.", "Save the payment receipt PDF; Tulen files it in your reminder."],
          prepare: ["IC number", "Income tax number", "Reference no.", "Online banking"]
        },
        walkin: {
          steps: ["Nearest LHDN branch is located from your postcode (example data).", "Check opening hours and whether an appointment is needed on hasil.gov.my before going.", "Bring the documents below; ask the counter about instalment if the amount is hard to pay at once."],
          prepare: ["IC (original)", "This notice", "Income tax number", "Latest payslip"]
        },
        source: "hasil.gov.my · MyTax", confidence: "High"
      },
      draft: "Kepada: Pengarah, LHDN Cawangan [auto]\nPerkara: Permohonan Bayaran Secara Ansuran - Tahun Taksiran 2025\nRujukan: LHDN/SAMPEL/TT2025/0001\n\nTuan/Puan,\nSaya merujuk kepada notis taksiran bertarikh 1 November 2026 berjumlah RM 1,240.00.\nSaya memohon agar bayaran ini dibenarkan secara ansuran selama 4 bulan atas sebab kekangan kewangan semasa.\n\nSekian, terima kasih.\n[Nama penuh]\n[No. cukai pendapatan]",
      reminder: "8 Dec 2026 · 7 days before deadline"
    },

    {
      id: "jpj",
      short: "JPJ",
      kind: "Notis Saman",
      issuer: "Jabatan Pengangkutan Jalan Malaysia (JPJ)",
      issuerShort: "JPJ · jpj.gov.my",
      title: "NOTIS SAMAN - KESALAHAN MELEBIHI HAD LAJU (KAMERA AwAS)",
      ref: "JPJ/SAMPEL/AWAS/2026/0042",
      date: "28 Oktober 2026",
      to: "PEMILIK BERDAFTAR KENDERAAN JXX 0000 (SAMPEL)",
      body: [
        "Tuan/Puan,",
        "Kenderaan di atas telah dikesan oleh <mark>kamera AwAS</mark> memandu melebihi had laju yang ditetapkan pada 12 Oktober 2026.",
        "Tuan/Puan selaku <mark>pemilik berdaftar</mark> dikehendaki menjelaskan <mark>kompaun</mark> sebanyak <mark>RM 300.00</mark> sebelum <mark>20 Disember 2026</mark>.",
        "Jika kenderaan dipandu oleh orang lain pada masa kesalahan, sila kemukakan maklumat pemandu mengikut arahan di belakang notis ini.",
        "Bayaran boleh dibuat melalui saluran rasmi JPJ. Kegagalan bertindak boleh menyebabkan tindakan <mark>saman</mark> mahkamah."
      ],
      fields: { Issuer: "JPJ", Type: "Speed camera summons", Amount: "RM 300.00", Deadline: "20 Dec 2026", Reference: "JPJ/SAMPEL/…0042", Urgency: "Medium · 44 days" },
      scam: {
        genuine: true, score: 91,
        checks: [
          "Issuer matches official domain jpj.gov.my",
          "Vehicle and offence details are specific and checkable in MyJPJ",
          "Payment only through official JPJ channels",
          "No request for bank login, TAC or personal transfer"
        ]
      },
      explain: {
        bm: ["Ini kelihatan seperti notis saman JPJ. Kamera AwAS merakam kereta anda memandu lebih laju daripada had pada 12 Oktober.", "Bayar kompaun RM 300 sebelum 20 Disember 2026. Jika orang lain yang memandu, anda boleh namakan pemandu itu."],
        en: ["This looks like a normal JPJ summons. An AwAS camera recorded your car above the speed limit on 12 October.", "Pay the RM 300 compound before 20 December 2026. If someone else was driving, you can name that driver."],
        zh: ["这看起来像陆路交通局（JPJ）的罚单。AwAS 测速摄像头记录到您的车辆于10月12日超速。", "请在2026年12月20日之前缴付 RM 300 罚款。如果当时是其他人驾驶，您可以申报该司机。"],
        ta: ["இது JPJ அபராத அறிவிப்பு போலத் தெரிகிறது. அக்டோபர் 12 அன்று உங்கள் கார் வேக வரம்பை மீறியதாக AwAS கேமரா பதிவு செய்தது.", "RM 300 அபராதத்தை 20 டிசம்பர் 2026-க்கு முன் செலுத்தவும். வேறு ஒருவர் ஓட்டியிருந்தால், அந்த ஓட்டுநரின் பெயரைத் தெரிவிக்கலாம்."]
      },
      kenapa: {
        q: "Kenapa saya dapat surat ini?",
        a: "Speed cameras photograph the plate, not the driver, so the notice goes to the registered owner of the vehicle. The owner either settles the compound or tells JPJ who was driving.",
        rule: "Rule behind it: road traffic offences can be settled by compound; an unsettled compound can be escalated to court."
      },
      terms: ["Saman", "Kompaun", "Pemilik berdaftar", "AwAS"],
      route: {
        online: {
          steps: ["Open the official MyJPJ app or jpj.gov.my and log in.", "Go to Semakan Saman (check summons) and confirm the vehicle number and reference.", "Pay the compound by FPX or card inside the official app.", "Keep the e-receipt; Tulen marks this letter as cleared."],
          prepare: ["IC number", "Vehicle no.", "Reference no.", "Online banking"]
        },
        walkin: {
          steps: ["Nearest JPJ office is located from your postcode (example data).", "Check counter hours and any queue app on the official site first.", "Bring the documents below; ask how to nominate the driver if it was not you."],
          prepare: ["IC (original)", "This notice", "Vehicle grant / ownership"]
        },
        source: "jpj.gov.my · MyJPJ", confidence: "High"
      },
      draft: "Kepada: Pengarah JPJ Negeri [auto]\nPerkara: Penamaan Pemandu bagi Notis Saman JPJ/SAMPEL/AWAS/2026/0042\n\nTuan/Puan,\nSaya, pemilik berdaftar kenderaan JXX 0000, memaklumkan bahawa kenderaan tersebut dipandu oleh [nama pemandu, no. KP] pada tarikh kesalahan.\nBersama-sama ini disertakan salinan lesen memandu beliau.\n\nSekian, terima kasih.\n[Nama penuh]",
      reminder: "13 Dec 2026 · 7 days before deadline"
    },

    {
      id: "ptptn",
      short: "PTPTN",
      kind: "Notis Peringatan",
      issuer: "Perbadanan Tabung Pendidikan Tinggi Nasional (PTPTN)",
      issuerShort: "PTPTN · ptptn.gov.my",
      title: "NOTIS PERINGATAN - TUNGGAKAN BAYARAN BALIK PINJAMAN",
      ref: "PTPTN/SAMPEL/BB/2026/7781",
      date: "3 November 2026",
      to: "NUR CONTOH BINTI SAMPEL",
      body: [
        "Tuan/Puan,",
        "Rekod kami menunjukkan akaun pinjaman tuan/puan mempunyai <mark>tunggakan</mark> sebanyak <mark>RM 450.00</mark> bagi tempoh tiga bulan.",
        "Tuan/Puan dinasihatkan menjelaskan tunggakan sebelum <mark>31 Disember 2026</mark> atau menghubungi PTPTN untuk <mark>penstrukturan semula</mark> jadual <mark>bayaran balik</mark>.",
        "Bayaran boleh dibuat melalui aplikasi myPTPTN atau potongan gaji. Kegagalan bertindak boleh menyebabkan tindakan susulan."
      ],
      fields: { Issuer: "PTPTN", Type: "Repayment reminder", Amount: "RM 450.00", Deadline: "31 Dec 2026", Reference: "PTPTN/SAMPEL/…7781", Urgency: "Low · 55 days" },
      scam: {
        genuine: true, score: 89,
        checks: [
          "Issuer matches official domain ptptn.gov.my",
          "Points to the official myPTPTN app, not a link",
          "Offers restructuring, no 'today only' discount",
          "No transfer to a personal account"
        ]
      },
      explain: {
        bm: ["Ini kelihatan seperti peringatan PTPTN. Anda terlepas bayaran pinjaman selama tiga bulan, jumlahnya RM 450.", "Bayar sebelum 31 Disember 2026 melalui myPTPTN, atau minta jadual bayaran baru jika gaji anda belum stabil."],
        en: ["This looks like a normal PTPTN reminder. You missed three months of loan repayments, totalling RM 450.", "Pay before 31 December 2026 through myPTPTN, or ask for a new repayment schedule if your income is not stable yet."],
        zh: ["这看起来像国家高等教育基金（PTPTN）的提醒。您已拖欠三个月的贷款还款，共 RM 450。", "请在2026年12月31日之前通过 myPTPTN 缴付，或者如果收入尚未稳定，可申请新的还款计划。"],
        ta: ["இது PTPTN நினைவூட்டல் போலத் தெரிகிறது. மூன்று மாத கடன் தவணைகள், மொத்தம் RM 450, செலுத்தப்படவில்லை.", "31 டிசம்பர் 2026-க்கு முன் myPTPTN மூலம் செலுத்தவும், அல்லது வருமானம் நிலையாக இல்லையெனில் புதிய தவணை அட்டவணையைக் கேட்கவும்."]
      },
      kenapa: {
        q: "Kenapa saya dapat surat ini?",
        a: "Education loans start repayment after you graduate. When monthly payments are missed, the system flags the account and sends a reminder before stronger follow-up actions begin.",
        rule: "Rule behind it: repayment follows the schedule in your loan agreement; restructuring is the formal way to change it."
      },
      terms: ["Tunggakan", "Bayaran balik", "Penstrukturan semula"],
      route: {
        online: {
          steps: ["Open the official myPTPTN app and log in.", "Check the arrears amount matches RM 450.00.", "Pay by FPX, or choose the option to apply for restructuring / salary deduction.", "Save the receipt; Tulen sets a monthly reminder from now."],
          prepare: ["IC number", "Loan account no.", "Online banking"]
        },
        walkin: {
          steps: ["Nearest PTPTN counter is located from your postcode (example data).", "Check hours on ptptn.gov.my first.", "Bring the documents below and ask about a restructured schedule."],
          prepare: ["IC (original)", "This notice", "Latest payslip / offer letter"]
        },
        source: "ptptn.gov.my · myPTPTN", confidence: "High"
      },
      draft: "Kepada: PTPTN [auto]\nPerkara: Permohonan Penstrukturan Semula Bayaran Balik\nRujukan: PTPTN/SAMPEL/BB/2026/7781\n\nTuan/Puan,\nSaya baru memulakan pekerjaan dan pendapatan saya belum stabil.\nSaya memohon jadual bayaran balik baharu dengan ansuran bulanan yang lebih rendah.\n\nSekian, terima kasih.\n[Nama penuh]",
      reminder: "24 Dec 2026 · 7 days before deadline"
    },

    {
      id: "scam",
      short: "\"PDRM\"",
      kind: "Suspicious notice",
      issuer: "Claims to be: PDRM (Polis Diraja Malaysia)",
      issuerShort: "Unverified sender",
      title: "NOTIS SEGERA - SAMAN TERTUNGGAK & WARAN TANGKAP",
      ref: "PDRM-99X-SEGERA",
      date: "Hari ini",
      to: "PEMILIK AKAUN",
      body: [
        "AMARAN TERAKHIR.",
        "Anda mempunyai 3 saman tertunggak berjumlah RM 2,150.00. <mark class='red'>Bayar dalam masa 24 JAM</mark> atau <mark class='red'>waran tangkap</mark> akan dikeluarkan.",
        "Pindahkan bayaran ke <mark class='red'>akaun Maybank 1234-XXXX-XXXX atas nama \"Syarikat Penyelesaian Saman\"</mark>.",
        "Semak saman anda di: <mark class='red'>bit.ly/saman-pdrm-bayar</mark>",
        "Hubungi Inspektor Rahman di <mark class='red'>WhatsApp 011-XXXX XXXX</mark>. Jangan beritahu sesiapa."
      ],
      fields: { Issuer: "Unverified", Type: "Demand + threat", Amount: "RM 2,150.00", Deadline: "24 hours", Reference: "Not valid format", Urgency: "Fake urgency" },
      scam: {
        genuine: false, score: 8,
        checks: [
          "x|Asks you to transfer money to a company or personal account",
          "x|Shortened link (bit.ly) instead of an official .gov.my site",
          "x|Threatens arrest within 24 hours to make you panic",
          "x|Contact is a WhatsApp number and asks you to keep it secret",
          "x|Reference number does not match any official format"
        ]
      },
      explain: {
        bm: ["Ini hampir pasti SCAM. Polis tidak akan minta anda pindah wang ke akaun syarikat atau peribadi, dan tidak ugut waran tangkap dalam 24 jam melalui mesej.", "Jangan klik pautan dan jangan bayar. Semak saman anda sendiri di saluran rasmi PDRM, atau hubungi talian NSRC 997 jika anda sudah tertipu."],
        en: ["This is almost certainly a SCAM. Police will not ask you to transfer money to a company or personal account, or threaten arrest within 24 hours by message.", "Do not click the link and do not pay. Check your summons yourself on official PDRM channels, or call the NSRC hotline 997 if you have already been tricked."],
        zh: ["这几乎可以肯定是诈骗。警方不会要求您转账到公司或私人户口，也不会通过短信威胁24小时内发出逮捕令。", "不要点击链接，也不要付款。请自行通过警方官方渠道查询罚单；如果已经受骗，请拨打 NSRC 热线 997。"],
        ta: ["இது கிட்டத்தட்ட நிச்சயமாக ஒரு மோசடி. நிறுவன அல்லது தனிப்பட்ட கணக்கிற்குப் பணம் அனுப்பச் சொல்லியோ, 24 மணி நேரத்தில் கைது செய்வதாகச் செய்தியில் மிரட்டியோ காவல்துறை கேட்காது.", "இணைப்பைக் கிளிக் செய்யவோ பணம் செலுத்தவோ வேண்டாம். அதிகாரப்பூர்வ PDRM வழிகளில் நீங்களே சரிபார்க்கவும்; ஏமாற்றப்பட்டிருந்தால் NSRC 997-ஐ அழைக்கவும்."]
      },
      kenapa: {
        q: "Kenapa saya dapat mesej ini?",
        a: "Scammers copy logos and official words like 'saman' and 'waran' because people fear the police. They add a short deadline so you act before you think or ask someone.",
        rule: "Rule of thumb: official agencies use .gov.my sites and official apps, never ask for transfers to personal accounts, and never ask you to keep it secret."
      },
      terms: ["Waran tangkap", "NSRC 997", "Domain rasmi"],
      route: {
        online: {
          steps: ["Do NOT open the bit.ly link or reply on WhatsApp.", "Check for real summons yourself through the official PDRM channel or MyBayar PDRM.", "Report the number and message to the NSRC (997) or via Semak Mule (semakmule.rmp.gov.my).", "If you already transferred money, call your bank and 997 immediately."],
          prepare: ["Screenshot of message", "Sender number", "Bank (if you paid)"]
        },
        walkin: {
          steps: ["Nearest police station is located from your postcode (example data).", "Make a police report if money was lost.", "Bring the evidence below."],
          prepare: ["IC (original)", "Screenshots", "Bank transaction slip"]
        },
        source: "rmp.gov.my · NSRC 997", confidence: "High"
      },
      draft: "LAPORAN SCAM (draf untuk NSRC / balai polis)\n\nTarikh terima: [auto]\nSaluran: SMS / WhatsApp\nNombor penghantar: 011-XXXX XXXX\nKandungan: Mendakwa dari PDRM, minta pindahan RM 2,150 ke akaun \"Syarikat Penyelesaian Saman\" dalam 24 jam dan ugut waran tangkap. Pautan: bit.ly/saman-pdrm-bayar\nTindakan saya: Tidak membuat bayaran. Tidak klik pautan.\n\n[Nama penuh]",
      reminder: "No deadline - this is not a real demand"
    }
  ],

  /* ---------- Glossary (Kamus Surat) ---------- */
  glossary: {
    "Taksiran": { src: "LHDN", def: "Assessment - the official calculation of how much tax you owe for a year." },
    "PCB": { src: "LHDN", def: "Potongan Cukai Bulanan - monthly tax your employer deducts from your salary in advance." },
    "Tahun Taksiran": { src: "LHDN", def: "Year of assessment - the year of income being taxed (YA 2025 = income earned in 2025)." },
    "Kenaikan": { src: "LHDN", def: "An increase (penalty) added when tax is not paid by the due date." },
    "Rayuan": { src: "General", def: "Appeal - a formal request to review a decision you disagree with, within a set time." },
    "Saman": { src: "JPJ / PDRM", def: "Summons - an official notice of an offence that requires action." },
    "Kompaun": { src: "JPJ / PDRM", def: "Compound - a fine you can pay to settle an offence without going to court." },
    "Pemilik berdaftar": { src: "JPJ", def: "Registered owner - the person whose name the vehicle is registered under." },
    "AwAS": { src: "JPJ", def: "Automated speed and red-light camera system that records the vehicle plate." },
    "Tunggakan": { src: "PTPTN / Bank", def: "Arrears - payments that are overdue." },
    "Bayaran balik": { src: "PTPTN", def: "Repayment - paying back a loan by instalments." },
    "Penstrukturan semula": { src: "PTPTN / Bank", def: "Restructuring - formally changing your repayment schedule." },
    "Waran tangkap": { src: "Court / PDRM", def: "Arrest warrant - issued by a court, never 'cancelled' by paying a stranger." },
    "NSRC 997": { src: "Scam", def: "National Scam Response Centre hotline - call quickly if money was taken by a scam." },
    "Domain rasmi": { src: "Scam", def: "Official domain - Malaysian government sites end in .gov.my." },
    "Notis": { src: "General", def: "Notice - an official written message telling you something you must know or do." }
  },

  /* ---------- Practice: Spot the scam (all fictional) ---------- */
  practice: [
    { from: "noreply@hasil-refund-my.com", kind: "Email", text: "Tahniah! Anda layak menerima bayaran balik cukai RM 870. Log masuk akaun bank anda di pautan ini dalam 2 jam untuk tuntut.", scam: true,
      clues: ["Domain is not hasil.gov.my", "Asks for bank login", "2-hour pressure"] },
    { from: "MyJPJ (official app notification)", kind: "App", text: "Anda mempunyai 1 saman baharu. Sila semak butiran dan buat bayaran di dalam aplikasi MyJPJ.", scam: false,
      clues: ["Inside the official app", "No link to click", "No transfer to an account"] },
    { from: "+60 11-XXXX XXXX", kind: "SMS", text: "PTPTN: DISKAUN 50% HARI INI SAHAJA! Pindahkan RM 300 ke akaun peribadi pegawai kami untuk selesaikan pinjaman.", scam: true,
      clues: ["'Today only' discount", "Personal account of an 'officer'", "Sent from a mobile number"] },
    { from: "Majlis Perbandaran (letter by post)", kind: "Letter", text: "Bil Cukai Taksiran Penggal 2/2026 berjumlah RM 98.00. Bayar di portal rasmi majlis atau di kaunter sebelum 31 Disember.", scam: false,
      clues: ["Regular council bill", "Official portal or counter", "Reasonable deadline"] },
    { from: "+60 3-XXXX XXXX (\"Bank\")", kind: "SMS", text: "Akaun anda telah DIBEKUKAN. Berikan nombor TAC yang anda terima kepada pegawai kami untuk aktifkan semula.", scam: true,
      clues: ["Banks never ask for your TAC", "Fear of frozen account", "Asks you to share a code"] },
    { from: "Mahkamah Majistret (letter by registered post)", kind: "Letter", text: "Anda dikehendaki hadir sebagai saksi pada tarikh yang dinyatakan. Sila hubungi pejabat pendaftar di nombor rasmi mahkamah untuk pertanyaan.", scam: false,
      clues: ["Asks you to attend, not to pay", "Points to the official registry", "Verifiable case details"] },
    { from: "Insurans (renewal notice)", kind: "Letter", text: "Polisi kereta anda akan tamat pada 30 Disember. Hubungi ejen berdaftar anda atau perbaharui di laman rasmi syarikat.", scam: false,
      clues: ["Routine renewal", "Registered agent / official site", "No threat"] },
    { from: "WhatsApp: \"Pegawai LHDN\"", kind: "Chat", text: "Hantar gambar IC depan & belakang serta nombor akaun bank untuk proses bayaran balik cukai anda segera.", scam: true,
      clues: ["Agencies don't ask for IC photos on WhatsApp", "Asks for bank details", "Unverified 'officer'"] }
  ],

  levels: [
    { name: "Pemula", min: 0 },
    { name: "Celik Surat", min: 60 },
    { name: "Bijak Surat", min: 140 },
    { name: "Pakar Tulen", min: 240 }
  ]
};
