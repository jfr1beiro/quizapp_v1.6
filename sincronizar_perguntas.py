import argparse
import json
import os
import re
import shutil
from datetime import datetime

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    load_dotenv = None  # optional


def load_env_variables() -> None:
    if load_dotenv:
        try:
            load_dotenv()
        except Exception:
            pass


def read_json(path: str):
    with open(path, 'r', encoding='utf-8') as file_handle:
        return json.load(file_handle)


def safe_write_json(file_path: str, data) -> None:
    tmp_path = f"{file_path}.tmp"
    with open(tmp_path, 'w', encoding='utf-8') as tmp_handle:
        json.dump(data, tmp_handle, ensure_ascii=False, indent=2)
    os.replace(tmp_path, file_path)


def ensure_directory_exists(path: str) -> None:
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)


def backup_file(path: str) -> str:
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{path}.backup_{timestamp}"
    ensure_directory_exists(backup_path)
    shutil.copy(path, backup_path)
    return backup_path


def extract_questions(data) -> list:
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and 'perguntas' in data and isinstance(data['perguntas'], list):
        return data['perguntas']
    raise ValueError('Formato não reconhecido. Use uma lista de perguntas ou um objeto {"perguntas": [...]}')


def normalize_text(value: str) -> str:
    return ' '.join((value or '').strip().split()).lower()


def question_key(question: dict) -> tuple:
    pergunta_text = normalize_text(question.get('pergunta', ''))
    opcoes = tuple(normalize_text(opt) for opt in question.get('opcoes', []) or [])
    disciplina = normalize_text(question.get('disciplina', ''))
    periodo = question.get('periodo')
    return (pergunta_text, opcoes, disciplina, periodo)


def merge_questions(existing_questions: list, new_questions: list) -> tuple:
    existing_keys = {question_key(q) for q in existing_questions}
    unique_new_questions = []
    duplicated = 0
    for q in new_questions:
        if question_key(q) in existing_keys:
            duplicated += 1
            continue
        unique_new_questions.append(q)
    merged = existing_questions + unique_new_questions
    return merged, len(unique_new_questions), duplicated


def detect_default_staging_file() -> str:
    candidates = [
        'perguntas_staging.json',
        'perguntas_test.json',
        os.path.join('data', 'perguntas_staging.json'),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return 'perguntas_staging.json'


def get_main_bank_path(args_main: str | None) -> str:
    if args_main:
        return args_main
    load_env_variables()
    env_path = os.environ.get('PERGUNTAS_JSON_PATH')
    if env_path:
        return env_path
    return os.path.join('data', 'perguntas.json')


def mirror_local_copy(merged_questions: list, destination: str) -> None:
    ensure_directory_exists(destination)
    safe_write_json(destination, merged_questions)


def list_json_files_recursively(root_directory: str, glob_extension: str = '.json') -> list:
    collected_paths = []
    for current_directory, _subdirs, files in os.walk(root_directory):
        for filename in files:
            if filename.lower().endswith(glob_extension.lower()):
                collected_paths.append(os.path.join(current_directory, filename))
    return sorted(collected_paths)


def infer_period_from_directory(path: str) -> int | None:
    parts = os.path.normpath(path).split(os.sep)
    for segment in reversed(parts):
        match = re.match(r'^periodo[_\- ]?(\d+)$', segment.strip(), flags=re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except Exception:
                return None
    return None


def infer_discipline_from_filename(path: str) -> str | None:
    stem = os.path.splitext(os.path.basename(path))[0]
    cleaned = re.sub(r'[_\-]+', ' ', stem).strip()
    cleaned = re.sub(r'\s+', ' ', cleaned)
    if not cleaned:
        return None
    return cleaned.title()


def load_questions_from_staging_files(
    file_paths: list,
    default_period: int | None,
    default_discipline: str | None,
    enable_period_inference: bool,
    enable_discipline_inference: bool,
) -> list:
    aggregated_questions: list = []
    for file_path in file_paths:
        data = read_json(file_path)
        questions = extract_questions(data)

        inferred_period = infer_period_from_directory(os.path.dirname(file_path)) if enable_period_inference else None
        inferred_discipline = infer_discipline_from_filename(file_path) if enable_discipline_inference else None

        for question in questions:
            if 'periodo' not in question or question.get('periodo') in [None, '', 0]:
                period_value = inferred_period if inferred_period is not None else default_period
                if period_value is not None:
                    question['periodo'] = period_value

            if not question.get('disciplina'):
                discipline_value = inferred_discipline if inferred_discipline else default_discipline
                if discipline_value:
                    question['disciplina'] = discipline_value

            aggregated_questions.append(question)

    return aggregated_questions


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            'Sincroniza perguntas de um arquivo de staging (ex.: perguntas_test.json) '
            'para o banco principal (PERGUNTAS_JSON_PATH), com backup e deduplicação.'
        )
    )
    parser.add_argument(
        '--staging',
        type=str,
        default=detect_default_staging_file(),
        help='Caminho do arquivo de staging com novas perguntas (padrão: tenta detectar automaticamente)'
    )
    parser.add_argument(
        '--staging-dir',
        type=str,
        default=None,
        help='Diretório contendo arquivos de staging organizados (ex.: periodo_2/Disciplina.json)'
    )
    parser.add_argument(
        '--main',
        type=str,
        default=None,
        help='Caminho do banco principal. Se ausente, usa PERGUNTAS_JSON_PATH ou data/perguntas.json'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Apenas mostra o que será feito, sem escrever arquivos'
    )
    parser.add_argument(
        '--no-mirror-local',
        action='store_true',
        help='Não espelhar automaticamente a cópia local em data/perguntas.json'
    )
    parser.add_argument(
        '--mirror-local-dest',
        type=str,
        default=os.path.join('data', 'perguntas.json'),
        help='Destino do espelhamento local (padrão: data/perguntas.json)'
    )
    parser.add_argument(
        '--infer-period-from-dir',
        action='store_true',
        help='Inferir automaticamente o período a partir do nome do diretório (ex.: periodo_2)'
    )
    parser.add_argument(
        '--infer-discipline-from-filename',
        action='store_true',
        help='Inferir automaticamente a disciplina a partir do nome do arquivo (ex.: Anatomia.json -> Anatomia)'
    )
    parser.add_argument(
        '--periodo',
        type=int,
        default=None,
        help='Período padrão para atribuir às perguntas sem período quando não for possível inferir'
    )
    parser.add_argument(
        '--disciplina',
        type=str,
        default=None,
        help='Disciplina padrão para atribuir às perguntas sem disciplina quando não for possível inferir'
    )

    args = parser.parse_args()

    staging_path = args.staging
    main_bank_path = get_main_bank_path(args.main)
    mirror_dest = None if args.no_mirror_local else args.mirror_local_dest

    if not os.path.exists(staging_path) and not args.staging_dir:
        raise SystemExit(f"Arquivo de staging não encontrado: {staging_path} (ou informe --staging-dir)")

    if not os.path.exists(main_bank_path):
        raise SystemExit(f"Banco principal não encontrado: {main_bank_path}")

    try:
        main_data = read_json(main_bank_path)
        main_questions = extract_questions(main_data)

        staging_questions: list = []

        if args.staging_dir and os.path.exists(args.staging_dir):
            files = list_json_files_recursively(args.staging_dir, '.json')
            if not files:
                print(f"Aviso: nenhum JSON encontrado em {args.staging_dir}")
            staged_from_dir = load_questions_from_staging_files(
                file_paths=files,
                default_period=args.periodo,
                default_discipline=args.disciplina,
                enable_period_inference=bool(args.infer_period_from_dir),
                enable_discipline_inference=bool(args.infer_discipline_from_filename),
            )
            staging_questions.extend(staged_from_dir)

        if os.path.exists(staging_path):
            staging_data = read_json(staging_path)
            staged_from_file = extract_questions(staging_data)
            staging_questions.extend(staged_from_file)
    except Exception as exc:
        raise SystemExit(f"Erro ao carregar JSON: {exc}")

    merged_questions, added_count, duplicated_count = merge_questions(main_questions, staging_questions)

    print('Resumo da sincronização:')
    print(f"- Banco principal atual: {len(main_questions)} perguntas")
    print(f"- Novas no staging:     {len(staging_questions)} perguntas")
    print(f"- Adicionadas:           {added_count}")
    print(f"- Duplicadas/ignoradas:  {duplicated_count}")
    print(f"- Total após merge:      {len(merged_questions)}")

    if args.dry_run:
        print('\nExecução em modo dry-run. Nenhum arquivo foi modificado.')
        return

    # Backup do banco principal
    try:
        backup_path = backup_file(main_bank_path)
        print(f"Backup criado do banco principal: {backup_path}")
    except Exception as exc:
        raise SystemExit(f"Falha ao criar backup do banco principal: {exc}")

    # Salva o merge no banco principal
    try:
        ensure_directory_exists(main_bank_path)
        safe_write_json(main_bank_path, merged_questions)
        print(f"Banco principal atualizado: {main_bank_path}")
    except Exception as exc:
        raise SystemExit(f"Falha ao salvar banco principal: {exc}")

    # Espelha cópia local (opcional, habilitado por padrão)
    if mirror_dest:
        try:
            if os.path.abspath(mirror_dest) != os.path.abspath(main_bank_path):
                mirror_local_copy(merged_questions, mirror_dest)
                print(f"Cópia local espelhada: {mirror_dest}")
        except Exception as exc:
            print(f"Aviso: falha ao espelhar cópia local ({mirror_dest}): {exc}")

    print('\nSincronização concluída com sucesso.')


if __name__ == '__main__':
    main()


