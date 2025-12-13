import json

for fn in ['locales/de.json', 'locales/en.json']:
    with open(fn, 'r', encoding='utf-8') as f:
        d = json.load(f)
    
    d['help']['text'] = d['help']['text'].replace('v0.9.3', 'v0.9.4').replace('Version 0.9.3', 'Version 0.9.4')
    d['gui']['credits'] = d['gui']['credits'].replace('v0.9.3', 'v0.9.4')
    
    with open(fn, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    
    print(f'✅ Updated {fn}')

print('\n✅ All locale files updated to v0.9.4')
