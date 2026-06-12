SEED_URL="https://www.getonbrd.com/empleos-ingeniero-de-sistemas"
TIEMPO=30
REPETICIONES=3
WORKERS=(1 2 4 6)
OUT="experimento_resultados.csv"

echo "workers,corrida,total_procesadas,ofertas_validas,habilidades_unicas" > $OUT

for w in "${WORKERS[@]}"; do
    for r in $(seq 1 $REPETICIONES); do
        echo ""
        echo "▶ Workers=$w | Corrida=$r/3 ..."

        rm -f output/resultados.csv output/apertura.csv output/grafo.json

        SEED_URL="$SEED_URL" TIEMPO=$TIEMPO WORKERS=$w docker compose up --no-build 2>/dev/null

        TOTAL=$(python3 -c "
import json
try:
    g = json.load(open('output/grafo.json'))
    print(g['meta']['total_ofertas'])
except: print(0)
")
        VALIDAS=$(python3 -c "
import json
try:
    g = json.load(open('output/grafo.json'))
    print(g['meta']['ofertas_validas'])
except: print(0)
")
        HABILIDADES=$(python3 -c "
import json
try:
    g = json.load(open('output/grafo.json'))
    print(g['meta']['total_nodos'])
except: print(0)
")

        echo "   ✓ total_procesadas=$TOTAL | ofertas_validas=$VALIDAS | habilidades=$HABILIDADES"
        echo "$w,$r,$TOTAL,$VALIDAS,$HABILIDADES" >> $OUT

        sleep 2
    done
done

echo ""
echo "============================================"
echo "✅ Experimento completo. Resultados en: $OUT"
echo "============================================"