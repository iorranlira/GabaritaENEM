import json
import os
import re

from chuncking import (
    extrair_texto_pdf,
    separar_questoes,
    extrair_gabarito,
    montar_dataset,
    salvar_json,
    limpar_texto_bruto
)


def processar_prova(ano):

    caminho_prova = f"dataset/provas/prova_{ano}.pdf"
    caminho_gabarito = f"dataset/gabaritos/gabarito_{ano}.pdf"

    print(f"\nProcessando prova {ano}...")

    # ===== PROVA =====
    texto_prova = extrair_texto_pdf(caminho_prova)
    texto_prova = limpar_texto_bruto(texto_prova)
    questoes = separar_questoes(texto_prova)

    print(f"{len(questoes)} questões encontradas")

    # ===== GABARITO =====
    gabarito = extrair_gabarito(caminho_gabarito)

    print(f"Gabaritos encontrados: {len(gabarito)}")

    # ===== DATASET =====
    dataset = montar_dataset(ano, questoes, gabarito)
    salvar_json(dataset, ano)
    return dataset
    
def processar_todas_provas():

    pasta_provas = "dataset/provas"

    arquivos = os.listdir(pasta_provas)

    anos = []

    for nome in arquivos:
        match = re.match(r"prova_(\d{4})\.pdf", nome)
        if match:
            anos.append(int(match.group(1)))

    anos.sort()

    print(f"{len(anos)} provas encontradas no dataset\n")

    total_questoes = 0

    for ano in anos:
        dataset = processar_prova(ano)

        total_questoes += len(dataset)

        print(f"{len(dataset)} questões válidas em {ano}")

    print("Provas processadas:", len(anos))
    print("Total de questões válidas:", total_questoes)

def main():

    #ano = 2022

    #dataset = processar_prova(ano)

    #print("\nExemplo de questão extraída:\n")

    #print(json.dumps(dataset[0], indent=2, ensure_ascii=False))

    #print("\nTotal de questões:", len(dataset))
    processar_todas_provas()

if __name__ == "__main__":
    main()