# CLAUDE.md — Directives projet cyd_lumiere

## ⛔ NE PAS utiliser les worktrees

Ne jamais passer `isolation: "worktree"` dans les appels Agent tool.
Travailler directement sur la branche courante (main) — jamais dans un worktree isolé.

## 📁 Chemins importants

- **Fichier principal** : `cyd_lumiere/index.html`
- **Racine git** : `C:/Users/ryb086/OneDrive - Groupe R.Y. Beaudoin/Bureau/CLAUDE_CODE`
- **Remote** : `https://github.com/robingag/cabane-marcoux.git`

## 🔧 Commandes git

Toujours exécuter git depuis la racine git (pas depuis cyd_lumiere/) :
```bash
cd "/c/Users/ryb086/OneDrive - Groupe R.Y. Beaudoin/Bureau/CLAUDE_CODE"
git add cyd_lumiere/index.html
git commit -m "message"
git push
```

## 💾 Backup automatique

Un hook PreToolUse crée un commit de backup avant chaque Edit/Write.
Pour récupérer une version précédente : `git log --oneline` puis `git checkout <hash> -- cyd_lumiere/index.html`
