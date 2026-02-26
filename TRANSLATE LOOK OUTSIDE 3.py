import os
import json
import shutil
import time
import urllib.request
import urllib.parse
import re
import sys
import threading
import customtkinter as ctk
from tkinter import messagebox, filedialog

# ==============================================================================
#  CONFIGURAÇÕES GLOBAIS
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
    "header_title": {
        "pt": "MESTRE TRADUTOR RPG MAKER - v6.0",
        "en": "RPG MAKER MASTER TRANSLATOR - v6.0",
        "es": "MAESTRO TRADUCTOR RPG MAKER - v6.0"
    },
    "menu_backup": {"pt": "1. FAZER BACKUP", "en": "1. MAKE BACKUP", "es": "1. HACER COPIA"},
    "desc_backup": {"pt": "Cria uma cópia de segurança do jogo original.", "en": "Creates a safety copy of the original game.", "es": "Crea una copia de seguridad del juego original."},
    "menu_translate": {"pt": "2. INICIAR TRADUÇÃO", "en": "2. START TRANSLATION", "es": "2. INICIAR TRADUCCIÓN"},
    "desc_translate": {"pt": "Traduz os arquivos usando a memória e a internet.", "en": "Translates files using memory and internet.", "es": "Traduce archivos usando memoria e internet."},
    "menu_install": {"pt": "3. APLICAR NO JOGO", "en": "3. APPLY TO GAME", "es": "3. APLICAR AL JUEGO"},
    "desc_install": {"pt": "Substitui os arquivos originais pelos traduzidos.", "en": "Replaces original files with translated ones.", "es": "Reemplaza archivos originales por los traducidos."},
    "menu_font": {"pt": "4. AJUSTAR FONTE", "en": "4. ADJUST FONT", "es": "4. AJUSTAR FUENTE"},
    "desc_font": {"pt": "Reduz a letra para caber nos balões de texto.", "en": "Reduces font to fit in text boxes.", "es": "Reduce la letra para caber en los cuadros."},
    "font_title": {"pt": "Ajuste de Fonte", "en": "Font Adjustment", "es": "Ajuste de Fuente"},
    "font_warning": {
        "pt": "O idioma traduzido pode ter palavras mais longas, fazendo com que o jogo corte os textos na tela.\n\nPara evitar isso, recomendamos diminuir o tamanho da fonte. O ideal sugerido é 18, mas você pode digitar outro valor abaixo:",
        "en": "Translated words can be longer, causing the game to cut off text on screen.\n\nTo prevent this, we recommend lowering the font size. The ideal size is 18, but you can enter another value below:",
        "es": "Las palabras traducidas pueden ser más largas, haciendo que el juego corte el texto.\n\nPara evitar esto, recomendamos reducir la fuente. El ideal es 18, pero puedes ingresar otro valor:"
    }
}

def get_text(key):
    lang = CONFIG.get("UI_LANG", "en")
    if lang not in ["pt", "en", "es"]: lang = "en"
    return UI_TEXTS.get(key, {}).get(lang, key)

CODIGOS_PERMITIDOS = [401, 402, 405, 102, 108, 408]
CAMPOS_DB_SEGUROS = ["name", "description", "nickname", "profile", "message1", "message2", "message3", "message4"]
ARQUIVOS_DB = ["Actors.json", "Classes.json", "Skills.json", "Items.json", "Weapons.json", "Armors.json", "Enemies.json", "States.json"]

memoria = {}
contador_trad = 0

# Descobre a pasta real do executável ou do script
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
app.geometry("800x700")
app.title("Mestre Tradutor RPG Maker")

# Variáveis visuais
progresso_var = ctk.DoubleVar(value=0)

def log_print(texto):
    """Adiciona texto ao console visual da interface."""
    app.after(0, _log_print_thread, texto)

def _log_print_thread(texto):
    texto_log.configure(state="normal")
    texto_log.insert("end", texto + "\n")
    texto_log.see("end")
    texto_log.configure(state="disabled")

def set_progresso(valor):
    app.after(0, progresso_var.set, valor)

# ==============================================================================
#  LÓGICA DO SISTEMA
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
    log_print("Iniciando configuração...")
    path_padrao = r"C:\Program Files (x86)\Steam\steamapps\common\Look Outside"
    
    if os.path.exists(path_padrao) and os.path.exists(os.path.join(path_padrao, "data")):
        CONFIG["GAME_DIR"] = path_padrao
        log_print(f"[AUTO] Jogo encontrado em: {path_padrao}")
    else:
        log_print("Jogo não detectado automaticamente. Selecione a pasta...")
        diretorio = filedialog.askdirectory(title="Selecione a pasta do jogo")
        if diretorio and os.path.exists(os.path.join(diretorio, "data")):
            CONFIG["GAME_DIR"] = diretorio
            log_print(f"[OK] Jogo selecionado: {diretorio}")
        else:
            log_print("[ERRO] Pasta inválida ou sem pasta 'data'. Reinicie o programa.")
            return

    CONFIG["TOOL_DIR"] = os.path.join(CONFIG["GAME_DIR"], "_TRADUTOR_FILES")
    CONFIG["BACKUP_DIR"] = os.path.join(CONFIG["TOOL_DIR"], "1_Backup")
    CONFIG["OUTPUT_DIR"] = os.path.join(CONFIG["TOOL_DIR"], "2_Traduzidos")
    CONFIG["CACHE_FILE"] = os.path.join(CONFIG["TOOL_DIR"], "memoria_traducoes.json")

    for p in [CONFIG["TOOL_DIR"], CONFIG["BACKUP_DIR"], CONFIG["OUTPUT_DIR"]]:
        if not os.path.exists(p): os.makedirs(p)

    cache_local = os.path.join(pasta_raiz, "memoria_traducoes.json")
    
    if os.path.exists(cache_local):
        if os.path.abspath(cache_local) != os.path.abspath(CONFIG["CACHE_FILE"]):
            try:
                shutil.copy2(cache_local, CONFIG["CACHE_FILE"])
            except shutil.SameFileError:
                pass
        log_print("[AUTO] Memória de tradução importada com sucesso!")
    else:
        log_print("[INFO] Criando nova memória de tradução...")
    
    app.after(0, habilitar_botoes)

def habilitar_botoes():
    btn_backup.configure(state="normal")
    btn_traduzir.configure(state="normal")
    btn_instalar.configure(state="normal")
    btn_fonte.configure(state="normal")

# ==============================================================================
#  AÇÕES
# ==============================================================================
def acao_backup():
    threading.Thread(target=_acao_backup_thread).start()

def _acao_backup_thread():
    log_print("\n--- INICIANDO BACKUP ---")
    src = os.path.join(CONFIG["GAME_DIR"], "data")
    if not os.path.exists(src): return

    files = [f for f in os.listdir(src) if f.endswith('.json')]
    total = len(files)
    for i, f in enumerate(files):
        shutil.copy2(os.path.join(src, f), os.path.join(CONFIG["BACKUP_DIR"], f))
        set_progresso((i + 1) / total)
    log_print(f"[OK] Backup concluído em: {CONFIG['BACKUP_DIR']}")


# --- JANELA DE FONTE ---
def acao_ajustar_fonte():
    # Cria uma janela flutuante (Pop-up)
    janela_fonte = ctk.CTkToplevel(app)
    janela_fonte.title(get_text("font_title"))
    janela_fonte.geometry("500x280")
    janela_fonte.attributes("-topmost", True) # Fica sempre por cima
    janela_fonte.transient(app)
    janela_fonte.grab_set() # Trava a janela principal enquanto essa estiver aberta

    lbl_aviso = ctk.CTkLabel(janela_fonte, text=get_text("font_warning"), font=("Segoe UI", 14), justify="center", wraplength=450)
    lbl_aviso.pack(pady=20, padx=20)

    # Caixa onde o usuário digita o número (já vem com 18 escrito)
    entrada_fonte = ctk.CTkEntry(janela_fonte, width=120, height=40, justify="center", font=("Segoe UI", 20, "bold"))
    entrada_fonte.insert(0, "18")
    entrada_fonte.pack(pady=10)

    def confirmar_fonte():
        valor = entrada_fonte.get()
        if valor.isdigit(): # Verifica se é apenas número
            tamanho = int(valor)
            janela_fonte.destroy()
            threading.Thread(target=_acao_fonte_thread, args=(tamanho,)).start()
        else:
            messagebox.showerror("Erro", "Por favor, digite apenas números inteiros.")

    btn_confirma = ctk.CTkButton(janela_fonte, text="Confirmar", font=("Segoe UI", 14, "bold"), height=40, command=confirmar_fonte)
    btn_confirma.pack(pady=10)


def _acao_fonte_thread(tamanho_escolhido):
    log_print(f"\n--- AJUSTANDO FONTE PARA {tamanho_escolhido} ---")
    caminho_system = os.path.join(CONFIG["GAME_DIR"], "data", "System.json")
    
    if not os.path.exists(caminho_system):
        log_print("[ERRO] System.json não encontrado.")
        return

    try:
        with open(caminho_system, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        if "advanced" in dados and "fontSize" in dados["advanced"]:
            dados["advanced"]["fontSize"] = tamanho_escolhido
            
        with open(caminho_system, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
            
        log_print(f"[OK] Tamanho da fonte alterado para {tamanho_escolhido} no jogo!")
    except Exception as e:
        log_print(f"[ERRO] Falha ao ajustar: {e}")

def acao_instalar():
    if messagebox.askyesno("Confirmar", "Isso substituirá os arquivos do jogo. Continuar?"):
        threading.Thread(target=_acao_instalar_thread).start()

def _acao_instalar_thread():
    log_print("\n--- INSTALANDO TRADUÇÃO ---")
    files = [f for f in os.listdir(CONFIG["OUTPUT_DIR"]) if f.endswith('.json')]
    dest = os.path.join(CONFIG["GAME_DIR"], "data")
    total = len(files)
    
    if total == 0:
        log_print("[ERRO] Nenhum arquivo traduzido encontrado.")
        return

    for i, f in enumerate(files):
        shutil.copy2(os.path.join(CONFIG["OUTPUT_DIR"], f), os.path.join(dest, f))
        set_progresso((i + 1) / total)
    log_print("[OK] Instalação concluída com sucesso!")

# --- MOTOR DE TRADUÇÃO ---
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
    
    if texto in memoria: return memoria[texto]
    
    try:
        texto_safe = texto.replace('\n', ' {BR} ')
        lang = CONFIG["TARGET_LANG"]
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={lang}&dt=t&q=" + urllib.parse.quote(texto_safe)
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            dados = json.loads(response.read().decode('utf-8'))
            trad = ""
            if dados and len(dados) > 0 and dados[0]:
                for pedaco in dados[0]:
                    if pedaco and len(pedaco) > 0: trad += pedaco[0]
            
            trad = trad.replace(' {BR} ', '\n').replace('{BR}', '\n')
            trad = limpar_codigos_rpg(trad)
            
            memoria[texto] = trad
            global contador_trad
            contador_trad += 1
            if contador_trad % 20 == 0: salvar_memoria()
            time.sleep(1.0)
            return trad
    except: return texto

# Processadores
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
        
        # Prevenção extra caso os parâmetros estejam vazios
        if not params: continue
        
        if code in CODIGOS_PERMITIDOS:
            if code == 102: 
                # Código 102: A lista principal de escolhas na tela
                if len(params) > 0 and isinstance(params[0], list):
                    for i in range(len(params[0])): 
                        if isinstance(params[0][i], str):
                            params[0][i] = traduzir_google(params[0][i])
                            
            elif code == 402: 
                # Código 402: O texto de ramificação da escolha que você encontrou
                if len(params) > 1 and isinstance(params[1], str):
                    params[1] = traduzir_google(params[1])
                    
            else: 
                # Outros códigos (401, 405, 108, 408): Textos normais e comentários
                if len(params) > 0 and isinstance(params[0], str):
                    params[0] = traduzir_google(params[0])

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

def acao_traduzir():
    threading.Thread(target=_acao_traduzir_thread).start()

def _acao_traduzir_thread():
    global memoria
    log_print("\n--- INICIANDO TRADUÇÃO ---")
    memoria = carregar_memoria()
    
    if not os.path.exists(CONFIG["BACKUP_DIR"]) or not os.listdir(CONFIG["BACKUP_DIR"]):
        log_print("[ERRO] Faça o backup antes de traduzir!")
        return

    arquivos = [f for f in os.listdir(CONFIG["BACKUP_DIR"]) if f.endswith('.json')]
    arquivos.sort(key=lambda x: os.path.getsize(os.path.join(CONFIG["BACKUP_DIR"], x)))
    mapa_regex = re.compile(r"Map\d+\.json")
    
    total = len(arquivos)
    for idx, arq in enumerate(arquivos):
        in_p = os.path.join(CONFIG["BACKUP_DIR"], arq)
        out_p = os.path.join(CONFIG["OUTPUT_DIR"], arq)
        log_print(f"Processando: {arq}")
        
        try:
            with open(in_p, 'r', encoding='utf-8') as f: dados = json.load(f)
            
            if arq == "System.json": processar_system(dados)
            elif arq == "Troops.json": processar_troops(dados)
            elif arq in ARQUIVOS_DB: processar_database(dados)
            elif arq == "CommonEvents.json" or mapa_regex.match(arq): percorrer_mapa(dados)
            
            with open(out_p, 'w', encoding='utf-8') as f:
                json.dump(dados, f, ensure_ascii=False, indent=4)
                
            salvar_memoria()
            set_progresso((idx + 1) / total)
        except Exception as e:
            log_print(f"[ERRO no {arq}]: {e}")
            
    log_print("[OK] TRADUÇÃO COMPLETA!")

# ==============================================================================
#  CONSTRUÇÃO DA INTERFACE (WIDGETS)
# ==============================================================================

# FRAME 1: SELEÇÃO DE IDIOMA
frame_idioma = ctk.CTkFrame(app, fg_color="transparent")
frame_idioma.pack(fill="both", expand=True, padx=50, pady=150)

lbl_idioma = ctk.CTkLabel(frame_idioma, text="Selecione o Idioma Base / Target Language", font=("Segoe UI", 20, "bold"))
lbl_idioma.pack(pady=20)

combo_idioma = ctk.CTkComboBox(frame_idioma, values=list(LANGUAGES.keys()), font=("Segoe UI", 16), width=300, height=40)
combo_idioma.set("Português (Brasil)")
combo_idioma.pack(pady=20)

btn_iniciar = ctk.CTkButton(frame_idioma, text="INICIAR SISTEMA", font=("Segoe UI", 16, "bold"), height=50, command=iniciar_sistema)
btn_iniciar.pack(pady=20)

# FRAME 2: MENU PRINCIPAL
frame_principal = ctk.CTkFrame(app, fg_color="transparent")

lbl_titulo = ctk.CTkLabel(frame_principal, text="", font=("Segoe UI", 24, "bold"), text_color="#3a7ebf")
lbl_titulo.pack(pady=10)

# Organização dos botões em Grid (Tabela) para colocar os textos embaixo
frame_botoes = ctk.CTkFrame(frame_principal, fg_color="transparent")
frame_botoes.pack(pady=10)

btn_font_style = ("Segoe UI", 14, "bold")
desc_font_style = ("Segoe UI", 11)

# Botão 1: Backup
btn_backup = ctk.CTkButton(frame_botoes, text="", font=btn_font_style, height=40, width=280, state="disabled", command=acao_backup)
btn_backup.grid(row=0, column=0, padx=15, pady=(15, 2))
lbl_desc_backup = ctk.CTkLabel(frame_botoes, text="", font=desc_font_style, text_color="gray")
lbl_desc_backup.grid(row=1, column=0, padx=15, pady=(0, 15))

# Botão 2: Traduzir
btn_traduzir = ctk.CTkButton(frame_botoes, text="", font=btn_font_style, height=40, width=280, state="disabled", command=acao_traduzir)
btn_traduzir.grid(row=0, column=1, padx=15, pady=(15, 2))
lbl_desc_traduzir = ctk.CTkLabel(frame_botoes, text="", font=desc_font_style, text_color="gray")
lbl_desc_traduzir.grid(row=1, column=1, padx=15, pady=(0, 15))

# Botão 3: Instalar
btn_instalar = ctk.CTkButton(frame_botoes, text="", font=btn_font_style, height=40, width=280, state="disabled", command=acao_instalar, fg_color="#28a745", hover_color="#218838")
btn_instalar.grid(row=2, column=0, padx=15, pady=(15, 2))
lbl_desc_instalar = ctk.CTkLabel(frame_botoes, text="", font=desc_font_style, text_color="gray")
lbl_desc_instalar.grid(row=3, column=0, padx=15, pady=(0, 15))

# Botão 4: Ajustar Fonte
btn_fonte = ctk.CTkButton(frame_botoes, text="", font=btn_font_style, height=40, width=280, state="disabled", command=acao_ajustar_fonte, fg_color="#d39e00", hover_color="#c69500")
btn_fonte.grid(row=2, column=1, padx=15, pady=(15, 2))
lbl_desc_fonte = ctk.CTkLabel(frame_botoes, text="", font=desc_font_style, text_color="gray")
lbl_desc_fonte.grid(row=3, column=1, padx=15, pady=(0, 15))

barra_progresso = ctk.CTkProgressBar(frame_principal, variable=progresso_var, width=590, height=15)
barra_progresso.pack(pady=15)

texto_log = ctk.CTkTextbox(frame_principal, width=700, height=220, font=("Consolas", 13), state="disabled", fg_color="#1e1e1e", text_color="#00ff00")
texto_log.pack(pady=10)

# Inicia o loop da aplicação
app.mainloop()