import os
import json
import time
import urllib.request
import urllib.parse
import re
import sys
import concurrent.futures

# ==============================================================================
#  CONFIGURAÇÕES DO MODO LOTE (ZUMBI)
# ==============================================================================
LINGUAS_ALVO = ["es", "fr", "de", "zh-CN"]

# Substitua pelo caminho exato se o script não encontrar automaticamente
GAME_DIR = r"C:\Program Files (x86)\Steam\steamapps\common\Look Outside\data"

# ==============================================================================
#  VARIÁVEIS DE ESTADO
# ==============================================================================
memoria_atual = {}
textos_coletados = set()

CODIGOS_PERMITIDOS = [401, 402, 405, 102, 108, 408]
CAMPOS_DB_SEGUROS = ["name", "description", "nickname", "profile", "message1", "message2", "message3", "message4"]
ARQUIVOS_DB = ["Actors.json", "Classes.json", "Skills.json", "Items.json", "Weapons.json", "Armors.json", "Enemies.json", "States.json"]

def limpar_codigos_rpg(texto):
    texto = re.sub(r'\\ ?([a-zA-Z])', r'\\\1', texto)
    texto = re.sub(r'\[ ?(\d+) ?\]', r'[\1]', texto)
    texto = texto.replace('\\ n', '\n').replace('\\N', '\n')
    return texto

def carregar_memoria(arquivo_cache):
    if os.path.exists(arquivo_cache):
        try:
            with open(arquivo_cache, 'r', encoding='utf-8') as f: return json.load(f)
        except: return {}
    return {}

def salvar_memoria(arquivo_cache):
    with open(arquivo_cache, 'w', encoding='utf-8') as f:
        json.dump(memoria_atual, f, ensure_ascii=False, indent=4)

def extrair_texto(texto):
    if not texto or not isinstance(texto, str) or not texto.strip(): return
    if re.match(r'^[\W\d_]+$', texto.replace('\\', '')): return
    textos_coletados.add(texto)

def proc_db_extract(dados):
    if isinstance(dados, list):
        for item in dados:
            if not item: continue
            for c in CAMPOS_DB_SEGUROS:
                if c in item and isinstance(item[c], str): extrair_texto(item[c])

def proc_ev_extract(lista):
    if not isinstance(lista, list): return
    for cmd in lista:
        if not isinstance(cmd, dict): continue
        code = cmd.get("code")
        params = cmd.get("parameters")
        if not params: continue
        
        if code in CODIGOS_PERMITIDOS:
            if code == 102:
                if len(params) > 0 and isinstance(params[0], list):
                    for p in params[0]: 
                        if isinstance(p, str): extrair_texto(p)
            elif code == 402:
                if len(params) > 1 and isinstance(params[1], str): extrair_texto(params[1])
            else:
                if len(params) > 0 and isinstance(params[0], str): extrair_texto(params[0])

def proc_map_extract(dados):
    if isinstance(dados, list):
        for item in dados:
            if item and "list" in item: proc_ev_extract(item["list"])
    elif isinstance(dados, dict):
        if "events" in dados and isinstance(dados["events"], list):
            for ev in dados["events"]:
                if not ev: continue
                if "pages" in ev:
                    for pag in ev["pages"]:
                        if "list" in pag: proc_ev_extract(pag["list"])

def proc_troop_extract(dados):
    if isinstance(dados, list):
        for troop in dados:
            if not troop: continue
            if "name" in troop and isinstance(troop["name"], str): extrair_texto(troop["name"])
            if "pages" in troop:
                for pag in troop["pages"]:
                    if "list" in pag: proc_ev_extract(pag["list"])

def proc_sys_extract(dados):
    if "gameTitle" in dados: extrair_texto(dados["gameTitle"])
    if "terms" in dados:
        t = dados["terms"]
        for c in ["basic", "commands", "params"]:
            if c in t:
                for p in t[c]: extrair_texto(p)
        if "messages" in t:
            for k, v in t["messages"].items(): extrair_texto(v)

def traduzir_api(texto, lang):
    try:
        texto_safe = texto.replace('\n', ' {BR} ')
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={lang}&dt=t&q=" + urllib.parse.quote(texto_safe)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            dados = json.loads(response.read().decode('utf-8'))
            trad = ""
            if dados and len(dados) > 0 and dados[0]:
                for pedaco in dados[0]:
                    if pedaco and len(pedaco) > 0 and pedaco[0]: trad += pedaco[0]
            
            trad = trad.replace(' {BR} ', '\n').replace('{BR}', '\n')
            time.sleep(0.2) 
            return limpar_codigos_rpg(trad)
    except:
        return texto

if __name__ == "__main__":
    print("=" * 60)
    print(" MODO ZUMBI INICIADO - GERADOR DE CACHE EM LOTE")
    print("=" * 60)
    
    if not os.path.exists(GAME_DIR):
        print(f"\n[ERRO] Pasta 'data' do jogo não encontrada em:\n{GAME_DIR}")
        print("\nVerifique se o caminho no inicio do script (GAME_DIR) esta correto.")
        input("\nPressione ENTER para sair...")
        sys.exit()

    arquivos = [f for f in os.listdir(GAME_DIR) if f.endswith('.json')]
    arquivos.sort(key=lambda x: os.path.getsize(os.path.join(GAME_DIR, x)))
    mapa_regex = re.compile(r"Map\d+\.json")

    print("\n[1/3] Varrendo arquivos do jogo para encontrar textos...")
    for arq in arquivos:
        try:
            with open(os.path.join(GAME_DIR, arq), 'r', encoding='utf-8') as f: dados = json.load(f)
            if arq == "System.json": proc_sys_extract(dados)
            elif arq == "Troops.json": proc_troop_extract(dados)
            elif arq in ARQUIVOS_DB: proc_db_extract(dados)
            elif arq == "CommonEvents.json" or mapa_regex.match(arq): proc_map_extract(dados)
        except: pass
    
    print(f"      -> {len(textos_coletados)} frases únicas encontradas no jogo inteiro.")

    pasta_script = os.path.dirname(os.path.abspath(__file__))
    
    for lang in LINGUAS_ALVO:
        arquivo_cache = os.path.join(pasta_script, f"memoria_traducoes_{lang}.json")
        memoria_atual = carregar_memoria(arquivo_cache)
        
        pendentes = [t for t in textos_coletados if t not in memoria_atual]
        total = len(pendentes)
        
        print("\n" + "=" * 60)
        print(f" INICIANDO IDIOMA: {lang.upper()}")
        print(f" Arquivo: memoria_traducoes_{lang}.json")
        print(f" Frases pendentes: {total}")
        print("=" * 60)

        if total == 0:
            print(" [OK] Idioma já está 100% traduzido! Pulando...")
            continue

        salvos = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futuros = {executor.submit(traduzir_api, texto, lang): texto for texto in pendentes}
            
            for i, futuro in enumerate(concurrent.futures.as_completed(futuros)):
                texto_original = futuros[futuro]
                try:
                    resultado = futuro.result()
                    memoria_atual[texto_original] = resultado
                    salvos += 1
                    
                    if salvos % 20 == 0:
                        salvar_memoria(arquivo_cache)
                    
                    print(f"[{i+1}/{total}] {lang.upper()}: OK")
                except Exception as e:
                    print(f"[{i+1}/{total}] {lang.upper()}: ERRO -> {e}")
        
        salvar_memoria(arquivo_cache)
        print(f"\n[SUCESSO] Idioma {lang.upper()} finalizado e salvo!\n")
        time.sleep(2) 

    print("\n=" * 60)
    print(" MODO ZUMBI FINALIZADO! VOCÊ PODE IR DORMIR TRANQUILO.")
    print("=" * 60)
    input("\nPressione ENTER para fechar...")