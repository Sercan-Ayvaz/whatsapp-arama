# 📱 WhatsApp Ekran Görüntüsü Arama

Ekran görüntülerinin (WhatsApp yazışmaları, belgeler, fotoğraflanmış metinler)
içinde **kelime veya cümle arayan** basit bir masaüstü uygulaması.
Resimlerdeki yazıyı OCR ([Tesseract](https://github.com/tesseract-ocr/tesseract))
ile okur; tamamen **çevrimdışı** çalışır, hiçbir dosya internete gönderilmez.

## Özellikler
- Klasördeki (isteğe bağlı alt klasörler dahil) tüm `png / jpg / jpeg / webp / bmp` resimlerde arama
- Türkçe harflere duyarlı değil: `isik` yazınca `IŞIK`, `ışık` ve `işık` bulunur
- Birden fazla kelime yazarsan hepsinin resimde geçtiği sonuçlar listelenir
- İlk tarama yavaş, sonrakiler çok hızlı (OCR sonuçları önbelleğe alınır)
- Sonuca çift tıklayınca resim açılır, aramayı istediğin an iptal edebilirsin

## İndirme

**[➡ En son sürümü buradan indir (Releases)](../../releases/latest)**

### Windows (önerilen: kurulumlu)
1. `WhatsAppArama-Windows-Kurulum.exe` dosyasını indir ve çift tıkla.
2. "İleri"ye basarak kur. Masaüstünde kısayol oluşur.
3. Python, Tesseract veya başka bir şey kurman **gerekmez**, hepsi pakette gelir.

Kurulum istemiyorsan `WhatsAppArama-Windows-Tasinabilir.zip` dosyasını indir,
**sağ tık → Tümünü ayıkla** de, içindeki `WhatsAppArama.exe`'yi çalıştır.

> Windows "PC'nizi korudu" uyarısı gösterirse **Ek bilgi → Yine de çalıştır** de.
> Program imzalı olmadığı için bu uyarı çıkar. Kaynak kod bu depoda açıktır.

### Linux
```bash
sudo apt install tesseract-ocr tesseract-ocr-tur tesseract-ocr-eng
tar -xzf WhatsAppArama-Linux.tar.gz
./WhatsAppArama
```

## Kaynak koddan çalıştırma
```bash
sudo apt install tesseract-ocr tesseract-ocr-tur tesseract-ocr-eng python3-tk
pip install pytesseract pillow
python3 whatsapp-arama.py
```
Windows'ta Tesseract'ı [buradan](https://github.com/UB-Mannheim/tesseract/wiki)
kurman ve Türkçe dil verisini seçmen gerekir.

## Kendin derlemek
GitHub Actions bu depoda hazırdır. `v1.0` gibi bir etiket itildiğinde
Windows ve Linux sürümleri otomatik derlenip **Releases** sayfasına yüklenir:
```bash
git tag v1.0
git push origin v1.0
```

## Lisans
[MIT](LICENSE). Tesseract OCR, Apache 2.0 lisansı ile dağıtılır.
