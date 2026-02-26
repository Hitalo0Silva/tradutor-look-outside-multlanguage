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

LANGUAGES = {
    "Português (Brasil)": {"code": "pt", "ui": "pt"},
    "English": {"code": "en", "ui": "en"},
    "Español": {"code": "es", "ui": "es"},
    "Français": {"code": "fr", "ui": "fr"},
    "Deutsch": {"code": "de", "ui": "de"},
    "Italiano": {"code": "it", "ui": "it"},
    "Русский": {"code": "ru", "ui": "ru"},
    "简体中文": {"code": "zh-CN", "ui": "zh"},
    "日本語": {"code": "ja", "ui": "ja"},
    "한국어": {"code": "ko", "ui": "ko"}
}

UI_TEXTS = {
    # Títulos e Botões Iniciais
    "lbl_select_lang": {"pt": "Selecione o Idioma / Target Language", "en": "Select Target Language", "es": "Seleccione el Idioma Destino"},
    "btn_start_sys": {"pt": "INICIAR SISTEMA", "en": "START SYSTEM", "es": "INICIAR SISTEMA"},
    "header_title": {"pt": "MESTRE TRADUTOR RPG MAKER - v6.0", "en": "RPG MAKER MASTER TRANSLATOR - v6.0", "es": "MAESTRO TRADUCTOR RPG MAKER - v6.0"},
    
    # Menu Principal
    "menu_backup": {"pt": "1. FAZER BACKUP", "en": "1. MAKE BACKUP", "es": "1. HACER COPIA"},
    "desc_backup": {"pt": "Cria uma cópia de segurança do jogo original.", "en": "Creates a safety copy of the original game.", "es": "Crea una copia de seguridad del juego original."},
    "menu_translate": {"pt": "2. INICIAR TRADUÇÃO", "en": "2. START TRANSLATION", "es": "2. INICIAR TRADUCCIÓN"},
    "desc_translate": {"pt": "Traduz os arquivos usando a memória e a internet.", "en": "Translates files using memory and internet.", "es": "Traduce archivos usando memoria e internet."},
    "menu_install": {"pt": "3. APLICAR NO JOGO", "en": "3. APPLY TO GAME", "es": "3. APLICAR AL JUEGO"},
    "desc_install": {"pt": "Substitui os arquivos originais pelos traduzidos.", "en": "Replaces original files with translated ones.", "es": "Reemplaza archivos originales por los traducidos."},
    "menu_font": {"pt": "4. AJUSTAR FONTE", "en": "4. ADJUST FONT", "es": "4. AJUSTAR FUENTE"},
    "desc_font": {"pt": "Reduz a letra para caber nos balões de texto.", "en": "Reduces font to fit in text boxes.", "es": "Reduce la letra para caber en los cuadros."},
    
    # Pop-ups e Alertas
    "font_title": {"pt": "Ajuste de Fonte", "en": "Font Adjustment", "es": "Ajuste de Fuente"},
    "font_warning": {
        "pt": "O idioma traduzido pode ter palavras mais longas, fazendo com que o jogo corte os textos na tela.\n\nRecomendamos diminuir o tamanho da fonte. O ideal sugerido é 18, mas digite outro valor abaixo se desejar:",
        "en": "Translated words can be longer, causing the game to cut off text on screen.\n\nWe recommend lowering the font size. The ideal size is 18, but you can enter another value below:",
        "es": "Las palabras traducidas pueden ser más largas, cortando el texto.\n\nRecomendamos reducir la fuente. El ideal es 18, pero puedes ingresar otro valor abajo:"
    },
    "btn_confirm": {"pt": "Confirmar", "en": "Confirm", "es": "Confirmar"},
    "msg_error_title": {"pt": "Erro", "en": "Error", "es": "Error"},
    "msg_error_num": {"pt": "Por favor, digite apenas números inteiros.", "en": "Please enter only integer numbers.", "es": "Por favor, ingrese solo números enteros."},
    "msg_confirm_title": {"pt": "Confirmar", "en": "Confirm", "es": "Confirmar"},
    "msg_confirm_install": {"pt": "Isso substituirá os arquivos do jogo. Continuar?", "en": "This will replace game files. Continue?", "es": "Esto reemplazará los archivos del juego. ¿Continuar?"},
    "msg_select_folder": {"pt": "Selecione a pasta do jogo", "en": "Select the game folder", "es": "Selecciona la carpeta del juego"},
    
    # Textos do LOG
    "log_init_config": {"pt": "Iniciando configuração...", "en": "Starting configuration...", "es": "Iniciando configuración..."},
    "log_game_found": {"pt": "[AUTO] Jogo encontrado em:", "en": "[AUTO] Game found at:", "es": "[AUTO] Juego encontrado en:"},
    "log_game_not_found": {"pt": "Jogo não detectado. Selecione a pasta...", "en": "Game not detected. Select the folder...", "es": "Juego no detectado. Selecciona la carpeta..."},
    "log_game_selected": {"pt": "[OK] Jogo selecionado:", "en": "[OK] Game selected:", "es": "[OK] Juego seleccionado:"},
    "log_invalid_folder": {"pt": "[ERRO] Pasta inválida ou sem pasta 'data'.", "en": "[ERROR] Invalid folder or missing 'data' folder.", "es": "[ERROR] Carpeta inválida o falta la carpeta 'data'."},
    "log_cache_copied": {"pt": "[AUTO] Memória ({}) copiada para a pasta do jogo!", "en": "[AUTO] Memory ({}) copied to game folder!", "es": "[AUTO] ¡Memoria ({}) copiada a la carpeta del juego!"},
    "log_cache_ready": {"pt": "[AUTO] Memória de tradução local pronta para uso.", "en": "[AUTO] Local translation memory ready for use.", "es": "[AUTO] Memoria de traducción local lista para usar."},
    "log_cache_loaded": {"pt": "[AUTO] Memória ({}) já existente carregada!", "en": "[AUTO] Existing memory ({}) loaded!", "es": "[AUTO] ¡Memoria existente ({}) cargada!"},
    "log_cache_new": {"pt": "[INFO] Nenhum cache encontrado. Criando nova memória: {}...", "en": "[INFO] No cache found. Creating new memory: {}...", "es": "[INFO] No se encontró caché. Creando nueva memoria: {}..."},
    
    "log_backup_start": {"pt": "\n--- INICIANDO BACKUP ---", "en": "\n--- STARTING BACKUP ---", "es": "\n--- INICIANDO COPIA DE SEGURIDAD ---"},
    "log_backup_ok": {"pt": "[OK] Backup concluído em:", "en": "[OK] Backup completed at:", "es": "[OK] Copia completada en:"},
    
    "log_font_start": {"pt": "\n--- AJUSTANDO FONTE PARA {} ---", "en": "\n--- ADJUSTING FONT TO {} ---", "es": "\n--- AJUSTANDO FUENTE A {} ---"},
    "log_font_error_not_found": {"pt": "[ERRO] System.json não encontrado.", "en": "[ERROR] System.json not found.", "es": "[ERROR] System.json no encontrado."},
    "log_font_ok": {"pt": "[OK] Tamanho da fonte alterado para {} no jogo!", "en": "[OK] Font size changed to {} in the game!", "es": "[OK] ¡Tamaño de fuente cambiado a {} en el juego!"},
    "log_font_error": {"pt": "[ERRO] Falha ao ajustar:", "en": "[ERROR] Failed to adjust:", "es": "[ERROR] Fallo al ajustar:"},
    
    "log_install_start": {"pt": "\n--- INSTALANDO TRADUÇÃO ---", "en": "\n--- INSTALLING TRANSLATION ---", "es": "\n--- INSTALANDO TRADUCCIÓN ---"},
    "log_install_error_no_files": {"pt": "[ERRO] Nenhum arquivo traduzido encontrado.", "en": "[ERROR] No translated files found.", "es": "[ERROR] No se encontraron archivos traducidos."},
    "log_install_ok": {"pt": "[OK] Instalação concluída com sucesso!", "en": "[OK] Installation completed successfully!", "es": "[OK] ¡Instalación completada con éxito!"},
    
    "log_trans_error_nobackup": {"pt": "[ERRO] Faça o backup antes de traduzir!", "en": "[ERROR] Make a backup before translating!", "es": "[ERROR] ¡Haz una copia antes de traducir!"},
    "log_trans_ok": {"pt": "[OK] TRADUÇÃO COMPLETA APLICADA COM SUCESSO!", "en": "[OK] TRANSLATION COMPLETELY APPLIED!", "es": "[OK] ¡TRADUCCIÓN APLICADA CON ÉXITO!"},
    
    # Textos do Motor Turbo de 3 Fases
    "log_phase1": {"pt": "\n--- FASE 1/3: EXTRAINDO TEXTOS ---", "en": "\n--- PHASE 1/3: EXTRACTING TEXTS ---", "es": "\n--- FASE 1/3: EXTRAYENDO TEXTOS ---"},
    "log_phase2": {"pt": "\n--- FASE 2/3: TRADUZINDO {} TEXTOS NOVOS ---", "en": "\n--- PHASE 2/3: TRANSLATING {} NEW TEXTS ---", "es": "\n--- FASE 2/3: TRADUCIENDO {} TEXTOS NUEVOS ---"},
    "log_phase3": {"pt": "\n--- FASE 3/3: APLICANDO E SALVANDO ---", "en": "\n--- PHASE 3/3: APPLYING AND SAVING ---", "es": "\n--- FASE 3/3: APLICANDO Y GUARDANDO ---"},
    "log_no_new_texts": {"pt": "[INFO] Nenhum texto novo detectado. Puxando tudo da memória...", "en": "[INFO] No new texts detected. Pulling all from memory...", "es": "[INFO] No se detectaron textos nuevos. Sacando todo de memoria..."},
    "log_processing": {"pt": "Processando e salvando:", "en": "Processing & saving:", "es": "Procesando y guardando:"},
}

def get_text(key):
    lang = CONFIG.get("UI_LANG", "en")
    if lang not in ["pt", "en", "es"]: lang = "en"
    return UI_TEXTS.get(key, {}).get(lang, key)

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
app.title("Mestre Tradutor RPG Maker")

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
    """Filtra textos e joga para extração ou aplica direto da memória"""
    if not texto or not isinstance(texto, str) or not texto.strip(): return texto
    if re.match(r'^[\W\d_]+$', texto.replace('\\', '')): return texto
    
    global MODO_EXTRACAO, textos_coletados, memoria
    if MODO_EXTRACAO:
        if texto not in memoria:
            textos_coletados.add(texto)
        return texto # Na Fase 1, não modificamos o arquivo
    else:
        return memoria.get(texto, texto) # Na Fase 3, puxa da memória instantaneamente

def traduzir_via_api(texto):
    """Função isolada para fazer chamadas HTTP na Fase 2 (Multithread)"""
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
            time.sleep(0.15) # Pausa mínima para não ser bloqueado pelo Google
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
    
    # FASE 1: EXTRAÇÃO (Varre tudo em 1 segundo e anota o que não está no cache)
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

    # FASE 2: TRADUÇÃO MULTITHREAD (Lote Rápido)
    pendentes = list(textos_coletados)
    total_pendentes = len(pendentes)
    
    if total_pendentes > 0:
        log_print(get_text("log_phase2").format(total_pendentes))
        contador_salvamento = 0
        
        # Cria 6 operários trabalhando ao mesmo tempo no Google Tradutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            for i, resultado in enumerate(executor.map(traduzir_via_api, pendentes)):
                texto_original = pendentes[i]
                memoria[texto_original] = resultado
                
                # Exibe a frase exata no console, encurtada para não travar a tela
                orig_limpo = texto_original.replace('\n', ' ')[:35]
                trad_limpo = resultado.replace('\n', ' ')[:35]
                log_print(f"[{i+1}/{total_pendentes}] \"{orig_limpo}\" -> \"{trad_limpo}\"")
                
                contador_salvamento += 1
                if contador_salvamento % 20 == 0: salvar_memoria()
                set_progresso((i + 1) / total_pendentes)
                
        salvar_memoria()
    else:
        log_print(get_text("log_no_new_texts"))

    # FASE 3: APLICAÇÃO (Coloca as palavras do Cache para dentro dos arquivos do Jogo instantaneamente)
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

lbl_idioma = ctk.CTkLabel(frame_idioma, text="Selecione o Idioma / Target Language", font=("Segoe UI", 20, "bold"))
lbl_idioma.pack(pady=20)

combo_idioma = ctk.CTkComboBox(frame_idioma, values=list(LANGUAGES.keys()), font=("Segoe UI", 16), width=300, height=40)
combo_idioma.set("Português (Brasil)")
combo_idioma.pack(pady=20)

btn_iniciar = ctk.CTkButton(frame_idioma, text="INICIAR SISTEMA", font=("Segoe UI", 16, "bold"), height=50, command=iniciar_sistema)
btn_iniciar.pack(pady=20)

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