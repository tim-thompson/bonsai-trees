import json
import os
import time
import unittest

from app import app, db, Tree


class TreeTests(unittest.TestCase):

    def setUp(self):
        app.config['DEBUG'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///unittest.db'
        app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
        self.app = app.test_client()
        db.drop_all()
        db.create_all()

    def tearDown(self):
        pass

    def test_create_tree(self):
        r1 = self.app.post('/trees', data=json.dumps({
            'species': 'A Random Species',
            'name': 'My tree has a name',
            'description': 'A random description.',
            'purchase_cost': 15.99,
            'purchase_date': '2018-01-01',
            'planted_date': '2018-01-01',
            'age': 8}), headers={'Accept': 'application/json', 'Content-Type': 'application/json', 'user_id': '1'})
        self.assertEqual(201, r1.status_code)

    def test_get_tree(self):
        tree1 = Tree(id='123', user_id='1')
        db.session.add(tree1)
        db.session.commit()

        r1 = self.app.get('/trees/123', headers={
            'Accept': 'application/json', 'Content-Type': 'application/json', 'user_id': '1'
        })
        self.assertEqual(200, r1.status_code)
        d1 = json.loads(r1.get_data(as_text=True))
        self.assertEqual('123', d1['id'])

    def test_get_tree_forbidden(self):
        tree1 = Tree(id='123', user_id='1')
        db.session.add(tree1)
        db.session.commit()

        r1 = self.app.get('/trees/123', headers={'user_id': '2'})
        self.assertEqual(403, r1.status_code)

    def test_get_tree_no_user(self):
        r1 = self.app.get('/trees/1', headers={
            'Accept': 'application/json', 'Content-Type': 'application/json'
        })
        self.assertEqual(400, r1.status_code)

    def test_get_tree_not_found(self):
        r1 = self.app.get('/trees/1', headers={
            'Accept': 'application/json', 'Content-Type': 'application/json', 'user_id': '1'
        })
        self.assertEqual(404, r1.status_code)
        data = json.loads(r1.get_data(as_text=True))
        self.assertEqual({'status': 404, 'message': 'Not found'}, data)

    def test_get_trees(self):
        tree1 = Tree(id='123', user_id='1')
        tree2 = Tree(id='234', user_id='1')
        tree3 = Tree(id='345', user_id='1')

        db.session.add(tree1)
        db.session.add(tree2)
        db.session.add(tree3)
        db.session.commit()

        r1 = self.app.get('/trees', headers={
            'Accept': 'application/json', 'Content-Type': 'application/json', 'user_id': '1'
        })
        self.assertEqual(200, r1.status_code)
        d1 = json.loads(r1.get_data(as_text=True))
        self.assertEqual(3, len(d1))
        self.assertEqual('123', d1[0]['id'])
        self.assertEqual('234', d1[1]['id'])
        self.assertEqual('345', d1[2]['id'])

    def test_get_trees_empty(self):
        r1 = self.app.get('/trees', headers={
            'Accept': 'application/json', 'Content-Type': 'application/json', 'user_id': '1'
        })
        self.assertEqual(404, r1.status_code)

    def test_delete_tree(self):
        tree1 = Tree(id='123')
        db.session.add(tree1)
        db.session.commit()

        r1 = self.app.delete('/trees/123', headers={
            'Accept': 'application/json', 'Content-Type': 'application/json', 'user_id': '1'
        })
        self.assertEqual(204, r1.status_code)

        tree = Tree.query.filter_by(id='123').first()
        self.assertIsNone(tree)

    def test_delete_tree_not_found(self):
        r1 = self.app.delete('/trees/123', headers={
            'Accept': 'application/json', 'Content-Type': 'application/json', 'user_id': '1'
        })
        self.assertEqual(404, r1.status_code)

    def test_patch_update_tree(self):
        tree1 = Tree(id='123', user_id='1')
        db.session.add(tree1)
        db.session.commit()

        r1 = self.app.patch('/trees/123', data={
            'species': 'A random species'
        }, headers={
            'Accept': 'application/json', 'Content-Type': 'application/json', 'user_id': '1'
        })
        d1 = json.loads(r1.get_data(as_text=True))
        self.assertEqual('A random species', d1['species'])