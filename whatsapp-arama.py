import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pytesseract
from PIL import Image
import os
import sys
import json
import shutil
import threading
import subprocess
import unicodedata

UYGULAMA_ADI = "WhatsAppArama"
UZANTILAR = (".png", ".jpg", ".jpeg", ".webp", ".bmp")


# ---------------------------------------------------------------
# Yardımcı fonksiyonlar
# ---------------------------------------------------------------
def uygulama_klasoru():
    """Çalışan programın bulunduğu klasör (PyInstaller ile de çalışır)."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def tesseract_ayarla():
    """
    Tesseract'ı sırayla şurada arar:
      1) Uygulamanın yanındaki 'tesseract' klasörü (kurulum paketine gömülü)
      2) Sistem PATH'i
      3) Windows'taki yaygın kurulum yolları
    Bulursa True döner.
    """
    ekzeci = "tesseract.exe" if os.name == "nt" else "tesseract"
    adaylar = [
        os.path.join(uygulama_klasoru(), "tesseract", ekzeci),
        os.path.join(os.path.dirname(sys.executable), "tesseract", ekzeci),
    ]
    yol_icinde = shutil.which("tesseract")
    if yol_icinde:
        adaylar.append(yol_icinde)
    if os.name == "nt":
        adaylar += [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]

    for aday in adaylar:
        if os.path.isfile(aday):
            pytesseract.pytesseract.tesseract_cmd = aday
            tessdata = os.path.join(os.path.dirname(aday), "tessdata")
            if os.path.isdir(tessdata):
                os.environ["TESSDATA_PREFIX"] = tessdata
            return True
    return False


def normalize(metin):
    """
    Aramayı Türkçe harflere ve büyük/küçük harfe duyarsız yapar.
    İ, I, ı -> i ; ş, ğ, ü, ö, ç -> s, g, u, o, c
    (OCR sık sık noktaları/aksanları yanlış okuduğu için bu daha güvenilir.)
    """
    metin = metin.replace("İ", "i").replace("I", "i").replace("ı", "i")
    metin = unicodedata.normalize("NFKD", metin.lower())
    return "".join(c for c in metin if not unicodedata.combining(c))


def veri_klasoru():
    if os.name == "nt":
        taban = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        taban = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
    yol = os.path.join(taban, UYGULAMA_ADI)
    os.makedirs(yol, exist_ok=True)
    return yol


def dosyayi_ac(yol):
    if os.name == "nt":
        os.startfile(yol)  # noqa
    elif sys.platform == "darwin":
        subprocess.Popen(["open", yol])
    else:
        subprocess.Popen(["xdg-open", yol])


# ---------------------------------------------------------------
# Uygulama
# ---------------------------------------------------------------
class WhatsAppAramaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WhatsApp Ekran Görüntüsü Arama")
        self.root.geometry("700x600")
        self.root.configure(bg="#f0f2f5")

        self.klasor = ""
        self.resimler = []
        self.sonuclar = []
        self.iptal = threading.Event()
        self.calisiyor = False

        self.cache_yolu = os.path.join(veri_klasoru(), "ocr_onbellek.json")
        self.cache = self._cache_yukle()

        self.dil = "eng"
        self.baslangic_kontrolu()
        self._arayuz_olustur()

    # ---------- Başlangıç kontrolü ----------
    def baslangic_kontrolu(self):
        if not tesseract_ayarla():
            messagebox.showerror(
                "Tesseract bulunamadı",
                "OCR motoru (Tesseract) bulunamadı.\n\n"
                "Programı yeniden kurmayı deneyin. Sorun devam ederse "
                "program geliştiricisine bildirin.",
            )
            self.root.destroy()
            sys.exit(1)

        try:
            diller = pytesseract.get_languages(config="")
        except Exception:
            diller = []

        if "tur" in diller and "eng" in diller:
            self.dil = "tur+eng"
        elif "tur" in diller:
            self.dil = "tur"
        elif "eng" in diller:
            self.dil = "eng"
            messagebox.showwarning(
                "Türkçe dil dosyası yok",
                "Türkçe OCR verisi (tur.traineddata) bulunamadı. "
                "Sadece İngilizce okunacak; Türkçe harfler hatalı çıkabilir.",
            )
        else:
            messagebox.showerror(
                "Dil verisi yok",
                "Tesseract dil dosyaları bulunamadı (tessdata klasörü).",
            )
            self.root.destroy()
            sys.exit(1)

    # ---------- Önbellek ----------
    def _cache_yukle(self):
        try:
            with open(self.cache_yolu, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _cache_kaydet(self):
        try:
            gecici = self.cache_yolu + ".tmp"
            with open(gecici, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False)
            os.replace(gecici, self.cache_yolu)
        except Exception as e:
            print(f"Önbellek kaydedilemedi: {e}")

    def _cache_anahtari(self, yol):
        st = os.stat(yol)
        return f"{yol}|{st.st_size}|{int(st.st_mtime)}|{self.dil}"

    # ---------- Arayüz ----------
    def _arayuz_olustur(self):
        tk.Label(
            self.root, text="📱 WhatsApp Ekran Görüntüsü Arama",
            font=("Arial", 16, "bold"), bg="#f0f2f5", fg="#075e54"
        ).pack(pady=10)

        klasor_frame = tk.Frame(self.root, bg="#f0f2f5")
        klasor_frame.pack(pady=5, padx=20, fill="x")

        self.klasor_label = tk.Label(
            klasor_frame, text="Klasör seçilmedi",
            bg="white", fg="#666", anchor="w", padx=10,
            relief="sunken", bd=1
        )
        self.klasor_label.pack(side="left", fill="x", expand=True, ipady=6)

        self.klasor_btn = tk.Button(
            klasor_frame, text="📁 Klasör Seç", command=self.klasor_sec,
            bg="#25d366", fg="white", font=("Arial", 10, "bold"),
            relief="flat", padx=15
        )
        self.klasor_btn.pack(side="left", padx=5)

        self.alt_klasor = tk.BooleanVar(value=False)
        tk.Checkbutton(
            self.root, text="Alt klasörleri de tara", variable=self.alt_klasor,
            command=self._resimleri_say, bg="#f0f2f5", font=("Arial", 9)
        ).pack(anchor="w", padx=20)

        arama_frame = tk.Frame(self.root, bg="#f0f2f5")
        arama_frame.pack(pady=10, padx=20, fill="x")

        tk.Label(
            arama_frame, text="Aranacak kelime:",
            bg="#f0f2f5", font=("Arial", 11)
        ).pack(side="left", padx=5)

        self.arama_entry = tk.Entry(
            arama_frame, font=("Arial", 12), relief="sunken", bd=2
        )
        self.arama_entry.pack(side="left", fill="x", expand=True, padx=5, ipady=4)
        self.arama_entry.bind("<Return>", lambda e: self.aramaya_basla())

        btn_frame = tk.Frame(self.root, bg="#f0f2f5")
        btn_frame.pack(pady=5)

        self.arama_btn = tk.Button(
            btn_frame, text="🔍 ARA", command=self.aramaya_basla,
            bg="#075e54", fg="white", font=("Arial", 12, "bold"),
            relief="flat", padx=30, pady=6
        )
        self.arama_btn.pack(side="left", padx=5)

        self.iptal_btn = tk.Button(
            btn_frame, text="⛔ İptal", command=self.iptal_et,
            bg="#c0392b", fg="white", font=("Arial", 12, "bold"),
            relief="flat", padx=20, pady=6, state="disabled"
        )
        self.iptal_btn.pack(side="left", padx=5)

        self.ilerleme = ttk.Progressbar(self.root, length=600, mode="determinate")
        self.ilerleme.pack(pady=5)

        self.durum_label = tk.Label(
            self.root, text="Hazır", bg="#f0f2f5", fg="#666",
            font=("Arial", 9)
        )
        self.durum_label.pack()

        tk.Label(
            self.root, text="📋 Bulunan Sonuçlar:",
            bg="#f0f2f5", font=("Arial", 11, "bold"), anchor="w"
        ).pack(padx=20, pady=(10, 0), fill="x")

        sonuc_frame = tk.Frame(self.root)
        sonuc_frame.pack(padx=20, pady=5, fill="both", expand=True)

        scrollbar = tk.Scrollbar(sonuc_frame)
        scrollbar.pack(side="right", fill="y")

        self.sonuc_listesi = tk.Listbox(
            sonuc_frame, yscrollcommand=scrollbar.set,
            font=("Arial", 10), selectbackground="#25d366"
        )
        self.sonuc_listesi.pack(side="left", fill="both", expand=True)
        self.sonuc_listesi.bind("<Double-Button-1>", self.resmi_ac)
        scrollbar.config(command=self.sonuc_listesi.yview)

        tk.Label(
            self.root,
            text="💡 İpucu: Sonuca çift tıklayarak resmi açabilirsin. "
                 "İlk tarama yavaştır, sonraki aramalar çok hızlıdır.",
            bg="#f0f2f5", fg="#888", font=("Arial", 8)
        ).pack(pady=5)

    # ---------- Klasör / resim listesi ----------
    def klasor_sec(self):
        klasor = filedialog.askdirectory(
            title="Ekran görüntülerinin olduğu klasörü seç"
        )
        if klasor:
            self.klasor = klasor
            self.klasor_label.config(text=klasor, fg="#000")
            self._resimleri_say()

    def _resimleri_say(self):
        if not self.klasor:
            return
        bulunan = set()
        try:
            if self.alt_klasor.get():
                for kok, _, dosyalar in os.walk(self.klasor):
                    for d in dosyalar:
                        if d.lower().endswith(UZANTILAR):
                            bulunan.add(os.path.join(kok, d))
            else:
                for d in os.listdir(self.klasor):
                    tam = os.path.join(self.klasor, d)
                    if os.path.isfile(tam) and d.lower().endswith(UZANTILAR):
                        bulunan.add(tam)
        except Exception as e:
            messagebox.showerror("Hata", f"Klasör okunamadı:\n{e}")
            return

        self.resimler = sorted(bulunan)
        self.durum_label.config(text=f"✅ {len(self.resimler)} resim bulundu")

    # ---------- Arama ----------
    def aramaya_basla(self):
        if self.calisiyor:
            return
        if not self.klasor:
            messagebox.showwarning("Uyarı", "Lütfen önce bir klasör seçin!")
            return

        kelime = self.arama_entry.get().strip()
        if not kelime:
            messagebox.showwarning("Uyarı", "Lütfen aranacak kelimeyi yazın!")
            return

        if not self.resimler:
            messagebox.showwarning("Uyarı", "Seçili klasörde resim bulunamadı!")
            return

        self.calisiyor = True
        self.iptal.clear()
        self.arama_btn.config(state="disabled", text="⏳ Aranıyor...")
        self.iptal_btn.config(state="normal")
        self.klasor_btn.config(state="disabled")
        self.sonuc_listesi.delete(0, tk.END)
        self.sonuclar = []
        self.ilerleme["maximum"] = len(self.resimler)
        self.ilerleme["value"] = 0

        threading.Thread(
            target=self._arama_islemi, args=(kelime, list(self.resimler)),
            daemon=True
        ).start()

    def iptal_et(self):
        self.iptal.set()
        self.iptal_btn.config(state="disabled")
        self.durum_label.config(text="İptal ediliyor...")

    def _arama_islemi(self, kelime, resimler):
        toplam = len(resimler)
        aranan = normalize(kelime).split()
        hata_sayisi = 0
        degisti = False

        for i, yol in enumerate(resimler, 1):
            if self.iptal.is_set():
                break
            try:
                anahtar = self._cache_anahtari(yol)
                metin = self.cache.get(anahtar)
                if metin is None:
                    with Image.open(yol) as img:
                        metin = pytesseract.image_to_string(img, lang=self.dil)
                    self.cache[anahtar] = metin
                    degisti = True

                norm_metin = normalize(metin)
                if all(k in norm_metin for k in aranan):
                    eslesen = ""
                    for satir in metin.split("\n"):
                        if any(k in normalize(satir) for k in aranan):
                            eslesen = satir.strip()[:80]
                            break
                    self.root.after(
                        0, lambda y=yol, s=eslesen: self._sonuc_ekle(y, s)
                    )
            except Exception as e:
                hata_sayisi += 1
                print(f"Hata: {yol} - {e}")

            # Her 25 resimde bir önbelleği kaydet (kapanırsa emek kaybolmasın)
            if degisti and i % 25 == 0:
                self._cache_kaydet()
                degisti = False

            self.root.after(0, lambda v=i, t=toplam: self._ilerleme_guncelle(v, t))

        if degisti:
            self._cache_kaydet()

        iptal_edildi = self.iptal.is_set()
        self.root.after(0, lambda: self._arama_bitti(iptal_edildi, hata_sayisi))

    # ---------- Arayüz güncellemeleri (ana thread) ----------
    def _sonuc_ekle(self, tam_yol, satir):
        self.sonuclar.append(tam_yol)
        gosterim = f"✅ {os.path.basename(tam_yol)}"
        if satir:
            gosterim += f"  →  \"{satir}\""
        self.sonuc_listesi.insert(tk.END, gosterim)
        self.sonuc_listesi.itemconfig(tk.END, {"bg": "#dcf8c6"})

    def _ilerleme_guncelle(self, mevcut, toplam):
        self.ilerleme["value"] = mevcut
        self.durum_label.config(text=f"⏳ Taranıyor: {mevcut}/{toplam}")

    def _arama_bitti(self, iptal_edildi, hata_sayisi):
        self.calisiyor = False
        self.arama_btn.config(state="normal", text="🔍 ARA")
        self.iptal_btn.config(state="disabled")
        self.klasor_btn.config(state="normal")

        adet = len(self.sonuclar)
        if iptal_edildi:
            self.durum_label.config(text=f"⛔ İptal edildi. {adet} sonuç bulundu.")
            return

        ek = f" ({hata_sayisi} resim okunamadı)" if hata_sayisi else ""
        self.durum_label.config(text=f"✅ Tamamlandı! {adet} sonuç bulundu.{ek}")

        if adet == 0:
            messagebox.showinfo(
                "Sonuç", "Hiçbir görüntüde bu kelime bulunamadı." + ek
            )
        else:
            messagebox.showinfo("Sonuç", f"{adet} görüntüde bulundu!{ek}")

    def resmi_ac(self, event):
        secili = self.sonuc_listesi.curselection()
        if not secili:
            return
        index = secili[0]
        if index < len(self.sonuclar):
            try:
                dosyayi_ac(self.sonuclar[index])
            except Exception as e:
                messagebox.showerror("Hata", f"Resim açılamadı:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = WhatsAppAramaApp(root)
    root.mainloop()
