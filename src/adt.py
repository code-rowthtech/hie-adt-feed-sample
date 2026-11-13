"""Generic ADT subset. Not an exchange-specific acceptance validator."""
from datetime import datetime
from uuid import uuid4
import re


def safe(value, field):
    if not isinstance(value,str) or not value.strip() or any(c in value for c in "|^~\\&\r\n"):
        raise ValueError(f"{field} must be nonempty and contain no HL7 delimiters")
    return value


def valid_date(value, fmt, size):
    if not isinstance(value,str) or len(value)!=size or not value.isdigit(): raise ValueError("Invalid date format")
    datetime.strptime(value,fmt)
    return value


def build(data: dict, event='A04') -> str:
    if event not in ['A01','A04']: raise ValueError('Only A01 and A04 supported')
    for key in ['facility_id','mrn','national_id','visit_id','family','given']:
        safe(data.get(key), key)
    valid_date(data.get('dob'),'%Y%m%d',8)
    if data.get('sex') not in ['M','F','O','U']: raise ValueError('Unsupported administrative sex')
    stamp=valid_date(data.get('timestamp','20260101120000'),'%Y%m%d%H%M%S',14)
    pv1=['PV1']+['']*44
    pv1[1]='1'; pv1[2]='I' if event=='A01' else 'O';pv1[19]=data['visit_id'];pv1[44]=stamp
    msg_id=str(uuid4())
    return '\r'.join([
        f"MSH|^~\\&|SYNTHETIC_EMR|{data['facility_id']}|HIE|SYNTHETIC_RECEIVER|{stamp}||ADT^{event}^ADT_A01|{msg_id}|T|2.5.1",
        f'EVN|{event}|{stamp}',
        f"PID|1||{data['mrn']}^^^{data['facility_id']}^MR~{data['national_id']}^^^SYNTHETIC^NI||{data['family']}^{data['given']}||{data['dob']}|{data['sex']}",
        '|'.join(pv1)])+'\r'


def validate(raw: str) -> list[str]:
    errors=[]
    rows=[line.split('|') for line in raw.replace('\r\n','\r').replace('\n','\r').split('\r') if line]
    def one(tag):
        matching=[r for r in rows if r[0]==tag]
        if len(matching)!=1: errors.append(f'Expected one {tag} segment')
        return matching[0] if matching else []
    msh,evn,pid,pv1=(one(t) for t in ['MSH','EVN','PID','PV1'])
    def f(row,n): return row[n] if len(row)>n else ''
    if not raw.startswith('MSH|^~\\&|'): errors.append('Unsupported delimiters')
    kind=f(msh,8).split('^')
    if len(kind)!=3 or kind[0]!='ADT' or kind[1] not in ['A01','A04'] or kind[2]!='ADT_A01':errors.append('Unsupported MSH-9')
    if not f(msh,9):errors.append('Missing MSH-10 control ID')
    if f(msh,10)!='T':errors.append('Synthetic sample requires MSH-11=T')
    if f(msh,11)!='2.5.1':errors.append('Unsupported HL7 version')
    if not f(msh,3):errors.append('Missing sending facility')
    if len(kind)>1 and f(evn,1)!=kind[1]:errors.append('EVN does not match message event')
    ids=f(pid,3).split('~')
    if len(ids)<2 or any(not part.split('^')[0] for part in ids):errors.append('Missing patient identifiers')
    try:valid_date(f(pid,7),'%Y%m%d',8)
    except ValueError:errors.append('Invalid birth date')
    if f(pid,8) not in ['M','F','O','U']:errors.append('Invalid sex code')
    if not f(pid,5):errors.append('Missing patient name')
    if f(pv1,2) not in ['I','O']:errors.append('Unsupported patient class')
    if len(kind)>1 and f(pv1,2)!=('I' if kind[1]=='A01' else 'O'):errors.append('Event and patient class mismatch')
    if not f(pv1,19):errors.append('Missing PV1-19 visit identifier')
    for stamp in [f(msh,6),f(evn,2),f(pv1,44)]:
        try:valid_date(stamp,'%Y%m%d%H%M%S',14)
        except ValueError:errors.append('Invalid event timestamp')
    return errors
