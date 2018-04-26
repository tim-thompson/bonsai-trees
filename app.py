import os
from datetime import datetime

from flask import Flask, jsonify, abort, request
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from marshmallow import ValidationError, fields

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('FLASK_DB')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', False)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

db = SQLAlchemy(app)
ma = Marshmallow(app)
migrate = Migrate(app, db)
content_type = {'Content-Type': 'application/json'}


class Tree(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    species = db.Column(db.String(100))
    name = db.Column(db.String(100))
    description = db.Column(db.String(1000))
    purchase_cost = db.Column(db.Float)
    purchase_date = db.Column(db.Date)
    planted_date = db.Column(db.Date)
    age = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.String(100))


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
    app.logger.info('Check User ID is in header: %s', user_id)
    if user_id is None:
        abort(400)
    return user_id


@app.route('/trees', methods=['GET'])
def get_trees():
    app.logger.info('get_trees start')
    user_id = authorise()
    trees = Tree.query.filter_by(user_id=user_id).all()
    return trees_schema.dumps(trees), 200, content_type


@app.route('/trees/<string:tree_id>', methods=['GET'])
def get_tree(tree_id):
    app.logger.info('get_tree with %s start', tree_id)
    user_id = authorise()
    tree = Tree.query.filter_by(id=tree_id).first()
    if tree is None:
        abort(404)
    if tree.user_id != user_id:
        abort(403)
    return tree_schema.dumps(tree), 200, content_type


@app.route('/trees', methods=['POST'])
def create_tree():
    app.logger.info('create_tree start')
    user_id = authorise()
    tree = None
    try:
        tree = tree_schema.load(request.get_json())
    except ValidationError as error:
        app.logger.info('invalid input: %s', error)
        abort(422)
    tree.timestamp = datetime.now()
    tree.user_id = user_id
    db.session.add(tree)
    db.session.commit()
    return tree_schema.dumps(tree), 201, content_type


@app.route('/trees/<string:tree_id>', methods=['PATCH'])
def patch_update_tree(tree_id):
    app.logger.info('patch_update_tree with %s start', tree_id)
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
    return tree_schema.dumps(tree), 200, content_type


@app.route('/trees/<string:tree_id>', methods=['DELETE'])
def delete_tree(tree_id):
    app.logger.info('delete_tree with %s start', tree_id)
    user_id = authorise()
    tree = Tree.query.filter_by(id=tree_id).first()
    if tree is None:
        abort(404)
    if tree.user_id != user_id:
        abort(403)
    db.session.delete(tree)
    db.session.commit()
    return '', 204, content_type


@app.errorhandler(400)
def bad_request(error):
    app.logger.error(error)
    return jsonify({'status': 400, 'message': 'Bad Request - No User ID'}), 400


@app.errorhandler(403)
def forbidden(error):
    app.logger.error(error)
    return jsonify({'status': 403, 'message': 'Forbidden'}), 403


@app.errorhandler(404)
def not_found(error):
    app.logger.error(error)
    return jsonify({'status': 404, 'message': 'Not Found'}), 404


@app.errorhandler(422)
def unprocessable_entity(error):
    app.logger.error(error)
    return jsonify({'status': 422, 'message': 'Unprocessable Entity'}), 422


@app.errorhandler(500)
def internal_server(error):
    app.logger.error(error)
    return jsonify({'status': 500, 'message': 'Internal Server Error'}), 500
