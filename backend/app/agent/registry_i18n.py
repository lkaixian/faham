"""Bahasa Melayu text for the official-source registry (lesson, steps, preparation lists).

The registry JSON stays the English source of truth. `localize(issuer, src, language)` returns the
BM version when one exists. zh and ta fall back to English for registry steps until a native speaker
supplies them (scam-type text in scam_content.py is already complete in all four languages).
"""
from __future__ import annotations

BM: dict[str, dict] = {
    "LHDN": {
        "online_steps": ["Log masuk ke portal rasmi MyTax (mytax.hasil.gov.my).", "Buka ByrHASIL dan pilih bayaran FPX atau kad.", "Masukkan nombor cukai pendapatan, tahun taksiran dan jumlah.", "Simpan resit."],
        "walkin_steps": ["Pergi ke cawangan LHDN terdekat.", "Semak waktu operasi dan syarat temu janji di hasil.gov.my dahulu.", "Tanya kaunter tentang ansuran jika perlu."],
        "prepare_online": ["Nombor kad pengenalan", "Nombor cukai pendapatan", "No. rujukan", "Perbankan dalam talian"],
        "prepare_walkin": ["Kad pengenalan (asal)", "Notis ini", "Nombor cukai pendapatan"],
        "lesson": "Potongan cukai bulanan (PCB) hanyalah anggaran. Apabila taksiran tahunan menunjukkan cukai lebih banyak daripada yang dipotong, LHDN menghantar notis untuk baki itu.",
    },
    "JPJ": {
        "online_steps": ["Buka aplikasi rasmi MyJPJ atau jpj.gov.my.", "Semak saman dengan nombor kenderaan anda.", "Bayar kompaun dalam aplikasi rasmi.", "Simpan e-resit."],
        "walkin_steps": ["Pergi ke pejabat JPJ terdekat.", "Semak waktu kaunter dahulu.", "Tanya cara menamakan pemandu jika bukan anda."],
        "prepare_online": ["Nombor kad pengenalan", "No. kenderaan", "No. rujukan", "Perbankan dalam talian"],
        "prepare_walkin": ["Kad pengenalan (asal)", "Notis ini", "Dokumen pemilikan kenderaan"],
        "lesson": "Kamera merakam plat, bukan pemandu, jadi notis dihantar kepada pemilik berdaftar yang membayar atau menamakan pemandu.",
    },
    "PTPTN": {
        "online_steps": ["Buka aplikasi rasmi myPTPTN.", "Semak jumlah tunggakan.", "Bayar melalui FPX atau mohon penstrukturan semula / potongan gaji.", "Simpan resit."],
        "walkin_steps": ["Pergi ke kaunter PTPTN terdekat.", "Semak waktu di ptptn.gov.my.", "Tanya tentang jadual bayaran yang disusun semula."],
        "prepare_online": ["Nombor kad pengenalan", "No. akaun pinjaman", "Perbankan dalam talian"],
        "prepare_walkin": ["Kad pengenalan (asal)", "Notis ini", "Slip gaji terkini"],
        "lesson": "Bayaran balik bermula selepas tamat pengajian. Bayaran bulanan yang terlepas ditandakan dan peringatan dihantar sebelum tindakan lebih tegas.",
    },
    "PDRM": {
        "online_steps": ["Semak saman sendiri melalui saluran rasmi PDRM / MyBayar PDRM.", "Jangan guna pautan atau nombor yang diberi dalam mesej yang mencurigakan.", "Laporkan penipuan yang disyaki kepada NSRC 997."],
        "walkin_steps": ["Pergi ke balai polis terdekat.", "Bawa notis dan kad pengenalan anda."],
        "prepare_online": ["Nombor kad pengenalan", "No. kenderaan (jika trafik)"],
        "prepare_walkin": ["Kad pengenalan (asal)", "Notis ini"],
        "lesson": "Notis polis sebenar menyatakan kesalahan tertentu dan menunjuk ke saluran rasmi. Mesej yang menuntut pemindahan wang atau mengugut tangkapan serta-merta ialah penipuan.",
    },
    "COURT": {
        "online_steps": ["Semak kes di laman web rasmi kehakiman.", "Telefon pejabat pendaftar menggunakan nombor di kehakiman.gov.my, bukan nombor dalam surat."],
        "walkin_steps": ["Hadir ke mahkamah yang dinyatakan pada tarikh yang diberi.", "Bawa notis dan kad pengenalan."],
        "prepare_online": ["Nombor kes", "Nombor kad pengenalan"],
        "prepare_walkin": ["Kad pengenalan (asal)", "Notis ini"],
        "lesson": "Mahkamah menghantar notis kepada pihak dan saksi. Anda diminta hadir atau menjawab, bukan membayar kepada orang tidak dikenali.",
    },
    "COUNCIL": {
        "online_steps": ["Bayar melalui portal rasmi majlis anda.", "Simpan resit."],
        "walkin_steps": ["Bayar di kaunter majlis.", "Bawa bil."],
        "prepare_online": ["No. akaun", "Perbankan dalam talian"],
        "prepare_walkin": ["Bil ini"],
        "lesson": "Majlis mengenakan cukai taksiran dua kali setahun untuk membiayai perkhidmatan tempatan.",
    },
    "UTILITY": {
        "online_steps": ["Buka sendiri aplikasi rasmi myTNB atau mytnb.com.my.", "Semak jumlah tunggakan dalam akaun anda.", "Bayar melalui aplikasi atau portal.", "Simpan resit."],
        "walkin_steps": ["Pergi ke kaunter Kedai Tenaga TNB terdekat.", "Bawa notis dan jelaskan tunggakan."],
        "prepare_online": ["No. akaun kontrak", "Perbankan dalam talian"],
        "prepare_walkin": ["Kad pengenalan (asal)", "Notis ini", "Bil elektrik terkini"],
        "lesson": "Di bawah Akta Bekalan Elektrik 1990 (seksyen 38), pemegang lesen boleh memotong bekalan jika bil tidak dijelaskan selepas tempoh notis. Borang A ialah amaran rasmi sebelum itu.",
    },
    "KWSP_PERKESO": {
        "online_steps": ["Log masuk i-Akaun di kwsp.gov.my atau aplikasi rasmi KWSP sendiri.", "Semak jumlah tunggakan.", "Bayar melalui saluran rasmi.", "Simpan resit."],
        "walkin_steps": ["Pergi ke kaunter cawangan KWSP terdekat.", "Bawa notis dan kad pengenalan."],
        "prepare_online": ["Nombor kad pengenalan", "Log masuk i-Akaun", "Perbankan dalam talian"],
        "prepare_walkin": ["Kad pengenalan (asal)", "Notis ini"],
        "lesson": "Majikan mesti membayar caruman KWSP menjelang 15 haribulan setiap bulan (seksyen 43, Akta 452). Bayaran lewat dikenakan caj. KWSP tidak pernah guna ejen WhatsApp atau Telegram dan tidak mengenakan komisen.",
    },
    "BANK": {
        "online_steps": ["Log masuk melalui aplikasi rasmi bank yang anda sudah guna.", "Jangan kongsi TAC atau kata laluan.", "Telefon nombor di belakang kad anda jika tidak pasti."],
        "walkin_steps": ["Pergi ke cawangan dengan kad pengenalan."],
        "prepare_online": ["Aplikasi bank rasmi"],
        "prepare_walkin": ["Kad pengenalan (asal)", "Notis ini"],
        "lesson": "Bank menghantar penyata, notis tunggakan dan pembaharuan. Bank tidak pernah minta TAC atau kata laluan anda.",
    },
}


def localize(issuer: str, src: dict, language: str) -> dict:
    """Registry fields (steps, lists, lesson text) in `language`, falling back to English."""
    out = {k: src[k] for k in ("online_steps", "walkin_steps", "prepare_online", "prepare_walkin")}
    out["lesson_a"] = src["lesson"]["a"]
    if language == "bm" and issuer in BM:
        b = BM[issuer]
        out |= {k: b[k] for k in ("online_steps", "walkin_steps", "prepare_online", "prepare_walkin")}
        out["lesson_a"] = b["lesson"]
    return out
