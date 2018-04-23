from flask import Flask, make_response, jsonify, abort, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

from uuid import uuid4 as uuid
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)


class Tree(db.Model):
    id = db.Column(db.String, primary_key=True)
    species = db.Column(db.String)
    name = db.Column(db.String)
    description = db.Column(db.String)
    purchase_cost = db.Column(db.Float)
    purchase_date = db.Column(db.Date)
    planted_date = db.Column(db.Date)
    age = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.String)


class TreeSchema(ma.ModelSchema):
    class Meta:
        model = Tree


tree_schema = TreeSchema()
trees_schema = TreeSchema(many=True)


def authorise():
    user_id = request.headers.get('user_id')
    if user_id is None:
        abort(400)
    return user_id


@app.route('/trees', methods=['GET'])
def get_trees():
    user_id = authorise()
    trees = Tree.query.filter_by(user_id=user_id).all()
    if len(trees) == 0:
        abort(404)
    return trees_schema.jsonify(trees), 200


@app.route('/trees/<string:tree_id>', methods=['GET'])
def get_tree(tree_id):
    user_id = authorise()
    tree = Tree.query.filter_by(id=tree_id).first()
    if tree is None:
        abort(404)
    if tree.user_id != user_id:
        abort(403)
    return tree_schema.jsonify(tree), 200


@app.route('/trees', methods=['POST'])
def create_tree():
    user_id = authorise()
    data = request.get_json()
    tree = Tree(
        id=str(uuid()),
        species=data['species'],
        name=data['name'],
        description=data['description'],
        purchase_cost=data['purchase_cost'],
        purchase_date=datetime.strptime(data['purchase_date'], "%Y-%m-%d"),
        planted_date=datetime.strptime(data['planted_date'], "%Y-%m-%d"),
        age=data['age'],
        timestamp=datetime.now(),
        user_id=user_id
    )
    db.session.add(tree)
    db.session.commit()
    return tree_schema.jsonify(tree), 201


@app.route('/trees/<string:tree_id>', methods=['PUT'])
def put_update_tree(tree_id):
    user_id = authorise()
    return tree_id


@app.route('/trees/<string:tree_id>', methods=['PATCH'])
def patch_update_tree(tree_id):
    user_id = authorise()
    return tree_id


@app.route('/trees/<string:tree_id>', methods=['DELETE'])
def delete_tree(tree_id):
    user_id = authorise()
    tree = Tree.query.filter_by(id=tree_id).first()
    if tree is None:
        abort(404)
    db.session.delete(tree)
    db.session.commit()
    return '', 204


@app.errorhandler(403)
def forbidden(error):
    return make_response(jsonify({'status': 403, 'message': 'Forbidden'}), 403)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'status': 404, 'message': 'Not found'}), 404)


@app.errorhandler(500)
def internal_server(error):
    return make_response(jsonify({'status': 500, 'message': 'Internal Server Error'}), 500)
