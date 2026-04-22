# MinikCoder: Vision-Based Jigsaw Puzzle and Drawing Application

Çocukların motor becerilerini ve el-göz koordinasyonunu geliştirmek üzere tasarlanmış, bilgisayarla görü (computer vision) tabanlı interaktif bir eğitim yazılımıdır. MediaPipe ve OpenCV teknolojilerini kullanarak temassız bir kullanıcı deneyimi sunar.

---

## Proje Hakkında Genel Bilgi

Uygulama, kullanıcının el hareketlerini gerçek zamanlı olarak analiz ederek dijital objelerle etkileşime girmesini sağlar. Temel olarak iki ana modda çalışır: Yapboz (Puzzle) modu ve Çizim (Drawing) modu. Kullanıcılar yapboz parçalarını fiziksel bir temas olmadan havada "tut-bırak" hareketleriyle yerleştirir, ardından tamamlanan görsel üzerinde serbest çizim yapabilirler.

---

## Genel İşleyiş Akışı (Workflow)

Uygulamanın operasyonel süreci aşağıdaki aşamalardan oluşur:

1.  **Giriş ve Kalibrasyon:** Uygulama başlatıldığında kamera bağlantısı kurulur ve görüntü ayna efektiyle ekrana yansıtılır. El takibi motoru aktif hale gelir.
2.  **Yapboz Modu (Puzzle Mode):** Ekranın sol tarafında rastgele dağıtılmış yapboz parçaları, sağ tarafında ise parçaların yerleştirileceği hedef silüet alanı bulunur.
    -   **Etkileşim:** İşaret ve baş parmak arasındaki mesafe (pinch) ölçülerek parça tutma işlemi gerçekleştirilir.
    -   **Kilitleme:** Hedef konuma yaklaşan parçalar otomatik olarak (snap-to-grid) yerine kilitlenir.
3.  **Çizim Modu (Drawing Mode):** Tüm yapboz parçaları tamamlandığında sistem otomatik olarak çizim moduna geçer.
    -   Tamamlanan görsel arka plana şablon olarak yerleştirilir.
    -   Kullanıcı işaret parmağını kullanarak tuval üzerinde çizim yapabilir.
4.  **Kutlama ve Sıfırlama:** Çizim aşaması tamamlandığında başarı ekranı görüntülenir ve uygulama başlangıç durumuna döner.

---

## Teknik İçerik ve Özellikler

### Yapboz (Puzzle) Mekaniği
Uygulama, klasik dikdörtgen parçalar yerine karmaşık geometrik yapılara sahip "interlocking" yapboz parçaları üretir.
-   **Dinamik Kenar Üretimi:** Her çalışma için parçalar rastgele girinti ve çıkıntılarla oluşturulur.
-   **Hassasiyet Yönetimi:** MediaPipe el landmarkları üzerinden 21 farklı nokta takip edilerek yüksek hassasiyetli bir tutuş deneyimi sağlanır.
-   **Görsel Geribildirim:** Parçaların kilitlenmesi sırasında neon yeşil parlama efektleri ve hedef alanında silüet rehberliği kullanılır.

### Mevcut Görsel Temalar (Assets)
Sistem içerisinde çocukların ilgisini çekecek yüksek çözünürlüklü aşağıdaki temalar tanımlıdır:
-   **Robot Teması:** Teknolojik ve geometrik formlardan oluşan yapboz seti.
-   **Kedi Teması:** Daha yumuşak hatlara ve renk paketlerine sahip hayvan temalı yapboz seti.

### Kontrol Paneli ve Hover Sistemi
Menü geçişleri ve tema seçimleri için fiziksel tıklama yerine "Hover" (üzerinde bekleme) sistemi entegre edilmiştir. Belirlenen butonun üzerinde 1.2 saniye boyunca elin tutulması işlemi tetikler.

---

## Proje Klasör Yapısı

```text
cocuk_visioun/
│
├── main.py                 # Uygulama ana giriş noktası ve durum yönetimi
├── requirements.txt        # Gerekli Python kütüphaneleri listesi
├── README.md               # Proje dökümantasyonu
│
├── src/                    # Kaynak kod dizini
│   ├── hand_tracker.py     # El takibi ve hareket algılama motoru
│   ├── puzzle_logic.py     # Yapboz oluşturma ve kenetlenme algoritmaları
│   └── drawing_logic.py    # Çizim fırçası ve tuval yönetim mantığı
│
├── assets/                 # Resimler ve görsel materyaller
│   ├── robot.png
│   └── cat.png
│
└── scratch/                # Geçici dosyalar ve test çıktıları
```

---

## Kurulum ve Çalıştırma

### Sistem Gereksinimleri
-   Python 3.10 veya üzeri
-   Yüksek çözünürlüklü web kamera (720p önerilir)
-   Yeterli ışıklandırma koşulları

### Kurulum Adımları
1.  Gerekli paketleri yükleyin:
    ```bash
    pip install -r requirements.txt
    ```
2.  Uygulamayı çalıştırın:
    ```bash
    python main.py
    ```

---

## Yazılım Mimarisi Notları

-   **Görüntü İşleme:** Görüntülerin maskelenmesi ve parça kesim işlemleri için OpenCV NumPy entegrasyonu kullanılır.
-   **Hicivli Ayna Modu:** Kullanıcının el-göz koordinasyonunu stabilize etmek için görüntüler matris seviyesinde yatay olarak çevrilir.
-   **Hız ve Performans:** Düşük gecikme süresi için el takibi işlemleri asenkron olarak değil, her karede optimize edilmiş şekilde işlenir.

---
