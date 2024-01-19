import re

from .config import load_config


def carregar_regras():
    config = load_config()

    regex_toml = config["regex"]

    #print(f"TOML: {regex_toml}")
    return regex_toml

def aplicar_regex(texto, regras):
    resultados = []
    for regra in regras:
        nome = regra["nome"]
        padrao = regra["padrao"]
        correspondencias = re.findall(padrao, texto)
        if correspondencias:
            resultados.append(nome)
    return ', '.join(resultados) if resultados else "Regex não encontrado"

def regex(texto):
    regras = carregar_regras()
    regex_result = aplicar_regex(texto, regras)
    #print(f"Título: {texto}, Resultado: {regex_result}")
    return regex_result