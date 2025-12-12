import os
files = [
    'data/gordon_database.db',
    'data/gordon.db',
    'data/GRT_reference.db',
    'data/gordon.db',
]
for p in files:
    print('\n--', p)
    if not os.path.exists(p):
        print('MISSING')
        continue
    try:
        with open(p, 'rb') as f:
            hdr = f.read(256)
            print('len=', len(hdr))
            print(hdr[:64])
            # show ascii-ish
            try:
                print(hdr[:128].decode('utf-8', errors='replace'))
            except Exception as e:
                print('decode error', e)
    except Exception as e:
        print('error reading file', e)
