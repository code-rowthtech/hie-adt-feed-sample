import unittest,json
from pathlib import Path
from src.adt import build,validate
class ADTTests(unittest.TestCase):
    def setUp(self):self.data=json.loads(Path('sample-data/registration.json').read_text())
    def test_registration_fields_and_carriage_returns(self):
        raw=build(self.data);self.assertEqual(validate(raw),[]);self.assertIn('ADT^A04^ADT_A01',raw);self.assertNotIn('\n',raw)
        pv1=next(s for s in raw.split('\r') if s.startswith('PV1')).split('|');self.assertEqual(pv1[19],self.data['visit_id']);self.assertEqual(pv1[44],self.data['timestamp'])
    def test_admission(self):self.assertEqual(validate(build(self.data,'A01')),[])
    def test_delimiter_injection_rejected(self):
        self.data['mrn']='bad|PID'
        with self.assertRaises(ValueError):build(self.data)
    def test_invalid_calendar_date_rejected(self):
        self.data['dob']='20000230'
        with self.assertRaises(ValueError):build(self.data)
    def test_missing_identifier_rejected(self):
        self.data['national_id']=''
        with self.assertRaises(ValueError):build(self.data)
    def test_corrupted_event_detected(self):self.assertTrue(validate(build(self.data).replace('EVN|A04','EVN|A01')))
    def test_missing_visit_detected(self):self.assertTrue(validate(build(self.data).replace(self.data['visit_id'],'')))
    def test_production_processing_flag_rejected(self):self.assertTrue(validate(build(self.data).replace('|T|2.5.1','|P|2.5.1')))
