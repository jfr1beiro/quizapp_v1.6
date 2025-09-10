
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 GERADOR DE QUESTÕES - SCRIPT PRINCIPAL
Baseado no modelo fornecido pelo usuário
"""

import json
import os
from typing import List, Dict

class GeradorQuestoes:
    def __init__(self):
        self.arquivo_destino = "perguntas_professor_apenas.json"
        self.questoes_existentes = []
        self.configuracoes = {}

    def mostrar_banner(self):
        """Banner do programa"""
        print("=" * 70)
        print("🎯 GERADOR DE QUESTÕES - FORMATO CORRETO")
        print("=" * 70)
        print("📚 Gera questões no formato que funciona no site")
        print("🎯 Baseado no modelo fornecido pelo usuário")
        print("✅ Integração com arquivo existente")
        print("=" * 70)
        print()

    def solicitar_configuracoes(self):
        """Solicita todas as configurações necessárias"""
        print("⚙️  CONFIGURAÇÕES DAS QUESTÕES")
        print("-" * 40)

        # 1. Período
        while True:
            try:
                periodo = input("📊 Em qual período essas questões devem aparecer? (1-8): ").strip()
                periodo = int(periodo)
                if 1 <= periodo <= 8:
                    self.configuracoes['periodo'] = periodo
                    print(f"✅ Período: {periodo}")
                    break
                else:
                    print("❌ Período deve ser entre 1 e 8!")
            except ValueError:
                print("❌ Digite um número válido!")

        # 2. Disciplina
        disciplina = input("📚 Nome da disciplina: ").strip()
        if not disciplina:
            disciplina = "GESTÃO DA QUALIDADE E SEGURANÇA DO PACIENTE"
        self.configuracoes['disciplina'] = disciplina
        print(f"✅ Disciplina: {disciplina}")

        # 3. Categoria/Tema
        categoria = input("🎯 Categoria/tema específico do conteúdo: ").strip()
        if not categoria:
            categoria = "Segurança do Paciente"
        self.configuracoes['categoria'] = categoria
        print(f"✅ Categoria: {categoria}")

        # 4. Fonte do material (sempre professor)
        fonte = input("👨‍🏫 Este material é do professor? (s/n): ").strip().lower()
        self.configuracoes['fonte_material'] = "professor" if fonte in ['s', 'sim'] else "geral"
        print(f"✅ Fonte: {self.configuracoes['fonte_material']}")

        # 5. Quantidade
        while True:
            try:
                qtd = input("📁 Quantas questões gerar? (padrão: 50): ").strip()
                if not qtd:
                    qtd = 50
                else:
                    qtd = int(qtd)
                if qtd > 0:
                    self.configuracoes['quantidade'] = qtd
                    print(f"✅ Quantidade: {qtd}")
                    break
                else:
                    print("❌ Quantidade deve ser maior que zero!")
            except ValueError:
                print("❌ Digite um número válido!")

        print("\n" + "=" * 50)
        print("📋 CONFIGURAÇÕES CONFIRMADAS:")
        for chave, valor in self.configuracoes.items():
            print(f"   • {chave}: {valor}")
        print("=" * 50)

    def carregar_questoes_existentes(self):
        """Carrega questões já existentes"""
        if os.path.exists(self.arquivo_destino):
            try:
                with open(self.arquivo_destino, 'r', encoding='utf-8') as f:
                    self.questoes_existentes = json.load(f)
                print(f"✅ Carregadas {len(self.questoes_existentes)} questões existentes")
            except Exception as e:
                print(f"⚠️ Erro ao carregar: {e}")
                self.questoes_existentes = []
        else:
            print("📝 Arquivo será criado novo")
            self.questoes_existentes = []

    def criar_questao_modelo(self, pergunta: str, opcoes: List[str], resposta_correta: str, 
                           explicacao: str, id_numero: int) -> Dict:
        """Cria questão seguindo EXATAMENTE o modelo fornecido"""

        # Prefixo da pergunta baseado na fonte
        if self.configuracoes['fonte_material'] == "professor":
            pergunta_formatada = f"👨‍🏫 **[PROFESSOR]** {pergunta}"
        else:
            pergunta_formatada = pergunta

        # Tema para referência
        tema = self.configuracoes['categoria']

        return {
            "pergunta": pergunta_formatada,
            "opcoes": opcoes,
            "resposta_correta": resposta_correta,
            "categoria": self.configuracoes['categoria'],
            "periodo": self.configuracoes['periodo'],  # NÚMERO
            "disciplina": self.configuracoes['disciplina'],
            "dificuldade": "medio",
            "explicacao": f"Baseado nos apontamentos do professor: {explicacao}",
            "referencia": f"Apontamentos Prof. - {tema}",
            "fonte_material": self.configuracoes['fonte_material'],
            "legenda": "📚 Material extraído de aula presencial",
            "prioridade_selecao": 0.7,
            "id_professor": f"PROF_{id_numero}"
        }

    def adicionar_questoes_ao_arquivo(self, novas_questoes: List[Dict]):
        """Adiciona questões ao arquivo existente"""
        print(f"\n💾 Adicionando {len(novas_questoes)} questões ao arquivo...")

        # Carregar questões existentes
        self.carregar_questoes_existentes()

        # Adicionar novas questões
        self.questoes_existentes.extend(novas_questoes)

        # Salvar arquivo atualizado
        try:
            with open(self.arquivo_destino, 'w', encoding='utf-8') as f:
                json.dump(self.questoes_existentes, f, ensure_ascii=False, indent=2)

            print(f"✅ Arquivo salvo: {self.arquivo_destino}")
            print(f"📊 Total de questões: {len(self.questoes_existentes)}")

        except Exception as e:
            print(f"❌ Erro ao salvar: {e}")

    def executar(self):
        """Executa o programa principal"""
        self.mostrar_banner()
        self.solicitar_configuracoes()

        print("\n🚀 CONFIGURAÇÕES PRONTAS!")
        print("Agora você pode:")
        print("1. Enviar PDFs no chat")
        print("2. Questões serão geradas com estas configurações")
        print("3. Formato garantido para funcionar no site")

        return self.configuracoes

def main():
    gerador = GeradorQuestoes()
    configuracoes = gerador.executar()

    print("\n✅ SCRIPT CONFIGURADO!")
    print("Envie PDFs no chat para gerar questões!")

if __name__ == "__main__":
    main()
