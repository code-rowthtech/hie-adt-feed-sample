import argparse,json,sys
from pathlib import Path
from .adt import build,validate

def main():
    p=argparse.ArgumentParser();p.add_argument('--event',choices=['A01','A04'],default='A04');p.add_argument('--validate');args=p.parse_args()
    try:
        raw=Path(args.validate).read_text() if args.validate else build(json.loads(Path('sample-data/registration.json').read_text()),args.event)
        errors=validate(raw)
        if errors: print(json.dumps({'valid':False,'errors':errors}),file=sys.stderr);return 1
        if args.validate:print(json.dumps({'valid':True,'scope':'generic-subset-only'}))
        else: print(raw.replace('\r','\n'),end='')
        return 0
    except (ValueError,OSError) as error:print(str(error),file=sys.stderr);return 1
if __name__=='__main__':sys.exit(main())
