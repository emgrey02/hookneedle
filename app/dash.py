import datetime
import os
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort
from app.auth import login_required
from app.db import get_db
from app.helpers import sql_data_to_list_of_dicts

bp = Blueprint('dash', __name__)

@bp.route('/')
def index():
    db = get_db()
    projects = None
    requests = None
    friends = None
    todos = None

    if (g.user):
        try:
            projects = db.execute(
                'SELECT id, image_data, image_filename, name'
                ' FROM project'
                ' WHERE user_id = ?', (g.user['id'],)
            ).fetchall()

            friends = sql_data_to_list_of_dicts('SELECT * FROM friendship WHERE (user1_id = ? OR user2_id = ?) AND approved = ?', (g.user['id'], g.user['id'], True))

            requests = db.execute('SELECT * FROM friendship JOIN user ON user1_id = user.id WHERE approved = ? AND user2_id = ?', (False, g.user['id'])).fetchall()

            todos = db.execute('SELECT * FROM todo WHERE user_id = ?', (g.user['id'],)).fetchall()

        except db.IntegrityError as e:
            print("Error occured when getting projects: ", e)
        except db.OperationalError as e:
            print("Operational error occured while getting projects: ", e)
        except db.ProgrammingError as e:
            print("Programming error occured while getting projects: ", e)

    # get username + image data for your friends
    if friends:
        for friend in friends:
            if friend['user1_id'] == g.user['id']:
                friend['friendId'] = friend['user2_id']
                friend['friendUsername'] = db.execute('SELECT username FROM user WHERE id = ?', (friend['user2_id'],)).fetchone()['username']
                friend['image_data'] = db.execute('SELECT image_data FROM profile WHERE user_id = ?', (friend['user2_id'],)).fetchone()['image_data']
            else:
                friend['friendId'] = friend['user1_id']
                friend['friendUsername'] = db.execute('SELECT username FROM user WHERE id = ?', (friend['user1_id'],)).fetchone()['username']
                friend['image_data'] = db.execute('SELECT image_data FROM profile WHERE user_id = ?', (friend['user1_id'],)).fetchone()['image_data']
    
    return render_template('dash/index.html', projects=projects, friends=friends, notifs=requests, todos=todos)
    
@bp.route('/members', methods=['GET'])
@login_required
def members():
    db = get_db()

    try:
        members = db.execute('SELECT * FROM user JOIN profile ON user.id = profile.user_id WHERE user.id != ?', (g.user['id'],)).fetchall()
    except db.IntegrityError as e:
        print('Error occured when getting users: ', e)
    
    return render_template('dash/members.html', members=members)


@login_required
@bp.route('/dash/completeTodo/<int:id>', methods=['POST'])
def complete_todo(id):
    db = get_db()

    thisTodo = db.execute('SELECT * from todo WHERE id = ?', (id,)).fetchone()
    if thisTodo['completed']:
        try:
            db.execute('UPDATE todo SET completed = False WHERE id = ?', (id,))
            db.commit();
        except db.IntegrityError as e:
            print("Error toggling todo completion: ", e)
    else:
        try:
            db.execute('UPDATE todo SET completed = True WHERE id = ?', (id,))
            db.commit();
        except db.IntegrityError as e:
            print("Error toggling todo completion: ", e)
    
    return jsonify('toggled todo completion');



@login_required
@bp.route('/dash/addTodo', methods=['POST'])
def add_todo():
    todo = request.json

    created = datetime.datetime.today().strftime('%Y-%m-%d')

    db = get_db()

    if todo['id']:
        try:
            db.execute('UPDATE todo SET content = ? WHERE id = ?', (todo['input'], todo['id']))
            db.commit()
        except db.IntegrityError as e:
            print("Error updating todo: ", e)
    else:
        try:
            db.execute('INSERT INTO todo (user_id, content, created, completed) VALUES (?, ?, ?, ?)', (g.user['id'], todo['input'], created, False))
            db.commit()
        except db.IntegrityError as e:
                print("Error adding todo: ", e)


    return jsonify('todo item added')

@bp.route('/dash/deleteTodo/<int:id>', methods=['POST'])
def delete_todo(id):

    db = get_db()
    try:
        db.execute('DELETE FROM todo WHERE id = ?', (id,))
        db.commit()
    except db.IntegrityError as e:
            print("Error deleting todo: ", e)

    return jsonify('todo item successfully deleted')