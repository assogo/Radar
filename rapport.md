# Rapport — connexion

# Page 1 · Synthèse de veille

## Sources (datées)
- [Claude Code v2.1.312](https://github.com/anthropics/claude-code/releases/tag/v2.1.312) — 2026-10-27
- [Codex rust-v0.165.0](https://github.com/openai/codex/releases/tag/rust-v0.165.0) — 2026-10-27
- [Claude Code v2.1.311](https://github.com/anthropics/claude-code/releases/tag/v2.1.311) — 2026-10-26
- [Claude Code v2.1.310](https://github.com/anthropics/claude-code/releases/tag/v2.1.310) — 2026-10-23
- [Codex rust-v0.164.0](https://github.com/openai/codex/releases/tag/rust-v0.164.0) — 2026-10-23
- [Claude Code v2.1.309](https://github.com/anthropics/claude-code/releases/tag/v2.1.309) — 2026-10-22
- [Claude Code v2.1.308](https://github.com/anthropics/claude-code/releases/tag/v2.1.308) — 2026-10-22
- [Claude Code v2.1.307](https://github.com/anthropics/claude-code/releases/tag/v2.1.307) — 2026-10-21
- [Claude Code v2.1.306](https://github.com/anthropics/claude-code/releases/tag/v2.1.306) — 2026-10-21
- [Claude Code v2.1.305](https://github.com/anthropics/claude-code/releases/tag/v2.1.305) — 2026-10-20
- [Claude Code v2.1.304](https://github.com/anthropics/claude-code/releases/tag/v2.1.304) — 2026-10-19
- [Claude Code v2.1.303](https://github.com/anthropics/claude-code/releases/tag/v2.1.303) — 2026-10-18
- [Codex rust-v0.163.0](https://github.com/openai/codex/releases/tag/rust-v0.163.0) — 2026-10-15
- [Europe Terms of Use | OpenAI](https://openai.com/policies/terms-of-use) — 2026-01-16
- [express vulnerable to XSS via response.redirect()](https://github.com/expressjs/express/security/advisories/GHSA-qw6h-vgh9-j6wx) — 2024-09-10
- [Express.js Open Redirect in malformed URLs](https://github.com/expressjs/express/security/advisories/GHSA-rv95-896h-c2vc) — 2024-03-25
- [Claude Chalk, a mod that lets Claude Code colour its own replies](https://github.com/adamkdean/claude-chalk) — 2026-10-28 (écartée)
- [I Used Claude Code to Speed Up My Shell Startup by 95%](https://www.nickyt.co/blog/how-i-used-claude-code-to-speed-up-my-shell-startup-by-95percent) — 2026-10-28 (écartée)
- [Claude Code's default telemetry sends Anthropic SHA-256 hashes of files it reads](https://agenticbench.org/ant-1-claude-code-telemetry.html) — 2026-10-28 (écartée)
- [DeltaDB now has a Claude Code plugin](https://delta.dev/blog/claude-code-multiplayer) — 2026-10-28 (écartée)
- [I built a tool with Claude Code that makes the correction stick](https://github.com/globalmpc/nomore) — 2026-10-28 (écartée)
- [Show HN: Nekot, an iPhone app that warns you before Claude Code limits hit](https://jeman.net/nekot/) — 2026-10-28 (écartée)
- [Show HN: CleanCode – Claude Code and Codex collaborating on one canvas](https://github.com/chen-985211/cleancode) — 2026-10-27 (écartée)
- [Show HN: Aigent-OS, a Claude Code harness that clears and resumes](https://github.com/wrg32786/aigent-os) — 2026-10-27 (écartée)
- [AI review optimized for recall (catches more defects than Codex or Claude)](https://github.com/quickchatai/quickreview) — 2026-10-27 (écartée)
- [Claude Code's Source Got Leaked. Here's What's Worth Learning](https://thoughts.jock.pl/p/claude-code-source-leak-what-to-learn-ai-agents-2026) — 2026-10-27 (écartée)
- [Show HN: SkillTotal – scan packages before Claude Code installs them](https://github.com/pezhik/skilltotal) — 2026-10-27 (écartée)

## Tendance 1 — Cadence de livraison rapide des CLI d'IA (Claude Code / Codex)
- Impact attendu : Hivemind pilote Claude Code et Codex en ligne de commande ; des sorties quasi quotidiennes imposent de suivre et tester chaque version.
- Ce qu'elle permet d'anticiper : planifier la compatibilité de Hivemind avec les nouvelles versions et éviter des régressions.
- Compatibilité budget & technique : compatible — mises à jour automatiques, 0 €, aucun composant en plus.
- Statut : retenue — sources officielles (score 4). 10 versions de Claude Code (v2.1.303 → v2.1.312) et 3 versions stables de Codex (rust-v0.165.0, v0.164.0, v0.163.0).

## Tendance 2 — Montée de l'interopérabilité entre agents (MCP/ACP)
- Impact attendu : piloter plusieurs IA via un protocole standard devient une tendance, ce qui appuie l'option ACP de notre question.
- Ce qu'elle permet d'anticiper : la convergence des outils vers un protocole d'agent, et donc l'intérêt de s'y brancher tôt.
- Compatibilité budget & technique : compatible — protocoles open source, pas de coût supplémentaire.
- Statut : écartée — source communautaire « Show HN » (autopromo, score 2 < seuil 4). Ex. « Show HN: CleanCode – Claude Code and Codex collaborating on one canvas » (2026-10-27).

## Tendance 3 — Data : encadrement réglementaire, sécurité et télémétrie
- Impact attendu : pour un outil local, l'usage des données est encadré (CGU) et exposé à des failles (dépendances) et à la télémétrie des agents.
- Ce qu'elle permet d'anticiper : contrôler ce qui quitte la machine (télémétrie) et mettre à jour les dépendances.
- Compatibilité budget & technique : compatible (reste local), mais demande vigilance et mises à jour de sécurité.
- Statut : retenue — CGU officielle « Europe Terms of Use | OpenAI » (2026-01-16) et 2 failles express (securite, score 4) ; la télémétrie (2026-10-28) est écartée (communautaire).

# Page 2 · Note de recommandation

## Question et contexte
- Ne rien changer (Hivemind, pilotage CLI) (`assogo/hivemind`)
- Agent Client Protocol (ACP) (`agentclientprotocol/agent-client-protocol`)

## Options et matrice

| Critère | Poids | Ne rien changer (Hivemind, pilotage CLI) | Agent Client Protocol (ACP) |
|---|---|---|---|
| Maturité | 2 | 1 (0 release, créé 2026-10-26, [src](https://github.com/assogo/hivemind), 2026-10-28) | 4 (95 releases, créé 2025-06-23, [src](https://github.com/agentclientprotocol/agent-client-protocol), 2026-10-28) |
| Dynamisme | 1 | 1 (1 contributeur, 11 commits/90j, [src](https://github.com/assogo/hivemind), 2026-10-28) | 5 (100+ contributeurs, 100+ commits/90j, [src](https://github.com/agentclientprotocol/agent-client-protocol), 2026-10-28) |
| Licence | 3 | 1 (aucun fichier LICENSE, [src](https://github.com/assogo/hivemind), 2026-10-28) | 5 (Apache-2.0, [src](https://github.com/agentclientprotocol/agent-client-protocol), 2026-10-28) |
| Maintenance | 2 | 2 (1 développeur, [src](https://github.com/assogo/hivemind), 2026-10-28) | 4 (communauté active, [src](https://github.com/agentclientprotocol/agent-client-protocol), 2026-10-28) |
| Coût total | 3 | 5 (déjà en place, 0 €, [src](https://github.com/assogo/hivemind), 2026-10-28) | 4 (open source, gratuit, [src](https://github.com/agentclientprotocol/agent-client-protocol), 2026-10-28) |
| Apprentissage | 3 | 5 (déjà maîtrisé, [src](https://github.com/assogo/hivemind), 2026-10-28) | 2 (protocole à apprendre, [src](https://github.com/agentclientprotocol/agent-client-protocol), 2026-10-28) |
| Réversibilité | 2 | 5 (rien à défaire, [src](https://github.com/assogo/hivemind), 2026-10-28) | 3 (standard, réversible, [src](https://github.com/agentclientprotocol/agent-client-protocol), 2026-10-28) |

## Total pondéré
- Ne rien changer (Hivemind, pilotage CLI) : **50**
- Agent Client Protocol (ACP) : **60**

## Recommandation
Adopter l'Agent Client Protocol (ACP) pour connecter Hivemind aux IA, au lieu de maintenir un pilotage CLI en dur — décision fondée sur la matrice gh api (ACP 60 vs Hivemind 50), la tendance HN sur l'interopérabilité restant écartée.

## Impact
- **Périmètre** : remplacer la couche d'appel CLI de Hivemind par un client ACP.
- **Budget** : 0 € (ACP open source Apache-2.0) ; coût en temps de développement uniquement.
- **Délais** : 2 sprints, compatible avec la prochaine livraison.

## Risques et plan B
- Risque : ACP est récent et sa courbe d'apprentissage est réelle pour un seul développeur (matrice : apprentissage 2/5).
- Risque : Le protocole peut encore évoluer (dynamisme fort : 100+ commits/90 j).
- Plan B : Garder le pilotage CLI actuel et réévaluer après le premier sprint.

## Prochaine étape
Coder un client ACP minimal dans Hivemind et le tester sur un agent d'ici le 2026-11-06.
