[🇹🇷](README_TR.md) [🇬🇧](README.md)

# Pardus Yazı Tipi Yöneticisi

## Giriş
Pardus Yazı Tipi Yöneticisi, Linux kullanıcıları için tasarlanmış, yazı tiplerini kolayca yönetmeyi ve önizlemeyi sağlayan çok yönlü bir uygulamadır.
Bu uygulama, kullanıcıların sisteme yeni yazı tipleri eklemesini, önizlemesini ve mevcut yazı tiplerini yönetmesini sağlar.

## Kurulum

### Önkoşullar
- Sisteminizde `fontconfig` ve Python 3.x'in yüklü olduğundan emin olun.
- GTK 3.0 ve GTK için Python bağlantıları gereklidir.

### Kullanım
- Depoyu klonlayın:

    ```
    git clone https://github.com/pardus/pardus-font-manager.git
    ```

- Uygulamayı başlatmak için şunu çalıştırın:
    `python3 Main.py`

### Arayüz

Ana pencere, sisteminizde bulunan yazı tiplerinin listesini ve seçili yazı tipinin karakter haritasını gösterir:

![Yazı Tipi Listesi](screenshots/font_list.png)

### Yazı Tipi Yönetim Özellikleri
- Sisteme yeni yazı tipleri kolayca eklenebilir.
- Yazı tipleri yüklenmeden önizlenebilir.
- Mevcut yazı tiplerini yönetebilir ve düzenleyebilir.
- Her yazı tipi hakkında detaylı bilgi görüntüleyebilir.

## Geliştirici Notları
`MainWindow.py`, uygulamanın arayüzü için ana dosyadır.
Font önizleme ve karakter haritası işlevleri için `font_charmaps.py` ve `font_viewer.py` kullanılır.

`font_adder.c`, yazı tiplerini sisteme eklemek için paylaşımlı bir kütüphane olarak derlenen C tabanlı bir modüldür.

