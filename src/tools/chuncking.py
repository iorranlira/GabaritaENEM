import json
import re
import os
from pathlib import Path
import fitz

ROOT_DIR = Path(__file__).resolve().parents[2]

def extrair_texto_pdf(caminho):
    texto_total = ""
 
    doc = fitz.open(caminho)
 
    for page in doc:
        largura = page.rect.width
        meio    = largura / 2

        blocos = [b for b in page.get_text("blocks") if b[6] == 0 and b[4].strip()]
 
      
        col_esq = sorted([b for b in blocos if b[0] < meio],  key=lambda b: b[1])
        col_dir = sorted([b for b in blocos if b[0] >= meio], key=lambda b: b[1])
 
        
        for bloco in col_esq + col_dir:
            texto_bloco = bloco[4].strip()
            if texto_bloco:
                texto_total += texto_bloco + "\n"
 
        texto_total += "\n"  
 
    doc.close()
    return limpar_texto_bruto(texto_total)


def separar_questoes(texto):

    padrao = r"QUEST[ÃA]O\s*0*(\d{1,3})"
    partes = re.split(padrao, texto, flags=re.IGNORECASE)

    questoes = []

    for i in range(1, len(partes), 2):

        numero = int(partes[i])
        conteudo = partes[i+1].strip()

        questoes.append({
            "numero": numero,
            "texto": conteudo
        })

    return questoes


def extrair_alternativas(texto):
    padrao = r"\n([A-E])\s+(.*?)(?=\n[A-E]\s+|\Z)"
    matches = re.findall(padrao, texto, re.S)

    if not matches:
        return None

    alternativas = {}

    for letra, conteudo in matches:
        alternativas[letra] = conteudo.strip()
    return alternativas


def extrair_enunciado(texto):

    match = re.search(r"\n[A-E][\)\.]?\s+", texto)

    if match:
        return texto[:match.start()].strip()

    return texto.strip()


def get_area(numero_questao):
    if 1 <= numero_questao <= 45:
        return "Linguagens, Códigos e suas Tecnologias"
    elif 46 <= numero_questao <= 90:
        return "Ciências Humanas e suas Tecnologias"
    elif 91 <= numero_questao <= 135:
        return "Ciências da Natureza e suas Tecnologias"
    elif 136 <= numero_questao <= 180:
        return "Matemática e suas Tecnologias"
    else:
        return "Desconhecida"


def extrair_gabarito(caminho):

    doc = fitz.open(caminho)
    gabarito = {}

    for page in doc:

        words = page.get_text("words")

        numeros = [
            w for w in words
            if re.fullmatch(r'\d{1,3}', w[4]) and 1 <= int(w[4]) <= 185
        ]

        letras = [
            w for w in words
            if re.fullmatch(r'[A-E]', w[4])
        ]

        for num_word in numeros:

            numero = int(num_word[4])
            ny0 = num_word[1]
            nx1 = num_word[2]

            candidatas = [
                l for l in letras
                if abs(l[1] - ny0) <= 4 and l[0] > nx1
            ]

            if candidatas:
                letra_mais_proxima = min(candidatas, key=lambda l: l[0] - nx1)
                gabarito[numero] = letra_mais_proxima[4]

    doc.close()

    return gabarito


def limpar_texto_bruto(texto):

    # remove repetições tipo ENEM2024ENEM2024
    texto = re.sub(r'(ENEM\s*\d{4})+', '', texto)

    # remove variações tipo ENEM20E4 ou ENEN2025
    texto = re.sub(r'ENE[M|N]\s*\d{2}[A-Z]?\d', '', texto)

    # remove cabeçalhos da prova
    texto = re.sub(
        r'LINGUAGENS.*?AZUL',
        '',
        texto,
        flags=re.IGNORECASE
    )

     # remove cabeçalhos da prova
    texto = re.sub(r'LINGUAGENS, CÓDIGOS E SUAS TECNOLOGIAS.*', '', texto)

    texto = re.sub(r'\*\d+[A-Z]+\d+\*', '', texto) ##
    
    # remove rodapé tipo LC - 1° dia | Caderno
    texto = re.sub(r'LC\s*-\s*.*', '', texto)

    # remover cabeçalho automaticamente
    texto = re.sub(r'[A-ZÇÃÉ\s]+TECNOLOGIAS\s*•\s*\dº DIA\s*•\s*CADERNO\s*\d+\s*•\s*AZUL\s*•?', '', texto)
    # remove rodapés tipo: CH - 1° dia | Caderno 1 - AZUL - 1ª Aplicação
    texto = re.sub(r'[A-Z]{2}\s*-\s*\d°\s*dia\s*\|\s*Caderno\s*\d+\s*-\s*AZUL\s*-\s*\dª\s*Aplicação', '', texto)

    # remove variação: CN - 2° dia | Caderno 7 - AZUL - 1ª Aplicação
    texto = re.sub(r'CN\s*-\s*\d°\s*dia\s*\|\s*Caderno\s*\d+\s*-\s*AZUL\s*-\s*\dª\s*Aplicação', '', texto)

    # remove blocos institucionais completos
    texto = re.sub(r'CIÊNCIAS DA NATUREZA E SUAS TECNOLOGIAS\s*•\s*\dº DIA\s*•\s*CADERNO\s*\d+\s*•\s*AZUL\s*•?', '', texto)

    texto = re.sub(r'MATEMÁTICA E SUAS TECNOLOGIAS\s*•\s*\dº DIA\s*•\s*CADERNO\s*\d+\s*•\s*AZUL\s*•?', '', texto)
    
    texto = re.sub(r'Questões de \d+ a \d+', '', texto)

###
    texto = re.sub(r'^[A-E]\t\s*', '', texto)
    texto = re.sub(r'[A-ZÁÉÍÓÚÂÊÔÃÕÇ\s]+TECNOLOGIAS', '', texto)
    texto = texto.replace("\t", " ")
###
    texto = re.sub(
        r"(CH|LC|CN|MT)\s*-\s*\dº\s*dia\s*\|\s*Caderno\s*\d+\s*-\s*AZUL\s*-\s*Página\s*\d+",
        "",
        texto
    )

    texto = re.sub(r"\*?AZUL\d+[A-Z]+\d+\*?", "", texto)

    texto = re.sub(r"Página\s*\d+", "", texto)


    texto = re.sub(r"Página\s*\d+", "", texto)

    texto = re.sub(r'([A-Z])\1+', r'\1', texto)

    return texto.strip()


def questao_valida(q):

    if not q["enunciado"]:
        return False

    if len(q["enunciado"]) < 40:
        return False

    if not q["alternativas"]:
        return False

    if len(q["alternativas"]) != 5:
        return False

    if q["gabarito"] not in ["A", "B", "C", "D", "E"]:
        return False

    if not (1 <= q["numero_questao"] <= 180):
        return False

    return True

def montar_dataset(ano, questoes, gabarito):

    dataset = []
    questoes = sorted(questoes, key=lambda x: x["numero"]) 

    for q in questoes:
        alternativas = extrair_alternativas(q["texto"])
        enunciado = (extrair_enunciado(q["texto"]))

        numero = q["numero"] 
        resposta = gabarito.get(numero)

        item = ({
            "ano": ano,
            "area": get_area(numero),
            "numero_questao": numero,
            "enunciado": enunciado,
            "alternativas": alternativas,
            "gabarito": resposta,
        })

        if questao_valida(item):
            dataset.append(item)

    return dataset


def salvar_json(dataset, ano):
    diretorio = ROOT_DIR / "processed"
    
    if not os.path.exists(diretorio):
        os.makedirs(diretorio)
        print(f"Pasta '{diretorio}' criada com sucesso!")

    caminho_arquivo = f"{diretorio}/enem_{ano}_99.json"
    
    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=4, ensure_ascii=False)
    
    print(f"Arquivo salvo em: {caminho_arquivo}")
