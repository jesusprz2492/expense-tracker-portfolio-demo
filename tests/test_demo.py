import unittest
from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app, MONTHS, context

class DemoTests(unittest.TestCase):
    def setUp(self):
        self.client=TestClient(app)

    def test_all_pages_all_months(self):
        for month in MONTHS:
            for page in ['dashboard','movements','reports','budgets','accounts','contacts','categories','payment-methods']:
                with self.subTest(month=month['id'],page=page):
                    response=self.client.get('/'+page,params={'month_id':month['id']})
                    self.assertEqual(response.status_code,200)
                    self.assertIn('All data is fictional',response.text)
                    self.assertEqual(response.headers['X-Robots-Tag'],'noindex, nofollow')

    def test_both_languages_and_user_text(self):
        for page in ['dashboard','movements','reports','budgets','accounts','contacts','categories','payment-methods']:
            en=self.client.get('/'+page).text
            es=self.client.get('/'+page+'?lang=es').text
            self.assertTrue('<html lang="en">' in en)
            self.assertTrue('<html lang="es">' in es)
            self.assertTrue('All data is fictional' in en)
            self.assertTrue('Todos los datos son ficticios' in es)
            self.assertTrue('data-demo-language="es"' in en)
        self.assertTrue('$ 3,979.00' in self.client.get('/dashboard').text)
        self.assertTrue('$ 3.979,00' in self.client.get('/dashboard?lang=es').text)
        self.assertTrue('Sample rent' in self.client.get('/movements').text)
        self.assertTrue('Alquiler de ejemplo' in self.client.get('/movements?lang=es').text)
        data={'month_id':'2026-10','transaction_date':'2026-10-16','description':'Vivienda','note':'Ocio','amount':'25','kind':'expense'}
        for lang in ['en','es']:
            result=self.client.post('/demo/render',json={'page':'movements','lang':lang,'operations':[{'action':'create','data':data}]})
            self.assertEqual(result.status_code,200)
            self.assertTrue('<strong>Vivienda</strong>' in result.text)
            self.assertTrue('>Ocio</small>' in result.text)

    def test_totals_reconcile(self):
        for month in MONTHS:
            data=context(month)
            k=data['dashboard']['kpis']
            self.assertEqual(k['income']-k['spent'],k['balance'])
            self.assertEqual(sum(c['spent'] for c in data['dashboard']['categories']),k['spent'])
            self.assertEqual(data['reports']['kpis']['net'],k['balance'])
            self.assertEqual(sum(a['net'] for a in data['reports']['by_account']),k['balance'])
            self.assertEqual(sum(p['amount'] for p in data['reports']['by_payment_method']),k['spent'])

    def test_no_writes_or_auth_endpoints(self):
        for method in ['POST','PUT','PATCH','DELETE']:
            for path in ['/movements','/budgets','/accounts','/security','/unknown']:
                self.assertEqual(self.client.request(method,path,json={'amount':1}).status_code,405)
        for path in ['/security','/unlock','/docs','/.env','/database.py']:
            self.assertEqual(self.client.get(path).status_code,404)
        self.assertEqual(self.client.get('/health').json()['database'],False)

    def test_filters_and_assets(self):
        october=self.client.get('/dashboard?month_id=2026-10').text
        may=self.client.get('/dashboard?month_id=2026-05').text
        self.assertNotEqual(october,may)
        self.assertIn('October 2026',self.client.get('/dashboard?month_id=invalid').text)
        for asset in ['css/app.css','css/demo.css','js/app.js','img/cleryvo-logo.png']:
            self.assertEqual(self.client.get('/static/'+asset).status_code,200)
        self.assertIn('<input disabled',self.client.get('/accounts').text)

    def test_sandbox_edits_are_isolated(self):
        data={'month_id':'2026-10','transaction_date':'2026-10-16','description':'Demo test item','amount':'25.50',
              'kind':'expense','category_id':'2','account_id':'1','payment_method_id':'2','counterparty_id':''}
        op={'action':'create','data':data}
        result=self.client.post('/demo/render',json={'page':'movements','month_id':'2026-10','operations':[op]})
        self.assertEqual(result.status_code,200,result.text)
        self.assertIn('Demo test item',result.text)
        self.assertNotIn('Demo test item',self.client.get('/movements').text)
        edit={'action':'edit','id':'demo-0','data':{**data,'description':'Updated demo item','amount':'12.30'}}
        result=self.client.post('/demo/render',json={'page':'movements','operations':[op,edit]})
        self.assertIn('Updated demo item',result.text)
        delete={'action':'delete','id':'demo-0','data':{'month_id':'2026-10'}}
        result=self.client.post('/demo/render',json={'page':'movements','operations':[op,edit,delete]})
        self.assertNotIn('Updated demo item',result.text)
        budget={'action':'budget','data':{'month_id':'2026-10','category_id':'2','amount':'555'}}
        result=self.client.post('/demo/render',json={'page':'budgets','operations':[budget]})
        self.assertIn('555.00',result.text)
        self.assertNotIn('555.00',self.client.get('/budgets').text)

    def test_invalid_sandbox_changes_fail_without_persistence(self):
        for amount in ['NaN','Infinity','-1','1000001']:
            result=self.client.post('/demo/render',json={'page':'budgets','operations':[{'action':'budget',
                 'data':{'month_id':'2026-10','category_id':'2','amount':amount}}]})
            self.assertEqual(result.status_code,422)
        self.assertEqual(self.client.post('/demo/render',json={'page':'dashboard','operations':[{'action':'create','data':{}}]*201}).status_code,422)

if __name__=='__main__':
    unittest.main()
