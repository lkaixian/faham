/* =========================================================
   FAHAM: example content
   ALL LETTERS BELOW ARE FICTIONAL SAMPLES. No real names,
   IC numbers, accounts or cases. Procedures are illustrative
   and must be retrieved from official sites at runtime.
   Chinese / Tamil text: have a native speaker review before demo.
   ========================================================= */

window.FAHAM_DATA = {
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
          steps: ["Open the official MyTax portal (mytax.hasil.gov.my) and log in with your IC number.", "Choose ByrHASIL → Bayaran (payment) and select FPX online banking or card.", "Enter your income tax number, year of assessment 2025 and the amount RM 1,240.00.", "Save the payment receipt PDF; FAHAM files it in your reminder."],
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
          steps: ["Open the official MyJPJ app or jpj.gov.my and log in.", "Go to Semakan Saman (check summons) and confirm the vehicle number and reference.", "Pay the compound by FPX or card inside the official app.", "Keep the e-receipt; FAHAM marks this letter as cleared."],
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
          steps: ["Open the official myPTPTN app and log in.", "Check the arrears amount matches RM 450.00.", "Pay by FPX, or choose the option to apply for restructuring / salary deduction.", "Save the receipt; FAHAM sets a monthly reminder from now."],
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
    { name: "Pakar FAHAM", min: 240 }
  ]
};
