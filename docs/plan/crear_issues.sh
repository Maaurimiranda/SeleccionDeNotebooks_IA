#!/usr/bin/env bash
# Crea en GitHub un issue por cada docs/plan/issues/PG3-NN.md.
# Uso: bash docs/plan/crear_issues.sh            (crea todo)
#      bash docs/plan/crear_issues.sh --dry-run  (solo muestra qué haría)
# Requiere `gh` autenticado. Crea las etiquetas que falten. No asigna personas:
# el responsable queda escrito en el cuerpo (los usuarios de GitHub se completan a mano).
set -euo pipefail
cd "$(dirname "$0")/issues"
seco=${1:-}

for f in PG3-*.md; do
  titulo=$(sed -n 's/^title: "\(.*\)"$/\1/p' "$f")
  etiquetas=$(sed -n 's/^labels: \[\(.*\)\]$/\1/p' "$f" | tr -d ' ')
  cuerpo=$(mktemp)
  # Saca el front matter y lo pasa a una línea de metadatos legible.
  { sed -n 's/^asignado: /**Responsable:** /p; s/^estimacion: /**Estimación:** /p; s/^bloque: /**Cuándo:** /p' "$f"; echo; \
    awk 'BEGIN{n=0} /^---$/{n++; next} n>=2' "$f"; } > "$cuerpo"
  if [ "$seco" = "--dry-run" ]; then
    echo "$titulo  [$etiquetas]"
  else
    for e in ${etiquetas//,/ }; do gh label create "$e" --force >/dev/null; done
    gh issue create --title "$titulo" --label "$etiquetas" --body-file "$cuerpo"
  fi
  rm -f "$cuerpo"
done
