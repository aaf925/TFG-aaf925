import json

for f in ['mejoras/whisper_finetune/dataset/train.json', 'mejoras/whisper_finetune/dataset/val.json',
          'mejoras/whisper_finetune/dataset/metadata.json']:
    data = json.load(open(f, encoding='utf-8'))
    for item in data:
        if 'audio' in item:
            item['audio'] = item['audio'].replace('\\', '/')
    json.dump(data, open(f, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    print(f'Fixed {f}: {len(data)} entries')
