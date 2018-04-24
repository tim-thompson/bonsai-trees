from datetime import datetime

from flask import Flask, jsonify, abort, request
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from marshmallow import ValidationError, fields

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)


class Tree(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
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
    id = fields.Int(dump_only=True)
    name = fields.String(required=True)
    user_id = fields.String(dump_only=True)
    timestamp = fields.DateTime(dump_only=True)

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
    return trees_schema.dumps(trees), 200


@app.route('/trees/<string:tree_id>', methods=['GET'])
def get_tree(tree_id):
    user_id = authorise()
    tree = Tree.query.filter_by(id=tree_id).first()
    if tree is None:
        abort(404)
    if tree.user_id != user_id:
        abort(403)
    return tree_schema.dumps(tree), 200


@app.route('/trees', methods=['POST'])
def create_tree():
    user_id = authorise()
    tree = None
    try:
        tree = tree_schema.load(request.get_json())
    except ValidationError as err:
        abort(422)
    tree.timestamp = datetime.now()
    tree.user_id = user_id
    db.session.add(tree)
    db.session.commit()
    return tree_schema.dumps(tree), 201


@app.route('/trees/<string:tree_id>', methods=['PATCH'])
def patch_update_tree(tree_id):
    user_id = authorise()
    tree = Tree.query.filter_by(id=tree_id).first()
    if tree is None:
        abort(404)
    if tree.user_id != user_id:
        abort(403)
    for key in request.get_json():
        # Check the attribute exists otherwise return 422
        try:
            getattr(tree, key)
        except AttributeError as error:
            abort(422)
        setattr(tree, key, request.get_json()[key])
    db.session.commit()
    return tree_schema.dumps(tree), 200


@app.route('/trees/<string:tree_id>', methods=['DELETE'])
def delete_tree(tree_id):
    user_id = authorise()
    tree = Tree.query.filter_by(id=tree_id).first()
    if tree is None:
        abort(404)
    if tree.user_id != user_id:
        abort(403)
    db.session.delete(tree)
    db.session.commit()
    return '', 204


@app.errorhandler(403)
def forbidden(error):
    return jsonify({'status': 403, 'message': 'Forbidden'}), 403


@app.errorhandler(404)
def not_found(error):
    return jsonify({'status': 404, 'message': 'Not found'}), 404


@app.errorhandler(422)
def unprocessable_entity(error):
    return jsonify({'status': 422, 'message': 'Unprocessable Entity'}), 422


@app.errorhandler(500)
def internal_server(error):
    return jsonify({'status': 500, 'message': 'Internal Server Error'}), 500
