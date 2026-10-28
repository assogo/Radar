#!/usr/bin/env python3
import argparse
import base64
import json
import os
import re
import subprocess
import sys
import unicodedata
from collections import Counter
from datetime import date, datetime, timedelta

import requests
import yaml

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "radar.config.yaml")
DATA_PATH = os.path.join(BASE_DIR, "data", "items.json")


def load_config():
    if not os.path.exists(CONFIG_PATH):
        sys.exit("radar.config.yaml introuvable dans le dossier radar.")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_items():
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_items(items):
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def source_par_id(source_id, config):
    for source in config.get("sources", []):
        if source.get("id") == source_id:
            return source
    return {}


def nom_de_source(source_id, config):
    return source_par_id(source_id, config).get("nom", source_id)


def correspond_mots_cles(titre, mots):
    if not mots:
        return True
    t = titre.lower()
    return any(m.lower() in t for m in mots)


def est_ignore(titre, ignorer):
    t = titre.lower()
    return any(m.lower() in t for m in ignorer)


def normaliser(texte):
    texte = unicodedata.normalize("NFD", texte)
    texte = "".join(c for c in texte if not unicodedata.combining(c))
    return texte.lower()


def calcul_etiquettes(titre, config):
    tags = []
    t = titre.lower()
    for etiquettes in config.get("etiquettes", []):
        if isinstance(etiquettes, str):
            nom = etiquettes
            mots = [etiquettes]
        else:
            nom = etiquettes.get("nom")
            mots = etiquettes.get("mots", [nom])
        if nom and any(m.lower() in t for m in mots):
            tags.append(nom)
    return tags


def nouvel_item(titre, url, publie_le, source, config, auteur=None):
    return {
        "titre": titre,
        "url": url,
        "publie_le": publie_le,
        "collecte_le": date.today().isoformat(),
        "source": source.get("id"),
        "auteur": auteur,
        "type_veille": source.get("type_veille"),
        "etiquettes": calcul_etiquettes(titre, config),
        "fiabilite": None,
        "statut": None,
    }


def collect_releases(source, config):
    depot = source["depot"]
    per_page = source.get("per_page", config.get("per_page", 10))
    cmd = ["gh", "api", f"repos/{depot}/releases?per_page={per_page}"]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        print(f"Erreur gh api pour {depot} : {proc.stderr.strip()}", file=sys.stderr)
        return []
    try:
        releases = json.loads(proc.stdout)
    except json.JSONDecodeError:
        print(f"Reponse invalide de gh api pour {depot}.", file=sys.stderr)
        return []

    ignorer = config.get("ignorer", [])
    produit = source.get("produit", "")
    exclure_prereleases = source.get("exclure_prereleases", False)
    items = []
    for rel in releases:
        if exclure_prereleases and rel.get("prerelease"):
            continue
        url = rel.get("html_url")
        publie_le = (rel.get("published_at") or "")[:10]
        tag = rel.get("tag_name") or ""
        if not url or not publie_le or not tag:
            continue
        titre = f"{produit} {tag}".strip()
        if not titre or est_ignore(titre, ignorer):
            continue
        items.append(nouvel_item(titre, url, publie_le, source, config))
    return items


def collect_hackernews(source, config):
    requete = source.get("requete", "")
    try:
        resp = requests.get("https://hn.algolia.com/api/v1/search_by_date",
                            params={"query": requete, "tags": "story"}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"Erreur Hacker News ({requete}) : {e}", file=sys.stderr)
        return []

    mots = config.get("mots_cles", [])
    ignorer = config.get("ignorer", [])
    items = []
    for hit in data.get("hits", []):
        titre = hit.get("title") or hit.get("story_title") or ""
        url = hit.get("url") or hit.get("story_url")
        publie_le = (hit.get("created_at") or "")[:10]
        if not url or not publie_le or not titre:
            continue
        if not correspond_mots_cles(titre, mots):
            continue
        if est_ignore(titre, ignorer):
            continue
        items.append(nouvel_item(titre, url, publie_le, source, config, auteur=hit.get("author")))
    return items


def collect_failles(source, config):
    paquet = source.get("paquet")
    ecosysteme = source.get("ecosysteme")
    version = source.get("version")
    body = {"package": {"name": paquet, "ecosystem": ecosysteme}, "version": version}
    try:
        resp = requests.post("https://api.osv.dev/v1/query", json=body, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"Erreur OSV ({paquet}@{version}) : {e}", file=sys.stderr)
        return []

    items = []
    for vuln in data.get("vulns", []):
        titre = vuln.get("summary") or vuln.get("id") or ""
        publie_le = (vuln.get("published") or vuln.get("modified") or "")[:10]
        url = next((r.get("url") for r in vuln.get("references", []) if r.get("url")), None)
        if not url:
            url = f"https://osv.dev/vulnerability/{vuln.get('id')}"
        if not url or not publie_le or not titre:
            continue
        items.append(nouvel_item(titre, url, publie_le, source, config))
    return items


def extraire_titre(html):
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else None


def collect_page(source, config):
    url = source.get("url")
    date_publication = source.get("date_publication")
    if not url or not date_publication:
        print(f"Source page ({source.get('id')}) sans url ou date_publication : ignoree.", file=sys.stderr)
        return []
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"Erreur page ({url}) : {e}", file=sys.stderr)
        return []

    titre = extraire_titre(resp.text)
    if not url or not titre:
        return []
    publie_le = str(date_publication)[:10]
    if publie_le > date.today().isoformat():
        titre = f"{titre} (à venir)"
    return [nouvel_item(titre, url, publie_le, source, config)]


COLLECTEURS = {
    "releases": collect_releases,
    "hackernews": collect_hackernews,
    "failles": collect_failles,
    "page": collect_page,
}


def trouver_placeholders(config):
    problemes = []
    for source in config.get("sources", []):
        sid = source.get("id", source.get("type"))
        for champ, valeur in source.items():
            if isinstance(valeur, str) and re.search(r"<[^>]+>", valeur):
                problemes.append(f"source « {sid} », champ « {champ} » = {valeur}")
    for champ in ("axes", "mots_cles", "ignorer"):
        for valeur in config.get(champ, []):
            if isinstance(valeur, str) and re.search(r"<[^>]+>", valeur):
                problemes.append(f"champ « {champ} » = {valeur}")
    return problemes


def collect():
    config = load_config()
    problemes = trouver_placeholders(config)
    if problemes:
        for p in problemes:
            print(f"Valeur non renseignée (<...>) : {p}", file=sys.stderr)
        sys.exit("Collect arrêté : des valeurs <...> restent à remplir dans radar.config.yaml.")
    items = load_items()
    vues = {item.get("url") for item in items}
    nb_nouveaux = 0

    for source in config.get("sources", []):
        collecteur = COLLECTEURS.get(source.get("type"))
        if collecteur is None:
            print(f"Source de type inconnu : {source.get('type')} (ignoree).", file=sys.stderr)
            continue
        for item in collecteur(source, config):
            if item.get("url") in vues:
                continue
            items.append(item)
            vues.add(item.get("url"))
            nb_nouveaux += 1

    for item in items:
        item["type_veille"] = source_par_id(item.get("source"), config).get("type_veille")
        item["etiquettes"] = calcul_etiquettes(item.get("titre", ""), config)

    items.sort(key=lambda i: i.get("publie_le", ""), reverse=True)
    save_items(items)
    print(f"{nb_nouveaux} nouvelle(s) info(s) ; {len(items)} au total dans data/items.json.")


def age_en_mois(publie_le):
    jour = datetime.strptime(publie_le, "%Y-%m-%d").date()
    aujourdhui = date.today()
    return (aujourdhui.year - jour.year) * 12 + (aujourdhui.month - jour.month)


def regle_vraie(regle, item, config, items):
    type_regle = regle.get("type")
    if type_regle == "categorie":
        return source_par_id(item.get("source"), config).get("categorie") == regle.get("valeur")
    if type_regle == "recent":
        return age_en_mois(item["publie_le"]) < int(regle.get("mois", 6))
    if type_regle == "contient":
        texte = normaliser(item.get("titre", ""))
        return any(normaliser(mot) in texte for mot in regle.get("mots", []))
    if type_regle == "champ":
        return bool(item.get(regle.get("champ")))
    if type_regle == "type_veille":
        return item.get("type_veille") == regle.get("valeur")
    if type_regle == "corroboration":
        types_concernes = regle.get("sources_concernees")
        source_item = source_par_id(item.get("source"), config)
        if types_concernes and source_item.get("type") not in types_concernes:
            return False
        mes_mots = [m.lower() for m in config.get("mots_cles", []) if m.lower() in item.get("titre", "").lower()]
        if not mes_mots:
            return False
        for autre in items:
            if autre is item or autre.get("source") == item.get("source"):
                continue
            source_autre = source_par_id(autre.get("source"), config)
            if types_concernes and source_autre.get("type") not in types_concernes:
                continue
            if any(m in autre.get("titre", "").lower() for m in mes_mots):
                return True
        return False
    return False


def scorer_item(item, config, items):
    total = 0
    regles = []
    for regle in config.get("regles_score", []):
        if regle_vraie(regle, item, config, items):
            points = int(regle.get("points", 0))
            total += points
            if points != 0:
                regles.append({"nom": regle.get("nom"), "points": points})
    return total, regles


def commande_score():
    config = load_config()
    items = load_items()
    seuil = config.get("seuil")
    for item in items:
        fiabilite, _ = scorer_item(item, config, items)
        item["fiabilite"] = fiabilite
        if seuil is not None:
            item["statut"] = "retenue" if fiabilite >= seuil else "ecartee"
    save_items(items)

    tries = sorted(items, key=lambda i: (i.get("fiabilite", -9999), i.get("publie_le", "")), reverse=True)
    for rang, item in enumerate(tries[:10], 1):
        fiabilite, regles = scorer_item(item, config, items)
        nom = nom_de_source(item.get("source"), config)
        print(f"{rang}. {fiabilite:+d}  {item.get('titre')}  ({item.get('publie_le')}, {nom})")
        if regles:
            detail = ", ".join(f"{r['nom']} {r['points']:+d}" for r in regles)
            print(f"   -> {detail}")

    print("")
    print("Répartition des scores :")
    for score, n in sorted(Counter(i["fiabilite"] for i in items).items(), reverse=True):
        print(f"  {score:+d} : {n} info(s)")

    print("")
    print("Par source (retenues / écartées) :")
    par_source = {}
    for item in items:
        statut = item.get("statut")
        d = par_source.setdefault(item.get("source"), {"retenue": 0, "ecartee": 0})
        if statut in d:
            d[statut] += 1
    for sid, c in par_source.items():
        print(f"  {nom_de_source(sid, config)} : {c['retenue']} retenue(s), {c['ecartee']} écartée(s)")

    failles = [i for i in items if i.get("type_veille") == "securite" and i.get("statut") == "retenue"]
    if failles:
        print("")
        print(f"ALERTE : {len(failles)} faille(s) de sécurité retenue(s) :")
        for f in failles:
            print(f"  - {f['titre']} ({f['publie_le']}) {f['url']}")


def commande_search(mot):
    items = load_items()
    mot_n = normaliser(mot)
    resultats = []
    for item in items:
        titre = normaliser(item.get("titre") or "")
        etiquettes = [normaliser(e) for e in (item.get("etiquettes") or [])]
        if mot_n in titre or any(mot_n in e for e in etiquettes):
            resultats.append(item)
    for item in resultats:
        print(f"{item.get('titre')}  ({item.get('publie_le')})  {item.get('url')}")
    print(f"{len(resultats)} resultat(s).")


def gh_api(endpoint):
    proc = subprocess.run(["gh", "api", endpoint], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def chiffres_depot(depot):
    info = gh_api(f"repos/{depot}")
    if info is None:
        return None
    releases = gh_api(f"repos/{depot}/releases?per_page=100") or []
    contributeurs = gh_api(f"repos/{depot}/contributors?per_page=100") or []
    depuis = (date.today() - timedelta(days=90)).isoformat() + "T00:00:00Z"
    commits = gh_api(f"repos/{depot}/commits?since={depuis}&per_page=100") or []
    return {
        "depot": depot,
        "url": f"https://github.com/{depot}",
        "cree_le": (info.get("created_at") or "")[:10],
        "licence": (info.get("license") or {}).get("spdx_id") or "non précisée",
        "etoiles": info.get("stargazers_count"),
        "versions": len(releases),
        "derniere_version": releases[0].get("tag_name") if releases else None,
        "contributeurs": len(contributeurs),
        "commits_90j": len(commits),
    }


def fmt_cape(n, cap=100):
    return f"{n}+" if n >= cap else str(n)


def dependances_depot(depot):
    for fichier in ("package.json", "requirements.txt"):
        contenu = gh_api(f"repos/{depot}/contents/{fichier}")
        if not contenu:
            continue
        raw = contenu.get("content", "")
        try:
            texte = base64.b64decode("".join(raw.split())).decode("utf-8")
        except Exception:
            continue
        if fichier == "package.json":
            try:
                data = json.loads(texte)
            except json.JSONDecodeError:
                continue
            return {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        lignes = [l.strip() for l in texte.splitlines() if l.strip() and not l.strip().startswith("#")]
        return {l: "" for l in lignes}
    return None


def filtrer_infos_question(config, items):
    mots = [m.lower() for m in config.get("decision", {}).get("mots", [])]
    if not mots:
        return items
    resultats = []
    for item in items:
        titre = (item.get("titre") or "").lower()
        etiquettes = " ".join(e.lower() for e in (item.get("etiquettes") or []))
        texte = f"{titre} {etiquettes}"
        if any(m in texte for m in mots):
            resultats.append(item)
    return resultats


def matrice_decision(decision):
    options = decision.get("options", [])
    criteres = decision.get("criteres", [])
    notes_cfg = decision.get("notes", {})
    lignes = ["| Critère | Poids | " + " | ".join(opt.get("nom", "") for opt in options) + " |"]
    lignes.append("|" + "---|" * (2 + len(options)))
    totaux = {opt.get("id"): 0 for opt in options}
    for critere in criteres:
        cid = critere.get("id")
        nom = critere.get("nom", cid)
        poids = int(critere.get("poids", 1))
        cellules = []
        for opt in options:
            note_cfg = notes_cfg.get(opt.get("id"), {}).get(cid)
            if note_cfg:
                note = int(note_cfg.get("note", 0))
                url = note_cfg.get("url", "")
                d = note_cfg.get("date", "")
                chiffre = note_cfg.get("chiffre", "")
                totaux[opt.get("id")] += poids * note
                cellules.append(f"{note} ({chiffre}, [src]({url}), {d})")
            else:
                cellules.append("—")
        lignes.append(f"| {nom} | {poids} | " + " | ".join(cellules) + " |")
    return lignes, totaux


def commande_decide():
    config = load_config()
    items = load_items()
    decision = config.get("decision") or {}
    if not decision:
        sys.exit("Pas de rubrique « decision » dans radar.config.yaml.")

    question = decision.get("question", "")
    options = decision.get("options", [])
    infos_liees = filtrer_infos_question(config, items)

    lignes = [f"# Décision : {question}", ""]
    lignes.append("## Contexte")
    for opt in options:
        lignes.append(f"- {opt.get('nom')} (`{opt.get('depot')}`)")
    lignes.append("")

    lignes.append("## Infos liées à la question")
    if infos_liees:
        for item in infos_liees:
            lignes.append(f"- [{item.get('titre')}]({item.get('url')}) — {item.get('publie_le')}")
    else:
        lignes.append("(aucune info collectée ne touche cette question)")
    lignes.append("")

    lignes.append("## Chiffres bruts (gh api)")
    for opt in options:
        lignes.append(f"### {opt.get('nom')}")
        c = chiffres_depot(opt.get("depot"))
        if c is None:
            lignes.append(f"- Dépôt `{opt.get('depot')}` introuvable (à renseigner dans radar.config.yaml).")
        else:
            lignes.append(f"- Création : {c['cree_le']}")
            lignes.append(f"- Versions (releases) : {fmt_cape(c['versions'])}" + (f" (dernière : {c['derniere_version']})" if c['derniere_version'] else ""))
            lignes.append(f"- Contributeurs : {fmt_cape(c['contributeurs'])}")
            lignes.append(f"- Commits (90 jours) : {fmt_cape(c['commits_90j'])}")
            lignes.append(f"- Licence : {c['licence']}")
            lignes.append(f"- Source : {c['url']} (consultée le {date.today().isoformat()})")
            if opt.get("dependances"):
                deps = dependances_depot(opt.get("depot"))
                if deps:
                    lignes.append("- Dépendances : " + ", ".join(f"{k} {v}".strip() for k, v in deps.items()))
                else:
                    lignes.append("- Dépendances : aucune détectée (pas de package.json / requirements.txt).")
        lignes.append("")

    lignes.append("## Matrice (poids × note)")
    lignes.append("")
    lignes_mat, totaux = matrice_decision(decision)
    lignes.extend(lignes_mat)
    lignes.append("")

    lignes.append("## Total pondéré")
    for opt in options:
        lignes.append(f"- {opt.get('nom')} : **{totaux.get(opt.get('id'), 0)}**")
    lignes.append("")

    lignes.append("## Impact")
    lignes.append("")
    lignes.append("- **Périmètre** : ")
    lignes.append("- **Budget** : ")
    lignes.append("- **Délais** : ")

    with open(os.path.join(BASE_DIR, "decision.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lignes) + "\n")
    print("decision.md écrit.")


def commande_report():
    config = load_config()
    items = load_items()
    decision = config.get("decision") or {}
    rapport = config.get("rapport") or {}
    if not decision:
        sys.exit("Pas de rubrique « decision » dans radar.config.yaml.")

    question = decision.get("question", "")
    options = decision.get("options", [])

    retenues = sorted([i for i in items if i.get("statut") == "retenue"], key=lambda i: i.get("publie_le", ""), reverse=True)
    ecartees = sorted([i for i in items if i.get("statut") != "retenue"], key=lambda i: i.get("publie_le", ""), reverse=True)

    lignes = [f"# Rapport — {question}", ""]

    lignes.append("# Page 1 · Synthèse de veille")
    lignes.append("")
    lignes.append("## Sources (datées)")
    for item in retenues:
        lignes.append(f"- [{item.get('titre')}]({item.get('url')}) — {item.get('publie_le')}")
    for item in ecartees:
        lignes.append(f"- [{item.get('titre')}]({item.get('url')}) — {item.get('publie_le')} (écartée)")
    lignes.append("")

    tendances = rapport.get("tendances", [])
    for i in (1, 2, 3):
        t = tendances[i - 1] if len(tendances) >= i else {}
        lignes.append(f"## Tendance {i} — {t.get('titre', '...')}")
        lignes.append(f"- Impact attendu : {t.get('impact', '')}")
        lignes.append(f"- Ce qu'elle permet d'anticiper : {t.get('anticiper', '')}")
        lignes.append(f"- Compatibilité budget & technique : {t.get('compatibilite', '')}")
        lignes.append(f"- Statut : {t.get('statut', 'retenue / écartée')}")
        lignes.append("")

    lignes.append("# Page 2 · Note de recommandation")
    lignes.append("")
    lignes.append("## Question et contexte")
    for opt in options:
        lignes.append(f"- {opt.get('nom')} (`{opt.get('depot')}`)")
    lignes.append("")
    lignes.append("## Options et matrice")
    lignes.append("")
    lignes_mat, totaux = matrice_decision(decision)
    lignes.extend(lignes_mat)
    lignes.append("")
    lignes.append("## Total pondéré")
    for opt in options:
        lignes.append(f"- {opt.get('nom')} : **{totaux.get(opt.get('id'), 0)}**")
    lignes.append("")
    lignes.append("## Recommandation")
    lignes.append(rapport.get("recommandation", "..."))
    lignes.append("")

    impact = rapport.get("impact", {})
    lignes.append("## Impact")
    lignes.append(f"- **Périmètre** : {impact.get('perimetre', '')}")
    lignes.append(f"- **Budget** : {impact.get('budget', '')}")
    lignes.append(f"- **Délais** : {impact.get('delais', '')}")
    lignes.append("")

    lignes.append("## Risques et plan B")
    for risque in rapport.get("risques", []):
        lignes.append(f"- Risque : {risque}")
    lignes.append(f"- Plan B : {rapport.get('plan_b', '...')}")
    lignes.append("")

    lignes.append("## Prochaine étape")
    lignes.append(rapport.get("prochaine_etape", "... (avec date)"))

    with open(os.path.join(BASE_DIR, "rapport.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lignes) + "\n")
    print("rapport.md écrit.")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    parser = argparse.ArgumentParser(prog="radar")
    sub = parser.add_subparsers(dest="commande", required=True)
    sub.add_parser("collect", help="Lit radar.config.yaml et enregistre les infos dans data/items.json")
    sub.add_parser("score", help="Remplit fiabilite et statut selon regles_score et affiche le top 10")
    sub.add_parser("decide", help="Compare 2 options (rubrique decision) et écrit decision.md")
    sub.add_parser("report", help="Écrit rapport.md (structure 2 pages + sources + matrice)")
    p_search = sub.add_parser("search", help="Retrouve les infos contenant un mot (titre ou etiquettes)")
    p_search.add_argument("mot", help="mot a rechercher")

    args = parser.parse_args()
    if args.commande == "collect":
        collect()
    elif args.commande == "score":
        commande_score()
    elif args.commande == "decide":
        commande_decide()
    elif args.commande == "report":
        commande_report()
    elif args.commande == "search":
        commande_search(args.mot)


if __name__ == "__main__":
    main()
