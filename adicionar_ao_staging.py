#!/usr/bin/env python3
"""
Script para adicionar perguntas ao arquivo de staging (perguntas_test.json)
mantendo o fluxo correto de trabalho.
"""

import json
import shutil
from datetime import datetime

def backup_file(path: str) -> str:
    """Cria backup do arquivo com timestamp"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{path}.backup_{timestamp}"
    shutil.copy(path, backup_path)
    return backup_path

def normalize_text(value: str) -> str:
    """Normaliza texto para comparação"""
    return ' '.join((value or '').strip().split()).lower()

def convert_question_format(question: dict) -> dict:
    """Converte formato da pergunta de genética para formato padrão"""
    converted = {
        "pergunta": question.get("questao", ""),
        "opcoes": question.get("alternativas", []),
        "resposta_correta": question.get("resposta_correta", ""),
        "categoria": question.get("categoria", ""),
        "periodo": question.get("periodo", 2),
        "disciplina": question.get("disciplina", ""),
        "dificuldade": question.get("dificuldade", "medio"),
        "explicacao": question.get("explicacao", "")
    }
    
    # Adicionar campos específicos se existirem
    if "fonte_professor" in question:
        converted["fonte_professor"] = question["fonte_professor"]
    if "prioridade_selecao" in question:
        converted["prioridade_selecao"] = question["prioridade_selecao"]
    
    return converted

def question_key(question: dict) -> tuple:
    """Cria chave única para detectar duplicatas"""
    pergunta_text = normalize_text(question.get('pergunta', ''))
    opcoes = tuple(normalize_text(opt) for opt in question.get('opcoes', []) or [])
    disciplina = normalize_text(question.get('disciplina', ''))
    periodo = question.get('periodo')
    return (pergunta_text, opcoes, disciplina, periodo)

def adicionar_perguntas_ao_staging(arquivo_origem: str, arquivo_staging: str = "perguntas_test.json"):
    """Adiciona perguntas ao arquivo de staging, evitando duplicatas"""
    
    print(f"🔄 ADICIONANDO PERGUNTAS AO STAGING")
    print(f"=" * 50)
    
    # Carregar arquivo de staging atual
    with open(arquivo_staging, 'r', encoding='utf-8') as f:
        staging_atual = json.load(f)
    
    print(f"📊 Staging atual: {len(staging_atual)} perguntas")
    
    # Carregar perguntas novas
    with open(arquivo_origem, 'r', encoding='utf-8') as f:
        perguntas_novas = json.load(f)
    
    print(f"📥 Perguntas novas: {len(perguntas_novas)} perguntas")
    
    # Criar conjunto de chaves existentes
    chaves_existentes = {question_key(q) for q in staging_atual}
    
    # Converter e filtrar perguntas novas
    perguntas_convertidas = []
    duplicatas = 0
    
    for pergunta in perguntas_novas:
        # Converter formato
        pergunta_convertida = convert_question_format(pergunta)
        chave = question_key(pergunta_convertida)
        
        if chave in chaves_existentes:
            duplicatas += 1
            continue
        
        perguntas_convertidas.append(pergunta_convertida)
        chaves_existentes.add(chave)  # Evitar duplicatas dentro do mesmo lote
    
    print(f"✅ Perguntas a adicionar: {len(perguntas_convertidas)}")
    print(f"🔄 Duplicatas ignoradas: {duplicatas}")
    
    if len(perguntas_convertidas) == 0:
        print(f"ℹ️ Nenhuma pergunta nova para adicionar.")
        return
    
    # Fazer backup
    backup_path = backup_file(arquivo_staging)
    print(f"💾 Backup criado: {backup_path}")
    
    # Adicionar perguntas ao staging
    staging_atualizado = staging_atual + perguntas_convertidas
    
    # Salvar arquivo atualizado
    with open(arquivo_staging, 'w', encoding='utf-8') as f:
        json.dump(staging_atualizado, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Staging atualizado: {len(staging_atualizado)} perguntas total")
    print(f"📁 Arquivo atualizado: {arquivo_staging}")
    print()
    print(f"🎯 PRÓXIMO PASSO:")
    print(f"   Execute o script de sincronização para processar o staging:")
    print(f"   python sincronizar_perguntas.py")
    print()

if __name__ == "__main__":
    # Executar para o arquivo de genética
    adicionar_perguntas_ao_staging(
        "materiais_estudo/periodo_2/morfofisiologia/banco_genetica_proteinas_100_questoes.json"
    )
