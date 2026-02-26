import os
import json
import shutil
import time
import urllib.request
import urllib.parse
import re
import sys
import threading
import concurrent.futures
import customtkinter as ctk
from tkinter import messagebox, filedialog

# ==============================================================================
#  CONFIGURAÇÕES GLOBAIS E VARIÁVEIS DE ESTADO
# ==============================================================================
CONFIG = {
    "GAME_DIR": "",
    "TOOL_DIR": "",
    "BACKUP_DIR": "",
    "OUTPUT_DIR": "",
    "CACHE_FILE": "",
    "TARGET_LANG": "pt",
    "UI_LANG": "pt"
}

MODO_EXTRACAO = False
textos_coletados = set()
memoria = {}

# As 15 linguagens (sem o inglês)
LANGUAGES = {
    "Português (Brasil)": {"code": "pt", "ui": "pt"},
    "Español": {"code": "es", "ui": "es"},
    "Français": {"code": "fr", "ui": "fr"},
    "Deutsch": {"code": "de", "ui": "de"},
    "Italiano": {"code": "it", "ui": "it"},
    "Русский": {"code": "ru", "ui": "ru"},
    "简体中文": {"code": "zh-CN", "ui": "zh"},
    "日本語": {"code": "ja", "ui": "ja"},
    "한국어": {"code": "ko", "ui": "ko"},
    "العربية": {"code": "ar", "ui": "ar"},
    "हिन्दी": {"code": "hi", "ui": "hi"},
    "Türkçe": {"code": "tr", "ui": "tr"},
    "Tiếng Việt": {"code": "vi", "ui": "vi"},
    "Polski": {"code": "pl", "ui": "pl"},
    "Bahasa Indonesia": {"code": "id", "ui": "id"}
}

# Dicionário Massivo de Localização Total
UI_TEXTS = {
    # Títulos e Botões Iniciais
    "lbl_select_lang": {
        "pt": "Selecione o Idioma / Target Language", "es": "Seleccione el Idioma / Target Language", "fr": "Sélectionnez la Langue / Target Language",
        "de": "Sprache wählen / Target Language", "it": "Seleziona la Lingua / Target Language", "ru": "Выберите язык / Target Language",
        "zh": "选择语言 / Target Language", "ja": "言語を選択 / Target Language", "ko": "언어 선택 / Target Language",
        "ar": "اختر اللغة / Target Language", "hi": "भाषा चुनें / Target Language", "tr": "Dili Seçin / Target Language",
        "vi": "Chọn Ngôn Ngữ / Target Language", "pl": "Wybierz Język / Target Language", "id": "Pilih Bahasa / Target Language"
    },
    "btn_start_sys": {
        "pt": "INICIAR SISTEMA", "es": "INICIAR SISTEMA", "fr": "DÉMARRER LE SYSTÈME", "de": "SYSTEM STARTEN", "it": "AVVIA SISTEMA",
        "ru": "ЗАПУСТИТЬ СИСТЕМУ", "zh": "启动系统", "ja": "システムを起動", "ko": "시스템 시작", "ar": "بدء النظام",
        "hi": "सिस्टम शुरू करें", "tr": "SİSTEMİ BAŞLAT", "vi": "KHỞI ĐỘNG HỆ THỐNG", "pl": "URUCHOM SYSTEM", "id": "MULAI SISTEM"
    },
    "header_title": {
        "pt": "MESTRE TRADUTOR RPG MAKER - v6.0", "es": "MAESTRO TRADUCTOR RPG MAKER - v6.0", "fr": "MAÎTRE TRADUCTEUR RPG MAKER - v6.0",
        "de": "RPG MAKER ÜBERSETZER-MEISTER - v6.0", "it": "MAESTRO TRADUTTORE RPG MAKER - v6.0", "ru": "МАСТЕР ПЕРЕВОДЧИК RPG MAKER - v6.0",
        "zh": "RPG MAKER 翻译大师 - v6.0", "ja": "RPGツクール 翻訳マスター - v6.0", "ko": "RPG MAKER 번역 마스터 - v6.0",
        "ar": "سيد مترجم RPG MAKER - الإصدار 6.0", "hi": "RPG मेकर मास्टर ट्रांसलेटर - v6.0", "tr": "RPG MAKER ÇEVİRİ USTASI - v6.0",
        "vi": "BẬC THẦY DỊCH THUẬT RPG MAKER - v6.0", "pl": "MISTRZ TŁUMACZ RPG MAKER - v6.0", "id": "MASTER PENERJEMAH RPG MAKER - v6.0"
    },
    
    # Menu Principal
    "menu_backup": {
        "pt": "1. FAZER BACKUP", "es": "1. HACER COPIA DE SEGURIDAD", "fr": "1. FAIRE UNE SAUVEGARDE", "de": "1. BACKUP ERSTELLEN",
        "it": "1. ESEGUI BACKUP", "ru": "1. СОЗДАТЬ РЕЗЕРВНУЮ КОПИЮ", "zh": "1. 制作备份", "ja": "1. バックアップを作成",
        "ko": "1. 백업 만들기", "ar": "1. إنشاء نسخة احتياطية", "hi": "1. बैकअप बनाएँ", "tr": "1. YEDEKLE",
        "vi": "1. TẠO BẢN SAO LƯU", "pl": "1. ZRÓB KOPIĘ ZAPASOWĄ", "id": "1. BUAT CADANGAN"
    },
    "desc_backup": {
        "pt": "Cria uma cópia de segurança do jogo original.", "es": "Crea una copia de seguridad del juego original.", "fr": "Crée une copie de sécurité du jeu original.",
        "de": "Erstellt eine Sicherheitskopie des Originalspiels.", "it": "Crea una copia di sicurezza del gioco originale.", "ru": "Создает резервную копию оригинальной игры.",
        "zh": "创建原始游戏的备份。", "ja": "オリジナルゲームのバックアップを作成します。", "ko": "원본 게임의 백업을 만듭니다.",
        "ar": "يقوم بإنشاء نسخة احتياطية من اللعبة الأصلية.", "hi": "मूल गेम की एक बैकअप कॉपी बनाता है।", "tr": "Orijinal oyunun bir yedeğini oluşturur.",
        "vi": "Tạo bản sao lưu của trò chơi gốc.", "pl": "Tworzy kopię zapasową oryginalnej gry.", "id": "Membuat salinan cadangan dari game asli."
    },
    "menu_translate": {
        "pt": "2. INICIAR TRADUÇÃO", "es": "2. INICIAR TRADUCCIÓN", "fr": "2. DÉMARRER LA TRADUCTION", "de": "2. ÜBERSETZUNG STARTEN",
        "it": "2. AVVIA TRADUZIONE", "ru": "2. НАЧАТЬ ПЕРЕВОД", "zh": "2. 开始翻译", "ja": "2. 翻訳を開始",
        "ko": "2. 번역 시작", "ar": "2. بدء الترجمة", "hi": "2. अनुवाद शुरू करें", "tr": "2. ÇEVİRİYİ BAŞLAT",
        "vi": "2. BẮT ĐẦU DỊCH", "pl": "2. ROZPOCZNIJ TŁUMACZENIE", "id": "2. MULAI TERJEMAHAN"
    },
    "desc_translate": {
        "pt": "Traduz os arquivos usando a memória e a internet.", "es": "Traduce los archivos usando la memoria y la internet.", "fr": "Traduit les fichiers en utilisant la mémoire et Internet.",
        "de": "Übersetzt Dateien mit Speicher und Internet.", "it": "Traduce i file usando la memoria e internet.", "ru": "Переводит файлы, используя память и интернет.",
        "zh": "使用内存和互联网翻译文件。", "ja": "メモリとインターネットを使用してファイルを翻訳します。", "ko": "메모리와 인터넷을 사용하여 파일을 번역합니다.",
        "ar": "يترجم الملفات باستخدام الذاكرة والإنترنت.", "hi": "मेमोरी और इंटरनेट का उपयोग करके फ़ाइलों का अनुवाद करता है।", "tr": "Hafıza ve interneti kullanarak dosyaları çevirir.",
        "vi": "Dịch các tập tin bằng bộ nhớ và internet.", "pl": "Tłumaczy pliki za pomocą pamięci i internetu.", "id": "Menerjemahkan file menggunakan memori dan internet."
    },
    "menu_install": {
        "pt": "3. APLICAR NO JOGO", "es": "3. APLICAR AL JUEGO", "fr": "3. APPLIQUER AU JEU", "de": "3. IM SPIEL ANWENDEN",
        "it": "3. APPLICA AL GIOCO", "ru": "3. ПРИМЕНИТЬ В ИГРЕ", "zh": "3. 应用到游戏", "ja": "3. ゲームに適用",
        "ko": "3. 게임에 적용", "ar": "3. تطبيق على اللعبة", "hi": "3. गेम में लागू करें", "tr": "3. OYUNA UYGULA",
        "vi": "3. ÁP DỤNG VÀO TRÒ CHƠI", "pl": "3. ZASTOSUJ W GRZE", "id": "3. TERAPKAN KE GAME"
    },
    "desc_install": {
        "pt": "Substitui os arquivos originais pelos traduzidos.", "es": "Reemplaza los archivos originales por los traducidos.", "fr": "Remplace les fichiers originaux par les fichiers traduits.",
        "de": "Ersetzt Originaldateien durch übersetzte.", "it": "Sostituisce i file originali con quelli tradotti.", "ru": "Заменяет оригинальные файлы переведенными.",
        "zh": "将原始文件替换为翻译后的文件。", "ja": "元のファイルを翻訳されたファイルに置き換えます。", "ko": "원본 파일을 번역된 파일로 바꿉니다.",
        "ar": "يستبدل الملفات الأصلية بالملفات المترجمة.", "hi": "मूल फ़ाइलों को अनुवादित फ़ाइलों से बदल देता है।", "tr": "Orijinal dosyaları çevrilmiş olanlarla değiştirir.",
        "vi": "Thay thế các tệp gốc bằng các tệp đã dịch.", "pl": "Zastępuje oryginalne pliki przetłumaczonymi.", "id": "Mengganti file asli dengan yang diterjemahkan."
    },
    "menu_font": {
        "pt": "4. AJUSTAR FONTE", "es": "4. AJUSTAR FUENTE", "fr": "4. AJUSTER LA POLICE", "de": "4. SCHRIFTART ANPASSEN",
        "it": "4. REGOLA CARATTERE", "ru": "4. НАСТРОИТЬ ШРИФТ", "zh": "4. 调整字体", "ja": "4. フォントを調整",
        "ko": "4. 글꼴 조정", "ar": "4. ضبط الخط", "hi": "4. फ़ॉन्ट समायोजित करें", "tr": "4. YAZI TİPİNİ AYARLA",
        "vi": "4. ĐIỀU CHỈNH PHÔNG CHỮ", "pl": "4. DOSTOSUJ CZCIONKĘ", "id": "4. SESUAIKAN FONT"
    },
    "desc_font": {
        "pt": "Reduz a letra para caber nos balões de texto.", "es": "Reduce la letra para caber en los cuadros de texto.", "fr": "Réduit la lettre pour tenir dans les bulles de texte.",
        "de": "Verkleinert die Schrift für die Textfelder.", "it": "Riduce la lettera per adattarsi alle caselle di testo.", "ru": "Уменьшает шрифт, чтобы он помещался в текстовых полях.",
        "zh": "缩小字体以适应文本框。", "ja": "テキストボックスに収まるようにフォントを小さくします。", "ko": "텍스트 상자에 맞게 글꼴을 줄입니다.",
        "ar": "يصغر الخط ليلائم مربعات النص.", "hi": "टेक्स्ट बॉक्स में फिट होने के लिए फ़ॉन्ट को छोटा करता है।", "tr": "Metin kutularına sığması için yazı tipini küçültür.",
        "vi": "Thu nhỏ chữ để vừa với hộp văn bản.", "pl": "Zmniejsza czcionkę, aby zmieściła się w polach tekstowych.", "id": "Mengecilkan font agar muat di kotak teks."
    },
    
    # Pop-ups e Alertas
    "font_title": {
        "pt": "Ajuste de Fonte", "es": "Ajuste de Fuente", "fr": "Ajustement de la Police", "de": "Schriftartanpassung",
        "it": "Regolazione Carattere", "ru": "Настройка шрифта", "zh": "字体调整", "ja": "フォント調整", "ko": "글꼴 조정",
        "ar": "تعديل الخط", "hi": "फ़ॉन्ट समायोजन", "tr": "Yazı Tipi Ayarı", "vi": "Điều chỉnh phông chữ", "pl": "Dostosowanie czcionki", "id": "Penyesuaian Font"
    },
    "font_warning": {
        "pt": "O idioma traduzido pode ter palavras mais longas, fazendo com que o jogo corte os textos na tela.\n\nRecomendamos diminuir o tamanho da fonte. O ideal sugerido é 18, mas digite outro valor abaixo se desejar:",
        "es": "El idioma traducido puede tener palabras más largas, haciendo que el juego corte los textos.\n\nRecomendamos disminuir el tamaño de la fuente. El ideal sugerido es 18, pero ingrese otro valor si lo desea:",
        "fr": "La langue traduite peut avoir des mots plus longs, ce qui coupe les textes à l'écran.\n\nNous recommandons de réduire la police. L'idéal est 18, mais entrez une autre valeur ci-dessous si vous le souhaitez :",
        "de": "Die übersetzte Sprache kann längere Wörter haben, wodurch der Text abgeschnitten wird.\n\nWir empfehlen, die Schriftgröße zu verringern. Ideal ist 18, aber Sie können unten einen anderen Wert eingeben:",
        "it": "La lingua tradotta può avere parole più lunghe, causando il taglio dei testi.\n\nConsigliamo di ridurre la dimensione del carattere. L'ideale suggerito è 18, ma inserisci un altro valore se lo desideri:",
        "ru": "В переведенном языке слова могут быть длиннее, из-за чего текст обрезается.\n\nМы рекомендуем уменьшить размер шрифта. Идеально 18, но вы можете ввести другое значение ниже:",
        "zh": "翻译后的语言可能会有更长的单词，导致游戏截断屏幕上的文本。\n\n我们建议减小字体大小。建议的理想值为18，但如果您愿意，可以在下面输入其他值：",
        "ja": "翻訳された言語は単語が長くなる可能性があり、ゲーム画面のテキストが途切れる原因となります。\n\nフォントサイズを小さくすることをお勧めします。推奨は18ですが、必要に応じて別の値を入力してください:",
        "ko": "번역된 언어는 단어가 더 길어 화면의 텍스트가 잘릴 수 있습니다.\n\n글꼴 크기를 줄이는 것이 좋습니다. 권장 크기는 18이지만 원하는 경우 아래에 다른 값을 입력하세요:",
        "ar": "قد تحتوي اللغة المترجمة على كلمات أطول، مما يتسبب في قطع النصوص على الشاشة.\n\nنوصي بتقليل حجم الخط. الحجم المثالي هو 18، ولكن يمكنك إدخال قيمة أخرى أدناه:",
        "hi": "अनुवादित भाषा में लंबे शब्द हो सकते हैं, जिससे गेम स्क्रीन पर टेक्स्ट कट सकता है।\n\nहम फ़ॉन्ट का आकार कम करने की सलाह देते हैं। आदर्श 18 है, लेकिन आप नीचे कोई अन्य मान दर्ज कर सकते हैं:",
        "tr": "Çevrilen dil daha uzun kelimelere sahip olabilir ve oyunun ekrandaki metni kesmesine neden olabilir.\n\nYazı tipi boyutunu küçültmenizi öneririz. Önerilen ideal değer 18'dir, ancak isterseniz aşağıya başka bir değer girebilirsiniz:",
        "vi": "Ngôn ngữ được dịch có thể có các từ dài hơn, khiến trò chơi cắt bỏ văn bản trên màn hình.\n\nChúng tôi khuyên bạn nên giảm kích thước phông chữ. Mức lý tưởng được đề xuất là 18, nhưng bạn có thể nhập một giá trị khác bên dưới:",
        "pl": "Przetłumaczony język może mieć dłuższe słowa, co powoduje ucinanie tekstów na ekranie.\n\nZalecamy zmniejszenie rozmiaru czcionki. Sugerowany ideał to 18, ale jeśli chcesz, wpisz inną wartość poniżej:",
        "id": "Bahasa terjemahan mungkin memiliki kata-kata yang lebih panjang, menyebabkan game memotong teks di layar.\n\nKami sarankan untuk mengurangi ukuran font. Idealnya adalah 18, namun Anda dapat memasukkan nilai lain di bawah ini:"
    },
    "btn_confirm": {
        "pt": "Confirmar", "es": "Confirmar", "fr": "Confirmer", "de": "Bestätigen", "it": "Conferma", "ru": "Подтвердить",
        "zh": "确认", "ja": "確認", "ko": "확인", "ar": "تأكيد", "hi": "पुष्टि करें", "tr": "Onayla", "vi": "Xác nhận", "pl": "Potwierdź", "id": "Konfirmasi"
    },
    "msg_error_title": {
        "pt": "Erro", "es": "Error", "fr": "Erreur", "de": "Fehler", "it": "Errore", "ru": "Ошибка",
        "zh": "错误", "ja": "エラー", "ko": "오류", "ar": "خطأ", "hi": "त्रुटि", "tr": "Hata", "vi": "Lỗi", "pl": "Błąd", "id": "Kesalahan"
    },
    "msg_error_num": {
        "pt": "Por favor, digite apenas números inteiros.", "es": "Por favor, ingrese solo números enteros.", "fr": "Veuillez entrer uniquement des nombres entiers.",
        "de": "Bitte geben Sie nur ganze Zahlen ein.", "it": "Si prega di inserire solo numeri interi.", "ru": "Пожалуйста, введите только целые числа.",
        "zh": "请输入整数。", "ja": "整数のみを入力してください。", "ko": "정수만 입력하세요.", "ar": "الرجاء إدخال أرقام صحيحة فقط.",
        "hi": "कृपया केवल पूर्णांक दर्ज करें।", "tr": "Lütfen sadece tam sayı girin.", "vi": "Vui lòng chỉ nhập số nguyên.",
        "pl": "Wprowadź tylko liczby całkowite.", "id": "Harap masukkan angka bulat saja."
    },
    "msg_confirm_title": {
        "pt": "Confirmar", "es": "Confirmar", "fr": "Confirmer", "de": "Bestätigen", "it": "Conferma", "ru": "Подтвердить",
        "zh": "确认", "ja": "確認", "ko": "확인", "ar": "تأكيد", "hi": "पुष्टि करें", "tr": "Onayla", "vi": "Xác nhận", "pl": "Potwierdź", "id": "Konfirmasi"
    },
    "msg_confirm_install": {
        "pt": "Isso substituirá os arquivos do jogo. Continuar?", "es": "Esto reemplazará los archivos del juego. ¿Continuar?", "fr": "Cela remplacera les fichiers du jeu. Continuer ?",
        "de": "Dadurch werden Spieldateien ersetzt. Fortfahren?", "it": "Questo sostituirà i file di gioco. Continuare?", "ru": "Это заменит файлы игры. Продолжить?",
        "zh": "这将替换游戏文件。继续吗？", "ja": "これによりゲームファイルが置き換えられます。続行しますか？", "ko": "이로 인해 게임 파일이 바뀝니다. 계속하시겠습니까?",
        "ar": "سيؤدي هذا إلى استبدال ملفات اللعبة. متابعة؟", "hi": "यह गेम फ़ाइलों को बदल देगा। जारी रखें?", "tr": "Bu, oyun dosyalarını değiştirecek. Devam edilsin mi?",
        "vi": "Thao tác này sẽ thay thế các tệp trò chơi. Tiếp tục?", "pl": "To zastąpi pliki gry. Kontynuować?", "id": "Ini akan mengganti file game. Lanjutkan?"
    },
    "msg_select_folder": {
        "pt": "Selecione a pasta do jogo", "es": "Selecciona la carpeta del juego", "fr": "Sélectionnez le dossier du jeu", "de": "Wählen Sie den Spieleordner",
        "it": "Seleziona la cartella del gioco", "ru": "Выберите папку с игрой", "zh": "选择游戏文件夹", "ja": "ゲームフォルダを選択",
        "ko": "게임 폴더 선택", "ar": "حدد مجلد اللعبة", "hi": "गेम फ़ोल्डर चुनें", "tr": "Oyun klasörünü seçin",
        "vi": "Chọn thư mục trò chơi", "pl": "Wybierz folder gry", "id": "Pilih folder game"
    },
    
    # Textos do LOG - CONFIGURAÇÃO
    "log_init_config": {
        "pt": "Iniciando configuração...", "es": "Iniciando configuración...", "fr": "Démarrage de la configuration...", "de": "Konfiguration wird gestartet...",
        "it": "Avvio configurazione...", "ru": "Запуск конфигурации...", "zh": "开始配置...", "ja": "構成を開始しています...",
        "ko": "구성 시작...", "ar": "بدء التكوين...", "hi": "कॉन्फ़िगरेशन शुरू कर रहा है...", "tr": "Yapılandırma başlatılıyor...",
        "vi": "Bắt đầu cấu hình...", "pl": "Uruchamianie konfiguracji...", "id": "Memulai konfigurasi..."
    },
    "log_game_found": {
        "pt": "[AUTO] Jogo encontrado em:", "es": "[AUTO] Juego encontrado en:", "fr": "[AUTO] Jeu trouvé à :", "de": "[AUTO] Spiel gefunden in:",
        "it": "[AUTO] Gioco trovato in:", "ru": "[АВТО] Игра найдена в:", "zh": "[自动] 发现游戏：", "ja": "[自動] ゲームが見つかりました:",
        "ko": "[자동] 게임 발견:", "ar": "[تلقائي] تم العثور على اللعبة في:", "hi": "[ऑटो] गेम यहाँ मिला:", "tr": "[OTO] Oyun şurada bulundu:",
        "vi": "[TỰ ĐỘNG] Trò chơi được tìm thấy tại:", "pl": "[AUTO] Gra znaleziona w:", "id": "[AUTO] Game ditemukan di:"
    },
    "log_game_not_found": {
        "pt": "Jogo não detectado. Selecione a pasta...", "es": "Juego no detectado. Selecciona la carpeta...", "fr": "Jeu non détecté. Sélectionnez le dossier...",
        "de": "Spiel nicht erkannt. Wählen Sie den Ordner...", "it": "Gioco non rilevato. Seleziona la cartella...", "ru": "Игра не обнаружена. Выберите папку...",
        "zh": "未检测到游戏。请选择文件夹...", "ja": "ゲームが検出されません。フォルダを選択してください...", "ko": "게임을 감지할 수 없습니다. 폴더를 선택하세요...",
        "ar": "لم يتم اكتشاف اللعبة. حدد المجلد...", "hi": "गेम का पता नहीं चला। फ़ोल्डर चुनें...", "tr": "Oyun algılanmadı. Klasörü seçin...",
        "vi": "Không phát hiện trò chơi. Chọn thư mục...", "pl": "Gra nie została wykryta. Wybierz folder...", "id": "Game tidak terdeteksi. Pilih folder..."
    },
    "log_game_selected": {
        "pt": "[OK] Jogo selecionado:", "es": "[OK] Juego seleccionado:", "fr": "[OK] Jeu sélectionné :", "de": "[OK] Spiel ausgewählt:",
        "it": "[OK] Gioco selezionato:", "ru": "[ОК] Игра выбрана:", "zh": "[OK] 已选游戏：", "ja": "[OK] ゲームが選択されました:",
        "ko": "[OK] 게임 선택됨:", "ar": "[موافق] اللعبة المحددة:", "hi": "[OK] गेम चुना गया:", "tr": "[TAMAM] Oyun seçildi:",
        "vi": "[OK] Trò chơi đã chọn:", "pl": "[OK] Wybrano grę:", "id": "[OK] Game yang dipilih:"
    },
    "log_invalid_folder": {
        "pt": "[ERRO] Pasta inválida ou sem pasta 'data'.", "es": "[ERROR] Carpeta inválida o falta la carpeta 'data'.", "fr": "[ERREUR] Dossier invalide ou dossier 'data' manquant.",
        "de": "[FEHLER] Ungültiger Ordner oder fehlender 'data'-Ordner.", "it": "[ERRORE] Cartella non valida o cartella 'data' mancante.", "ru": "[ОШИБКА] Неверная папка или отсутствует папка 'data'.",
        "zh": "[错误] 无效文件夹或缺少 'data' 文件夹。", "ja": "[エラー] 無効なフォルダ、または 'data' フォルダがありません。", "ko": "[오류] 잘못된 폴더이거나 'data' 폴더가 없습니다.",
        "ar": "[خطأ] مجلد غير صالح أو مجلد 'data' مفقود.", "hi": "[त्रुटि] अमान्य फ़ोल्डर या 'data' फ़ोल्डर गायब है।", "tr": "[HATA] Geçersiz klasör veya 'data' klasörü eksik.",
        "vi": "[LỖI] Thư mục không hợp lệ hoặc thiếu thư mục 'data'.", "pl": "[BŁĄD] Nieprawidłowy folder lub brak folderu 'data'.", "id": "[ERROR] Folder tidak valid atau folder 'data' tidak ada."
    },
    "log_cache_copied": {
        "pt": "[AUTO] Memória ({}) copiada para o jogo!", "es": "[AUTO] ¡Memoria ({}) copiada al juego!", "fr": "[AUTO] Mémoire ({}) copiée !",
        "de": "[AUTO] Speicher ({}) kopiert!", "it": "[AUTO] Memoria ({}) copiata!", "ru": "[АВТО] Память ({}) скопирована!",
        "zh": "[自动] 内存 ({}) 已复制！", "ja": "[自動] メモリ ({}) がコピーされました！", "ko": "[자동] 메모리 ({}) 복사됨!",
        "ar": "[تلقائي] تم نسخ الذاكرة ({})!", "hi": "[ऑटो] मेमोरी ({}) कॉपी की गई!", "tr": "[OTO] Bellek ({}) kopyalandı!",
        "vi": "[TỰ ĐỘNG] Bộ nhớ ({}) đã được sao chép!", "pl": "[AUTO] Pamięć ({}) skopiowana!", "id": "[AUTO] Memori ({}) disalin!"
    },
    "log_cache_ready": {
        "pt": "[AUTO] Memória pronta para uso.", "es": "[AUTO] Memoria lista para usar.", "fr": "[AUTO] Mémoire prête à l'emploi.",
        "de": "[AUTO] Speicher einsatzbereit.", "it": "[AUTO] Memoria pronta per l'uso.", "ru": "[АВТО] Память готова к использованию.",
        "zh": "[自动] 内存准备就绪。", "ja": "[自動] メモリの使用準備が完了しました。", "ko": "[자동] 메모리 사용 준비 완료.",
        "ar": "[تلقائي] الذاكرة جاهزة للاستخدام.", "hi": "[ऑटो] मेमोरी उपयोग के लिए तैयार है।", "tr": "[OTO] Bellek kullanıma hazır.",
        "vi": "[TỰ ĐỘNG] Bộ nhớ đã sẵn sàng để sử dụng.", "pl": "[AUTO] Pamięć gotowa do użycia.", "id": "[AUTO] Memori siap digunakan."
    },
    "log_cache_loaded": {
        "pt": "[AUTO] Memória ({}) carregada!", "es": "[AUTO] ¡Memoria ({}) cargada!", "fr": "[AUTO] Mémoire ({}) chargée !",
        "de": "[AUTO] Speicher ({}) geladen!", "it": "[AUTO] Memoria ({}) caricata!", "ru": "[АВТО] Память ({}) загружена!",
        "zh": "[自动] 内存 ({}) 已加载！", "ja": "[自動] メモリ ({}) が読み込まれました！", "ko": "[자동] 메모리 ({}) 로드됨!",
        "ar": "[تلقائي] تم تحميل الذاكرة ({})!", "hi": "[ऑटो] मेमोरी ({}) लोड की गई!", "tr": "[OTO] Bellek ({}) yüklendi!",
        "vi": "[TỰ ĐỘNG] Bộ nhớ ({}) đã được tải!", "pl": "[AUTO] Pamięć ({}) załadowana!", "id": "[AUTO] Memori ({}) dimuat!"
    },
    "log_cache_new": {
        "pt": "[INFO] Criando nova memória: {}...", "es": "[INFO] Creando nueva memoria: {}...", "fr": "[INFO] Création d'une nouvelle mémoire : {}...",
        "de": "[INFO] Neuer Speicher wird erstellt: {}...", "it": "[INFO] Creazione nuova memoria: {}...", "ru": "[ИНФО] Создание новой памяти: {}...",
        "zh": "[信息] 创建新内存：{}...", "ja": "[情報] 新しいメモリを作成中: {}...", "ko": "[정보] 새 메모리 생성 중: {}...",
        "ar": "[معلومات] إنشاء ذاكرة جديدة: {}...", "hi": "[जानकारी] नई मेमोरी बना रहा है: {}...", "tr": "[BİLGİ] Yeni bellek oluşturuluyor: {}...",
        "vi": "[THÔNG TIN] Đang tạo bộ nhớ mới: {}...", "pl": "[INFO] Tworzenie nowej pamięci: {}...", "id": "[INFO] Membuat memori baru: {}..."
    },
    
    # Textos do LOG - BACKUP
    "log_backup_start": {
        "pt": "\n--- INICIANDO BACKUP ---", "es": "\n--- INICIANDO COPIA DE SEGURIDAD ---", "fr": "\n--- DÉMARRAGE DE LA SAUVEGARDE ---",
        "de": "\n--- BACKUP STARTEN ---", "it": "\n--- AVVIO BACKUP ---", "ru": "\n--- НАЧАЛО РЕЗЕРВНОГО КОПИРОВАНИЯ ---",
        "zh": "\n--- 开始备份 ---", "ja": "\n--- バックアップを開始 ---", "ko": "\n--- 백업 시작 ---", "ar": "\n--- بدء النسخ الاحتياطي ---",
        "hi": "\n--- बैकअप शुरू ---", "tr": "\n--- YEDEKLEME BAŞLIYOR ---", "vi": "\n--- BẮT ĐẦU SAO LƯU ---", "pl": "\n--- ROZPOCZYNANIE KOPII ZAPASOWEJ ---",
        "id": "\n--- MEMULAI CADANGAN ---"
    },
    "log_backup_ok": {
        "pt": "[OK] Backup concluído em:", "es": "[OK] Copia completada en:", "fr": "[OK] Sauvegarde terminée à :", "de": "[OK] Backup abgeschlossen in:",
        "it": "[OK] Backup completato in:", "ru": "[ОК] Резервное копирование завершено в:", "zh": "[OK] 备份完成于：", "ja": "[OK] バックアップ完了:",
        "ko": "[OK] 백업 완료:", "ar": "[موافق] اكتمل النسخ الاحتياطي في:", "hi": "[OK] बैकअप यहाँ पूरा हुआ:", "tr": "[TAMAM] Yedekleme tamamlandı:",
        "vi": "[OK] Sao lưu hoàn tất tại:", "pl": "[OK] Kopia zapasowa zakończona w:", "id": "[OK] Pencadangan selesai di:"
    },
    
    # Textos do LOG - FONTE
    "log_font_start": {
        "pt": "\n--- AJUSTANDO FONTE PARA {} ---", "es": "\n--- AJUSTANDO FUENTE A {} ---", "fr": "\n--- AJUSTEMENT DE LA POLICE À {} ---",
        "de": "\n--- SCHRIFTART AUF {} ANPASSEN ---", "it": "\n--- REGOLAZIONE CARATTERE A {} ---", "ru": "\n--- НАСТРОЙКА ШРИФТА НА {} ---",
        "zh": "\n--- 调整字体为 {} ---", "ja": "\n--- フォントを {} に調整 ---", "ko": "\n--- 글꼴을 {}로 조정 ---", "ar": "\n--- ضبط الخط على {} ---",
        "hi": "\n--- फ़ॉन्ट को {} में समायोजित करना ---", "tr": "\n--- YAZI TİPİNİ {} OLARAK AYARLAMA ---", "vi": "\n--- ĐIỀU CHỈNH PHÔNG CHỮ THÀNH {} ---",
        "pl": "\n--- DOSTOSOWYWANIE CZCIONKI DO {} ---", "id": "\n--- MENYESUAIKAN FONT KE {} ---"
    },
    "log_font_error_not_found": {
        "pt": "[ERRO] System.json não encontrado.", "es": "[ERROR] System.json no encontrado.", "fr": "[ERREUR] System.json introuvable.",
        "de": "[FEHLER] System.json nicht gefunden.", "it": "[ERRORE] System.json non trovato.", "ru": "[ОШИБКА] System.json не найден.",
        "zh": "[错误] 未找到 System.json。", "ja": "[エラー] System.jsonが見つかりません。", "ko": "[오류] System.json을 찾을 수 없습니다.",
        "ar": "[خطأ] لم يتم العثور على System.json.", "hi": "[त्रुटि] System.json नहीं मिला।", "tr": "[HATA] System.json bulunamadı.",
        "vi": "[LỖI] Không tìm thấy System.json.", "pl": "[BŁĄD] Nie znaleziono System.json.", "id": "[ERROR] System.json tidak ditemukan."
    },
    "log_font_ok": {
        "pt": "[OK] Tamanho alterado para {}!", "es": "[OK] ¡Tamaño cambiado a {}!", "fr": "[OK] Taille modifiée à {} !",
        "de": "[OK] Größe auf {} geändert!", "it": "[OK] Dimensione modificata a {}!", "ru": "[ОК] Размер изменен на {}!",
        "zh": "[OK] 尺寸更改为 {}！", "ja": "[OK] サイズが {} に変更されました！", "ko": "[OK] 크기가 {}로 변경되었습니다!",
        "ar": "[موافق] تم تغيير الحجم إلى {}!", "hi": "[OK] आकार {} में बदला गया!", "tr": "[TAMAM] Boyut {} olarak değiştirildi!",
        "vi": "[OK] Kích thước đã thay đổi thành {}!", "pl": "[OK] Rozmiar zmieniony na {}!", "id": "[OK] Ukuran diubah menjadi {}!"
    },
    "log_font_error": {
        "pt": "[ERRO] Falha ao ajustar:", "es": "[ERROR] Fallo al ajustar:", "fr": "[ERREUR] Échec de l'ajustement :", "de": "[FEHLER] Anpassung fehlgeschlagen:",
        "it": "[ERRORE] Impossibile regolare:", "ru": "[ОШИБКА] Не удалось настроить:", "zh": "[错误] 调整失败：", "ja": "[エラー] 調整に失敗しました:",
        "ko": "[오류] 조정 실패:", "ar": "[خطأ] فشل في الضبط:", "hi": "[त्रुटि] समायोजित करने में विफल:", "tr": "[HATA] Ayarlama başarısız:",
        "vi": "[LỖI] Điều chỉnh thất bại:", "pl": "[BŁĄD] Nie udało się dostosować:", "id": "[ERROR] Gagal menyesuaikan:"
    },
    
    # Textos do LOG - INSTALAÇÃO
    "log_install_start": {
        "pt": "\n--- INSTALANDO TRADUÇÃO ---", "es": "\n--- INSTALANDO TRADUCCIÓN ---", "fr": "\n--- INSTALLATION DE LA TRADUCTION ---",
        "de": "\n--- ÜBERSETZUNG INSTALLIEREN ---", "it": "\n--- INSTALLAZIONE TRADUZIONE ---", "ru": "\n--- УСТАНОВКА ПЕРЕВОДА ---",
        "zh": "\n--- 安装翻译 ---", "ja": "\n--- 翻訳をインストール中 ---", "ko": "\n--- 번역 설치 중 ---", "ar": "\n--- تثبيت الترجمة ---",
        "hi": "\n--- अनुवाद स्थापित कर रहा है ---", "tr": "\n--- ÇEVİRİ YÜKLENİYOR ---", "vi": "\n--- CÀI ĐẶT BẢN DỊCH ---", "pl": "\n--- INSTALOWANIE TŁUMACZENIA ---",
        "id": "\n--- MENGINSTAL TERJEMAHAN ---"
    },
    "log_install_error_no_files": {
        "pt": "[ERRO] Nenhum arquivo traduzido.", "es": "[ERROR] Ningún archivo traducido.", "fr": "[ERREUR] Aucun fichier traduit.",
        "de": "[FEHLER] Keine übersetzten Dateien.", "it": "[ERRORE] Nessun file tradotto.", "ru": "[ОШИБКА] Нет переведенных файлов.",
        "zh": "[错误] 没有翻译的文件。", "ja": "[エラー] 翻訳されたファイルがありません。", "ko": "[오류] 번역된 파일이 없습니다.",
        "ar": "[خطأ] لا توجد ملفات مترجمة.", "hi": "[त्रुटि] कोई अनुवादित फ़ाइल नहीं।", "tr": "[HATA] Çevrilmiş dosya yok.",
        "vi": "[LỖI] Không có tệp được dịch.", "pl": "[BŁĄD] Brak przetłumaczonych plików.", "id": "[ERROR] Tidak ada file terjemahan."
    },
    "log_install_ok": {
        "pt": "[OK] Instalação concluída!", "es": "[OK] ¡Instalación concluida!", "fr": "[OK] Installation terminée !", "de": "[OK] Installation abgeschlossen!",
        "it": "[OK] Installazione completata!", "ru": "[ОК] Установка завершена!", "zh": "[OK] 安装完成！", "ja": "[OK] インストールが完了しました！",
        "ko": "[OK] 설치 완료!", "ar": "[موافق] اكتمل التثبيت!", "hi": "[OK] स्थापना पूर्ण!", "tr": "[TAMAM] Kurulum tamamlandı!",
        "vi": "[OK] Cài đặt hoàn tất!", "pl": "[OK] Instalacja zakończona!", "id": "[OK] Instalasi selesai!"
    },
    
    # Textos do LOG - TRADUÇÃO (3 FASES)
    "log_trans_error_nobackup": {
        "pt": "[ERRO] Faça o backup antes!", "es": "[ERROR] ¡Haga el backup antes!", "fr": "[ERREUR] Faites une sauvegarde avant !", "de": "[FEHLER] Vorher Backup machen!",
        "it": "[ERRORE] Fai un backup prima!", "ru": "[ОШИБКА] Сначала сделайте бэкап!", "zh": "[错误] 请先备份！", "ja": "[エラー] 先にバックアップしてください！",
        "ko": "[오류] 먼저 백업하세요!", "ar": "[خطأ] قم بعمل نسخة احتياطية أولاً!", "hi": "[त्रुटि] पहले बैकअप लें!", "tr": "[HATA] Önce yedek alın!",
        "vi": "[LỖI] Sao lưu trước!", "pl": "[BŁĄD] Najpierw zrób kopię!", "id": "[ERROR] Lakukan pencadangan dulu!"
    },
    "log_trans_ok": {
        "pt": "[OK] TRADUÇÃO APLICADA!", "es": "[OK] ¡TRADUCCIÓN APLICADA!", "fr": "[OK] TRADUCTION APPLIQUÉE !", "de": "[OK] ÜBERSETZUNG ANGEWENDET!",
        "it": "[OK] TRADUZIONE APPLICATA!", "ru": "[ОК] ПЕРЕВОД ПРИМЕНЕН!", "zh": "[OK] 翻译已应用！", "ja": "[OK] 翻訳が適用されました！",
        "ko": "[OK] 번역 적용됨!", "ar": "[موافق] تم تطبيق الترجمة!", "hi": "[OK] अनुवाद लागू किया गया!", "tr": "[TAMAM] ÇEVİRİ UYGULANDI!",
        "vi": "[OK] BẢN DỊCH ĐÃ ÁP DỤNG!", "pl": "[OK] TŁUMACZENIE ZASTOSOWANE!", "id": "[OK] TERJEMAHAN DITERAPKAN!"
    },
    "log_phase1": {
        "pt": "\n--- FASE 1/3: EXTRAINDO TEXTOS ---", "es": "\n--- FASE 1/3: EXTRAYENDO TEXTOS ---", "fr": "\n--- PHASE 1/3 : EXTRACTION DES TEXTES ---",
        "de": "\n--- PHASE 1/3: TEXTE EXTRAHIEREN ---", "it": "\n--- FASE 1/3: ESTRAZIONE TESTI ---", "ru": "\n--- ФАЗА 1/3: ИЗВЛЕЧЕНИЕ ТЕКСТОВ ---",
        "zh": "\n--- 第1/3阶段：提取文本 ---", "ja": "\n--- フェーズ 1/3: テキストの抽出 ---", "ko": "\n--- 1/3 단계: 텍스트 추출 ---",
        "ar": "\n--- المرحلة 1/3: استخراج النصوص ---", "hi": "\n--- चरण 1/3: पाठ निकाल रहा है ---", "tr": "\n--- AŞAMA 1/3: METİNLER ÇIKARTILIYOR ---",
        "vi": "\n--- GIAI ĐOẠN 1/3: TRÍCH XUẤT VĂN BẢN ---", "pl": "\n--- FAZA 1/3: WYDOBYWANIE TEKSTÓW ---", "id": "\n--- FASE 1/3: MENGEKSTRAK TEKS ---"
    },
    "log_phase2": {
        "pt": "\n--- FASE 2/3: TRADUZINDO {} TEXTOS ---", "es": "\n--- FASE 2/3: TRADUCIENDO {} TEXTOS ---", "fr": "\n--- PHASE 2/3 : TRADUCTION DE {} TEXTES ---",
        "de": "\n--- PHASE 2/3: ÜBERSETZE {} TEXTE ---", "it": "\n--- FASE 2/3: TRADUZIONE DI {} TESTI ---", "ru": "\n--- ФАЗА 2/3: ПЕРЕВОД {} ТЕКСТОВ ---",
        "zh": "\n--- 第2/3阶段：翻译 {} 个文本 ---", "ja": "\n--- フェーズ 2/3: {} 個のテキストを翻訳 ---", "ko": "\n--- 2/3 단계: {} 개 텍스트 번역 ---",
        "ar": "\n--- المرحلة 2/3: ترجمة {} نصوص ---", "hi": "\n--- चरण 2/3: {} पाठों का अनुवाद कर रहा है ---", "tr": "\n--- AŞAMA 2/3: {} METİN ÇEVRİLİYOR ---",
        "vi": "\n--- GIAI ĐOẠN 2/3: DỊCH {} VĂN BẢN ---", "pl": "\n--- FAZA 2/3: TŁUMACZENIE {} TEKSTÓW ---", "id": "\n--- FASE 2/3: MENERJEMAHKAN {} TEKS ---"
    },
    "log_phase3": {
        "pt": "\n--- FASE 3/3: SALVANDO ---", "es": "\n--- FASE 3/3: GUARDANDO ---", "fr": "\n--- PHASE 3/3 : ENREGISTREMENT ---",
        "de": "\n--- PHASE 3/3: SPEICHERN ---", "it": "\n--- FASE 3/3: SALVATAGGIO ---", "ru": "\n--- ФАЗА 3/3: СОХРАНЕНИЕ ---",
        "zh": "\n--- 第3/3阶段：保存 ---", "ja": "\n--- フェーズ 3/3: 保存中 ---", "ko": "\n--- 3/3 단계: 저장 중 ---",
        "ar": "\n--- المرحلة 3/3: الحفظ ---", "hi": "\n--- चरण 3/3: सहेज रहा है ---", "tr": "\n--- AŞAMA 3/3: KAYDEDİLİYOR ---",
        "vi": "\n--- GIAI ĐOẠN 3/3: LƯU ---", "pl": "\n--- FAZA 3/3: ZAPISYWANIE ---", "id": "\n--- FASE 3/3: MENYIMPAN ---"
    },
    "log_no_new_texts": {
        "pt": "[INFO] Nenhum texto novo.", "es": "[INFO] Ningún texto nuevo.", "fr": "[INFO] Aucun nouveau texte.", "de": "[INFO] Kein neuer Text.",
        "it": "[INFO] Nessun nuovo testo.", "ru": "[ИНФО] Нет новых текстов.", "zh": "[信息] 没有新文本。", "ja": "[情報] 新しいテキストはありません。",
        "ko": "[정보] 새 텍스트 없음.", "ar": "[معلومات] لا يوجد نص جديد.", "hi": "[जानकारी] कोई नया पाठ नहीं।", "tr": "[BİLGİ] Yeni metin yok.",
        "vi": "[THÔNG TIN] Không có văn bản mới.", "pl": "[INFO] Brak nowego tekstu.", "id": "[INFO] Tidak ada teks baru."
    },
    "log_processing": {
        "pt": "Processando:", "es": "Procesando:", "fr": "Traitement :", "de": "Verarbeitung:", "it": "Elaborazione:", "ru": "Обработка:",
        "zh": "正在处理：", "ja": "処理中:", "ko": "처리 중:", "ar": "معالجة:", "hi": "प्रसंस्करण:", "tr": "İşleniyor:", "vi": "Đang xử lý:", "pl": "Przetwarzanie:", "id": "Memproses:"
    }
}

def get_text(key):
    lang = CONFIG.get("UI_LANG", "en")
    return UI_TEXTS.get(key, {}).get(lang, UI_TEXTS[key].get("en", key))

CODIGOS_PERMITIDOS = [401, 402, 405, 102, 108, 408]
CAMPOS_DB_SEGUROS = ["name", "description", "nickname", "profile", "message1", "message2", "message3", "message4"]
ARQUIVOS_DB = ["Actors.json", "Classes.json", "Skills.json", "Items.json", "Weapons.json", "Armors.json", "Enemies.json", "States.json"]

if getattr(sys, 'frozen', False):
    pasta_raiz = os.path.dirname(sys.executable)
else:
    pasta_raiz = os.path.dirname(os.path.abspath(__file__))

# ==============================================================================
#  INTERFACE GRÁFICA (CustomTkinter)
# ==============================================================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.geometry("850x700")
app.title("RPG Maker Master Translator")

progresso_var = ctk.DoubleVar(value=0)

def log_print(texto):
    app.after(0, _log_print_thread, texto)

def _log_print_thread(texto):
    texto_log.configure(state="normal")
    texto_log.insert("end", texto + "\n")
    texto_log.see("end")
    texto_log.configure(state="disabled")

def set_progresso(valor):
    app.after(0, progresso_var.set, valor)

# ==============================================================================
#  LÓGICA DO SISTEMA E INICIALIZAÇÃO
# ==============================================================================
def iniciar_sistema():
    idioma_selecionado = combo_idioma.get()
    CONFIG["TARGET_LANG"] = LANGUAGES[idioma_selecionado]["code"]
    CONFIG["UI_LANG"] = LANGUAGES[idioma_selecionado]["ui"]
    
    frame_idioma.pack_forget()
    frame_principal.pack(fill="both", expand=True, padx=20, pady=20)
    
    lbl_titulo.configure(text=get_text("header_title"))
    btn_backup.configure(text=get_text("menu_backup"))
    lbl_desc_backup.configure(text=get_text("desc_backup"))
    btn_traduzir.configure(text=get_text("menu_translate"))
    lbl_desc_traduzir.configure(text=get_text("desc_translate"))
    btn_instalar.configure(text=get_text("menu_install"))
    lbl_desc_instalar.configure(text=get_text("desc_install"))
    btn_fonte.configure(text=get_text("menu_font"))
    lbl_desc_fonte.configure(text=get_text("desc_font"))
    
    threading.Thread(target=configurar_diretorios).start()

def configurar_diretorios():
    log_print(get_text("log_init_config"))
    path_padrao = r"C:\Program Files (x86)\Steam\steamapps\common\Look Outside"
    
    if os.path.exists(path_padrao) and os.path.exists(os.path.join(path_padrao, "data")):
        CONFIG["GAME_DIR"] = path_padrao
        log_print(f"{get_text('log_game_found')} {path_padrao}")
    else:
        log_print(get_text("log_game_not_found"))
        diretorio = filedialog.askdirectory(title=get_text("msg_select_folder"))
        if diretorio and os.path.exists(os.path.join(diretorio, "data")):
            CONFIG["GAME_DIR"] = diretorio
            log_print(f"{get_text('log_game_selected')} {diretorio}")
        else:
            log_print(get_text("log_invalid_folder"))
            return

    CONFIG["TOOL_DIR"] = os.path.join(CONFIG["GAME_DIR"], "_TRADUTOR_FILES")
    CONFIG["BACKUP_DIR"] = os.path.join(CONFIG["TOOL_DIR"], "1_Backup")
    CONFIG["OUTPUT_DIR"] = os.path.join(CONFIG["TOOL_DIR"], "2_Traduzidos")
    
    nome_cache = f"memoria_traducoes_{CONFIG['TARGET_LANG']}.json"
    CONFIG["CACHE_FILE"] = os.path.join(CONFIG["TOOL_DIR"], nome_cache)

    for p in [CONFIG["TOOL_DIR"], CONFIG["BACKUP_DIR"], CONFIG["OUTPUT_DIR"]]:
        if not os.path.exists(p): os.makedirs(p)

    cache_local = os.path.join(pasta_raiz, nome_cache)
    
    if os.path.exists(cache_local):
        if os.path.abspath(cache_local) != os.path.abspath(CONFIG["CACHE_FILE"]):
            try:
                shutil.copy2(cache_local, CONFIG["CACHE_FILE"])
                log_print(get_text("log_cache_copied").format(nome_cache))
            except Exception as e:
                log_print(f"{get_text('log_font_error')} {e}")
        else:
            log_print(get_text("log_cache_ready"))
    elif os.path.exists(CONFIG["CACHE_FILE"]):
         log_print(get_text("log_cache_loaded").format(nome_cache))
    else:
        log_print(get_text("log_cache_new").format(nome_cache))
    
    app.after(0, habilitar_botoes)

def habilitar_botoes():
    btn_backup.configure(state="normal")
    btn_traduzir.configure(state="normal")
    btn_instalar.configure(state="normal")
    btn_fonte.configure(state="normal")

# ==============================================================================
#  AÇÕES SIMPLES (Backup, Instalação e Fonte)
# ==============================================================================
def acao_backup():
    threading.Thread(target=_acao_backup_thread).start()

def _acao_backup_thread():
    log_print(get_text("log_backup_start"))
    src = os.path.join(CONFIG["GAME_DIR"], "data")
    if not os.path.exists(src): return

    files = [f for f in os.listdir(src) if f.endswith('.json')]
    total = len(files)
    for i, f in enumerate(files):
        shutil.copy2(os.path.join(src, f), os.path.join(CONFIG["BACKUP_DIR"], f))
        set_progresso((i + 1) / total)
    log_print(f"{get_text('log_backup_ok')} {CONFIG['BACKUP_DIR']}")

def acao_ajustar_fonte():
    janela_fonte = ctk.CTkToplevel(app)
    janela_fonte.title(get_text("font_title"))
    janela_fonte.geometry("520x280")
    janela_fonte.attributes("-topmost", True)
    janela_fonte.transient(app)
    janela_fonte.grab_set()

    lbl_aviso = ctk.CTkLabel(janela_fonte, text=get_text("font_warning"), font=("Segoe UI", 14), justify="center", wraplength=480)
    lbl_aviso.pack(pady=20, padx=20)

    entrada_fonte = ctk.CTkEntry(janela_fonte, width=120, height=40, justify="center", font=("Segoe UI", 20, "bold"))
    entrada_fonte.insert(0, "18")
    entrada_fonte.pack(pady=10)

    def confirmar_fonte():
        valor = entrada_fonte.get()
        if valor.isdigit():
            tamanho = int(valor)
            janela_fonte.destroy()
            threading.Thread(target=_acao_fonte_thread, args=(tamanho,)).start()
        else:
            messagebox.showerror(get_text("msg_error_title"), get_text("msg_error_num"))

    btn_confirma = ctk.CTkButton(janela_fonte, text=get_text("btn_confirm"), font=("Segoe UI", 14, "bold"), height=40, command=confirmar_fonte)
    btn_confirma.pack(pady=10)

def _acao_fonte_thread(tamanho_escolhido):
    log_print(get_text("log_font_start").format(tamanho_escolhido))
    caminho_system = os.path.join(CONFIG["GAME_DIR"], "data", "System.json")
    
    if not os.path.exists(caminho_system):
        log_print(get_text("log_font_error_not_found"))
        return

    try:
        with open(caminho_system, 'r', encoding='utf-8') as f: dados = json.load(f)
        if "advanced" in dados and "fontSize" in dados["advanced"]:
            dados["advanced"]["fontSize"] = tamanho_escolhido
        with open(caminho_system, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
        log_print(get_text("log_font_ok").format(tamanho_escolhido))
    except Exception as e:
        log_print(f"{get_text('log_font_error')} {e}")

def acao_instalar():
    if messagebox.askyesno(get_text("msg_confirm_title"), get_text("msg_confirm_install")):
        threading.Thread(target=_acao_instalar_thread).start()

def _acao_instalar_thread():
    log_print(get_text("log_install_start"))
    files = [f for f in os.listdir(CONFIG["OUTPUT_DIR"]) if f.endswith('.json')]
    dest = os.path.join(CONFIG["GAME_DIR"], "data")
    total = len(files)
    
    if total == 0:
        log_print(get_text("log_install_error_no_files"))
        return

    for i, f in enumerate(files):
        shutil.copy2(os.path.join(CONFIG["OUTPUT_DIR"], f), os.path.join(dest, f))
        set_progresso((i + 1) / total)
    log_print(get_text("log_install_ok"))

# ==============================================================================
#  NOVO MOTOR TURBO DE TRADUÇÃO (3 FASES)
# ==============================================================================
def carregar_memoria():
    if os.path.exists(CONFIG["CACHE_FILE"]):
        try:
            with open(CONFIG["CACHE_FILE"], 'r', encoding='utf-8') as f: return json.load(f)
        except: return {}
    return {}

def salvar_memoria():
    with open(CONFIG["CACHE_FILE"], 'w', encoding='utf-8') as f:
        json.dump(memoria, f, ensure_ascii=False, indent=4)

def limpar_codigos_rpg(texto):
    texto = re.sub(r'\\ ?([a-zA-Z])', r'\\\1', texto)
    texto = re.sub(r'\[ ?(\d+) ?\]', r'[\1]', texto)
    texto = texto.replace('\\ n', '\n').replace('\\N', '\n')
    return texto

def traduzir_google(texto):
    if not texto or not isinstance(texto, str) or not texto.strip(): return texto
    if re.match(r'^[\W\d_]+$', texto.replace('\\', '')): return texto
    
    global MODO_EXTRACAO, textos_coletados, memoria
    if MODO_EXTRACAO:
        if texto not in memoria:
            textos_coletados.add(texto)
        return texto
    else:
        return memoria.get(texto, texto)

def traduzir_via_api(texto):
    try:
        texto_safe = texto.replace('\n', ' {BR} ')
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={CONFIG['TARGET_LANG']}&dt=t&q=" + urllib.parse.quote(texto_safe)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            dados = json.loads(response.read().decode('utf-8'))
            trad = ""
            if dados and len(dados) > 0 and dados[0]:
                for pedaco in dados[0]:
                    if pedaco and len(pedaco) > 0 and pedaco[0]: trad += pedaco[0]
            
            trad = trad.replace(' {BR} ', '\n').replace('{BR}', '\n')
            time.sleep(0.15)
            return limpar_codigos_rpg(trad)
    except:
        return texto

# --- Processadores Locais ---
def processar_database(dados):
    if isinstance(dados, list):
        for item in dados:
            if not item: continue
            for campo in CAMPOS_DB_SEGUROS:
                if campo in item and isinstance(item[campo], str):
                    item[campo] = traduzir_google(item[campo])

def processar_eventos(lista_comandos):
    if not isinstance(lista_comandos, list): return
    for cmd in lista_comandos:
        if not isinstance(cmd, dict): continue
        code = cmd.get("code")
        params = cmd.get("parameters")
        
        if not params: continue
        
        if code in CODIGOS_PERMITIDOS:
            if code == 102: 
                if len(params) > 0 and isinstance(params[0], list):
                    for i in range(len(params[0])): 
                        if isinstance(params[0][i], str): params[0][i] = traduzir_google(params[0][i])
            elif code == 402: 
                if len(params) > 1 and isinstance(params[1], str): params[1] = traduzir_google(params[1])
            else: 
                if len(params) > 0 and isinstance(params[0], str): params[0] = traduzir_google(params[0])

def percorrer_mapa(dados):
    if isinstance(dados, list):
        for item in dados:
            if item and "list" in item: processar_eventos(item["list"])
    elif isinstance(dados, dict):
        if "events" in dados and isinstance(dados["events"], list):
            for evento in dados["events"]:
                if not evento: continue
                if "pages" in evento:
                    for pagina in evento["pages"]:
                        if "list" in pagina: processar_eventos(pagina["list"])

def processar_troops(dados):
    if isinstance(dados, list):
        for troop in dados:
            if not troop: continue
            if "name" in troop and isinstance(troop["name"], str): troop["name"] = traduzir_google(troop["name"])
            if "pages" in troop:
                for page in troop["pages"]:
                    if "list" in page: processar_eventos(page["list"])

def processar_system(dados):
    if "gameTitle" in dados: dados["gameTitle"] = traduzir_google(dados["gameTitle"])
    if "terms" in dados:
        t = dados["terms"]
        for c in ["basic", "commands", "params"]:
            if c in t:
                for i in range(len(t[c])): t[c][i] = traduzir_google(t[c][i])
        if "messages" in t:
            for k, v in t["messages"].items(): t["messages"][k] = traduzir_google(v)

# --- Ação Principal de Tradução ---
def acao_traduzir():
    threading.Thread(target=_acao_traduzir_thread).start()

def _acao_traduzir_thread():
    global memoria, MODO_EXTRACAO, textos_coletados
    
    if not os.path.exists(CONFIG["BACKUP_DIR"]) or not os.listdir(CONFIG["BACKUP_DIR"]):
        log_print(get_text("log_trans_error_nobackup"))
        return

    memoria = carregar_memoria()
    textos_coletados.clear()
    
    arquivos = [f for f in os.listdir(CONFIG["BACKUP_DIR"]) if f.endswith('.json')]
    arquivos.sort(key=lambda x: os.path.getsize(os.path.join(CONFIG["BACKUP_DIR"], x)))
    mapa_regex = re.compile(r"Map\d+\.json")
    
    log_print(get_text("log_phase1"))
    MODO_EXTRACAO = True
    
    for arq in arquivos:
        in_p = os.path.join(CONFIG["BACKUP_DIR"], arq)
        try:
            with open(in_p, 'r', encoding='utf-8') as f: dados = json.load(f)
            if arq == "System.json": processar_system(dados)
            elif arq == "Troops.json": processar_troops(dados)
            elif arq in ARQUIVOS_DB: processar_database(dados)
            elif arq == "CommonEvents.json" or mapa_regex.match(arq): percorrer_mapa(dados)
        except Exception: pass

    pendentes = list(textos_coletados)
    total_pendentes = len(pendentes)
    
    if total_pendentes > 0:
        log_print(get_text("log_phase2").format(total_pendentes))
        contador_salvamento = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            for i, resultado in enumerate(executor.map(traduzir_via_api, pendentes)):
                texto_original = pendentes[i]
                memoria[texto_original] = resultado
                
                orig_limpo = texto_original.replace('\n', ' ')[:35]
                trad_limpo = resultado.replace('\n', ' ')[:35]
                log_print(f"[{i+1}/{total_pendentes}] \"{orig_limpo}\" -> \"{trad_limpo}\"")
                
                contador_salvamento += 1
                if contador_salvamento % 20 == 0: salvar_memoria()
                set_progresso((i + 1) / total_pendentes)
                
        salvar_memoria()
    else:
        log_print(get_text("log_no_new_texts"))

    log_print(get_text("log_phase3"))
    MODO_EXTRACAO = False
    total_arquivos = len(arquivos)
    
    for idx, arq in enumerate(arquivos):
        in_p = os.path.join(CONFIG["BACKUP_DIR"], arq)
        out_p = os.path.join(CONFIG["OUTPUT_DIR"], arq)
        log_print(f"{get_text('log_processing')} {arq}")
        
        try:
            with open(in_p, 'r', encoding='utf-8') as f: dados = json.load(f)
            
            if arq == "System.json": processar_system(dados)
            elif arq == "Troops.json": processar_troops(dados)
            elif arq in ARQUIVOS_DB: processar_database(dados)
            elif arq == "CommonEvents.json" or mapa_regex.match(arq): percorrer_mapa(dados)
            
            with open(out_p, 'w', encoding='utf-8') as f:
                json.dump(dados, f, ensure_ascii=False, indent=4)
                
            set_progresso((idx + 1) / total_arquivos)
        except Exception as e:
            log_print(f"[ERRO no {arq}]: {e}")
            
    log_print(get_text("log_trans_ok"))

# ==============================================================================
#  CONSTRUÇÃO DA INTERFACE (WIDGETS)
# ==============================================================================
frame_idioma = ctk.CTkFrame(app, fg_color="transparent")
frame_idioma.pack(fill="both", expand=True, padx=50, pady=150)

# O label de escolha inicial precisa puxar direto do dicionário, pois a UI ainda não tem idioma definido
lbl_idioma = ctk.CTkLabel(frame_idioma, text="Select Target Language", font=("Segoe UI", 20, "bold"))
lbl_idioma.pack(pady=20)

combo_idioma = ctk.CTkComboBox(frame_idioma, values=list(LANGUAGES.keys()), font=("Segoe UI", 16), width=300, height=40)
combo_idioma.set("Português (Brasil)")
combo_idioma.pack(pady=20)

# Atualiza o texto inicial baseado na escolha do combobox
def atualizar_lbl_idioma(*args):
    lang_code = LANGUAGES[combo_idioma.get()]["ui"]
    texto_lbl = UI_TEXTS["lbl_select_lang"].get(lang_code, "Select Target Language")
    texto_btn = UI_TEXTS["btn_start_sys"].get(lang_code, "START SYSTEM")
    lbl_idioma.configure(text=texto_lbl)
    btn_iniciar.configure(text=texto_btn)

combo_idioma.configure(command=atualizar_lbl_idioma)

btn_iniciar = ctk.CTkButton(frame_idioma, text="INICIAR SISTEMA", font=("Segoe UI", 16, "bold"), height=50, command=iniciar_sistema)
btn_iniciar.pack(pady=20)
atualizar_lbl_idioma()

frame_principal = ctk.CTkFrame(app, fg_color="transparent")

lbl_titulo = ctk.CTkLabel(frame_principal, text="", font=("Segoe UI", 24, "bold"), text_color="#3a7ebf")
lbl_titulo.pack(pady=10)

frame_botoes = ctk.CTkFrame(frame_principal, fg_color="transparent")
frame_botoes.pack(pady=10)

btn_font_style = ("Segoe UI", 14, "bold")
desc_font_style = ("Segoe UI", 11)

btn_backup = ctk.CTkButton(frame_botoes, text="", font=btn_font_style, height=40, width=280, state="disabled", command=acao_backup)
btn_backup.grid(row=0, column=0, padx=15, pady=(15, 2))
lbl_desc_backup = ctk.CTkLabel(frame_botoes, text="", font=desc_font_style, text_color="gray")
lbl_desc_backup.grid(row=1, column=0, padx=15, pady=(0, 15))

btn_traduzir = ctk.CTkButton(frame_botoes, text="", font=btn_font_style, height=40, width=280, state="disabled", command=acao_traduzir)
btn_traduzir.grid(row=0, column=1, padx=15, pady=(15, 2))
lbl_desc_traduzir = ctk.CTkLabel(frame_botoes, text="", font=desc_font_style, text_color="gray")
lbl_desc_traduzir.grid(row=1, column=1, padx=15, pady=(0, 15))

btn_instalar = ctk.CTkButton(frame_botoes, text="", font=btn_font_style, height=40, width=280, state="disabled", command=acao_instalar, fg_color="#28a745", hover_color="#218838")
btn_instalar.grid(row=2, column=0, padx=15, pady=(15, 2))
lbl_desc_instalar = ctk.CTkLabel(frame_botoes, text="", font=desc_font_style, text_color="gray")
lbl_desc_instalar.grid(row=3, column=0, padx=15, pady=(0, 15))

btn_fonte = ctk.CTkButton(frame_botoes, text="", font=btn_font_style, height=40, width=280, state="disabled", command=acao_ajustar_fonte, fg_color="#d39e00", hover_color="#c69500")
btn_fonte.grid(row=2, column=1, padx=15, pady=(15, 2))
lbl_desc_fonte = ctk.CTkLabel(frame_botoes, text="", font=desc_font_style, text_color="gray")
lbl_desc_fonte.grid(row=3, column=1, padx=15, pady=(0, 15))

barra_progresso = ctk.CTkProgressBar(frame_principal, variable=progresso_var, width=590, height=15)
barra_progresso.pack(pady=15)

texto_log = ctk.CTkTextbox(frame_principal, width=720, height=220, font=("Consolas", 13), state="disabled", fg_color="#1e1e1e", text_color="#00ff00")
texto_log.pack(pady=10)

app.mainloop()