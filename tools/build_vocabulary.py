"""Migração reprodutível. Aprovação editorial pequena, sem promover o legado."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from stopots_v2.vocabulary import category_id, import_legacy, publish, upsert, canonical
from stopots_v2.sources import import_ibge, approve_ibge_geography

# Dados editoriais locais, revisados para associações comuns. Não constituem
# consenso do jogo, fonte externa ou garantia de aceitação comunitária.
BOOTSTRAP = {
    "Profissão": "Arquiteto|Bombeiro|Carpinteiro|Dentista|Engenheiro|Farmacêutico|Garçom|Historiador|Ilustrador|Jornalista|Lavrador|Médico|Nutricionista|Odontólogo|Professor|Químico|Radialista|Sapateiro|Taxista|Urologista|Veterinário|Zelador",
    "Programa de TV": "Altas Horas|Bom Dia Brasil|Cocoricó|Domingão do Faustão",
    "Fantasia": "Astronauta|Bruxa|Cavaleiro|Diabo",
    "Vilão": "Arlequina|Bowser|Coringa|Darth Vader",
    "Animal": "Arara|Baleia|Cachorro|Dromedário|Elefante|Foca|Gato|Hipopótamo|Iguana|Jacaré|Kiwi|Leão|Macaco|Narval|Onça|Pato|Quati|Raposa|Sapo|Tatu|Urso|Vaca|Wombat|Xexéu|Yak|Zebra",
    "Carro": "Argo|Brasília|Corsa|Duster",
    "Brinquedo": "Avião de brinquedo|Boneca|Carrinho|Dominó",
    "Objeto": "Anel|Balde|Caderno|Dado|Escova|Faca|Garrafa|Hélice|Isqueiro|Janela|Lápis|Mesa|Navalha|Óculos|Panela|Quadro|Relógio|Sapato|Tesoura|Urna|Vassoura|Xícara|Zíper",
    "Sabor de Pizza": "Atum|Bacon|Calabresa|Dois queijos",
    "Palavra em Inglês": "Apple|Book|Cat|Dog|Elephant|Flower|Green|House|Ice|Juice|Key|Lion|Moon|Night|Orange|Paper|Queen|Red|Sun|Table|Umbrella|Violin|Water|Xylophone|Yellow|Zebra",
    "Tem na academia": "Anilha|Barra|Colchonete|Dumbbell",
    "Remédio": "Aspirina|Buscopan|Captopril|Dipirona",
    "Comida": "Arroz|Batata|Carne|Doce de leite|Empada|Feijão|Goiabada|Hambúrguer|Iogurte|Jiló|Lasanha|Macarrão|Nhoque|Omelete|Pão|Quindim|Risoto|Sopa|Tapioca|Uva|Vatapá|Yakissoba",
    "Time Esportivo": "Arsenal|Botafogo|Corinthians|Dortmund",
    "Música": "Aquarela|Boate Azul|Carinhoso|Detalhes",
    "Ave": "Águia|Bem-te-vi|Canário|Dodo|Ema|Falcão|Galinha|Harpia|Irerê|João-de-barro|Kiwi|Lavadeira|Maritaca|Nambu|Pato|Quero-quero|Rolinha|Sabiá|Tucano|Urubu|Xexéu",
    "Cor": "Amarelo|Azul|Branco|Bege|Cinza|Dourado|Esmeralda|Ferrugem|Grená|Índigo|Laranja|Marrom|Negro|Ocre|Preto|Rosa|Roxo|Salmão|Turquesa|Verde|Vermelho|Violeta",
    "Fruta": "Abacate|Abacaxi|Banana|Caju|Damasco|Figo|Goiaba|Jabuticaba|Kiwi|Laranja|Maçã|Manga|Nectarina|Pera|Pêssego|Romã|Tangerina|Uva",
    "Cidade": "Aracaju|Belém|Curitiba|Diadema|Fortaleza|Goiânia|Manaus|Natal|Olinda|Recife|Salvador|Teresina|Vitória",
    "País": "Argentina|Brasil|Chile|Dinamarca|Equador|França|Guatemala|Honduras|Itália|Japão|Laos|México|Noruega|Omã|Peru|Quênia|Rússia|Suécia|Turquia|Uruguai|Venezuela|Zâmbia",
    "Nome Masculino": "André|Bruno|Carlos|Daniel|Eduardo|Felipe|Gabriel|Henrique|Igor|João|Lucas|Marcos|Nicolas|Otávio|Pedro|Rafael|Samuel|Tiago|Vinícius",
    "Nome Feminino": "Ana|Beatriz|Carla|Daniela|Elisa|Fernanda|Gabriela|Helena|Isabela|Júlia|Laura|Mariana|Natália|Olívia|Paula|Renata|Sofia|Tatiana|Vitória",
}


def build(recreate=False):
    data = ROOT / "data/source/editorial.json"
    release_path = ROOT / "src/stopots_v2/resources/vocabulary.json"
    if data.exists() and not recreate:
        manifest = publish(json.loads(data.read_text(encoding='utf-8')), release_path)
        print(json.dumps({'existing_editorial_preserved': True, 'release': manifest}, ensure_ascii=False))
        return
    original = ROOT / "stopots_bot/dictionary.json"
    labels = {label for cell in json.loads(original.read_text(encoding="utf-8")).values() for label in cell}
    labels |= set(BOOTSTRAP) | {"Estado", "Legume", "Verdura", "Nome", "Tem na academia"}
    taxonomy = {category_id(label): {"label": label, "language": "pt", "aliases": [], "includes": []} for label in sorted(labels)}
    for cid, language in [("palavra_em_ingles", "en"), ("palavra_em_espanhol", "es")]:
        taxonomy[cid]["language"] = language
    for parent, children in {"animal": ["ave", "mamifero", "inseto"], "cidade": ["capital"],
                             "cep": ["cidade", "estado", "pais"], "flv": ["fruta", "legume", "verdura"],
                             "nome": ["nome_masculino", "nome_feminino"]}.items():
        taxonomy[parent]["includes"] = children
    for cid, aliases in {"time_esportivo": ["Time", "Time de Futebol"], "pais": ["Países"],
                         "profissao": ["Profissões"], "palavra_em_ingles": ["Inglês"],
                         "comida": ["Alimento"]}.items():
        taxonomy[cid]["aliases"] = aliases
    document = import_legacy(original, taxonomy)
    document["sources"]["bootstrap-2026-10-29"] = {
        "kind": "local_editorial_review", "date": "2026-10-29", "license": "MIT",
        "scope": "Associações comuns revisadas localmente; sem garantia de aceitação por todos os jogadores"}
    for label, values in BOOTSTRAP.items():
        for value in values.split("|"):
            document = upsert(document, label, value, "approved", "bootstrap-2026-10-29",
                              "Associação semântica revisada para bootstrap pt-BR; categoria lexical quando aplicável")
    ibge = ROOT / 'data/source/ibge-municipios.json'
    if ibge.exists():
        snapshot = json.loads(ibge.read_text(encoding='utf-8'))
        document = import_ibge(document, snapshot)
        document = approve_ibge_geography(document, snapshot)
    data.parent.mkdir(parents=True, exist_ok=True)
    data.write_bytes(canonical(document) + b"\n")
    path = ROOT / "src/stopots_v2/resources/vocabulary.json"
    manifest = publish(document, path)
    path.with_suffix(".json.previous").unlink(missing_ok=True)
    print(json.dumps({"import": document["import_metrics"], "release": manifest}, ensure_ascii=False))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Compilar fonte editorial existente; recriar migração somente por opção explícita')
    parser.add_argument('--recriar', action='store_true', help='Recria editorial.json a partir das fontes; substitui curadoria local')
    build(parser.parse_args().recriar)
