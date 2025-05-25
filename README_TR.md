
# Spotify Takip Botu 🎧

Bu program, Spotify kullanıcılarını otomatik olarak takip eden Python tabanlı bir bottur. Takip edilen kullanıcılar yerel bir SQLite veritabanında saklanır.

---

## 🛠 Gereksinimler

### 1. Python
- Python 3.9 veya üzeri kurulu olmalıdır.  
[Python İndir](https://www.python.org/downloads/)

### 2. Gerekli Python Kütüphaneleri

Aşağıdaki komutu çalıştırarak kütüphaneleri yükleyin:

```bash
pip install selenium customtkinter pystray pillow webdriver-manager
```

> Linux kullanıyorsanız `tkinter` ayrı kurulmalıdır:
> ```bash
> sudo apt install python3-tk
> ```

### 3. Chrome ve Otomatik ChromeDriver

- Google Chrome yüklü olmalıdır: [İndir](https://www.google.com/chrome/)
- `webdriver-manager` sayesinde ChromeDriver otomatik yönetilir, manuel indirmeye gerek yoktur.

Kodda aşağıdaki satırları kullanın:

```python
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
```

---

## 🚀 Programı Çalıştırma

Proje klasöründe terminal açarak şu komutu girin:

```bash
python Spotify_Follow_Bot.py
```

---

## 🧾 Kullanım

1. Spotify kullanıcı adı ve şifrenizi girin.
2. Takip etmek istediğiniz kullanıcı ID’sini yazın.
3. Limit ve süre ayarlarını yapın.
4. “Başlat” butonuna tıklayın.

---

## 💾 Veri Yönetimi

- Takip edilenler `followed_users.db` veritabanında saklanır.
- Ayarlar `settings.json` dosyasına kaydedilir.
- Tema ve dil tercihleri `themes.json` ve `lang/*.json` içinde tutulur.

---

## 👨‍💻 Geliştirici

- Geliştirici bilgisi uygulamadaki “Yapımcı” sekmesinde yer alır.
- GitHub profiline doğrudan uygulamadan ulaşılabilir.

---

## ⚠️ Uyarı

Bu bot Spotify kullanım şartlarını ihlal edebilir. Kullanım tamamen sizin sorumluluğunuzdadır.

---
