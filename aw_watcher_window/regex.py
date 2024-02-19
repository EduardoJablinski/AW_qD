import re

from .config import load_config
from collections import deque

assign_last_value = True
lista_regex = deque(maxlen=3)

def carregar_regras():
    config = load_config()

    regex_toml = config["regex"]

    #print(f"TOML: {regex_toml}")
    return regex_toml

def aplicar_regex(texto, regras):
    global assign_last_value
    resultados = []

    for regra in regras:
        nome = regra["nome"]
        padrao = regra["padrao"]
        correspondencias = re.findall(padrao, texto)
        if correspondencias:
            resultados.append(nome)

    if resultados:
        assign_last_value = True    
        return ', '.join(resultados)
    elif assign_last_value and lista_regex:
        assign_last_value = False
        last_value = lista_regex[-1]
        if last_value:
            return f"{last_value} (***)"
        else:
            return "Regex não encontrado"
    elif lista_regex:
        return lista_regex[-1]
    else:
        return "Regex não encontrado"

def regex(texto):
    regras = carregar_regras()
    regex_result = aplicar_regex(texto, regras)
    #print(f"Título: {texto}, Resultado: {regex_result}")
    lista_regex.append(regex_result)
    #print(f"Lista: {teste}")
    return regex_result
