#!/bin/bash
# Re-deploya o gravador (sobe o HTML pro bucket público + serve via edge function /gravador).
# Uso: bash tools/recording/deploy_gravador.sh
cd "$(dirname "$0")/../.."
python3 - <<PY
import json,urllib.request
html=open('tools/recording/maya_recorder.html').read()
req=urllib.request.Request('https://yyxmtjqpmkonxlinflxu.functions.supabase.co/deploy-static',
  data=json.dumps({'html':html,'path':'gravador.html'}).encode(),
  headers={'Content-Type':'application/json'}, method='POST')
print('upload:', urllib.request.urlopen(req,timeout=30).read().decode())
print('PÁGINA: https://yyxmtjqpmkonxlinflxu.functions.supabase.co/gravador')
PY
