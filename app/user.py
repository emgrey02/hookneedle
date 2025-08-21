from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort
import base64
from app.auth import login_required
from app.db import get_db
import datetime
from app.helpers import sql_data_to_list_of_dicts

bp = Blueprint('user', __name__)

@login_required
@bp.route('/user/profile/<int:id>')
def profile(id):

    db = get_db()

    user = db.execute(
        'SELECT * FROM user WHERE id = ?', (id,)
    ).fetchone()

    # get request between logged in user and this one, if it exists
    request = db.execute('SELECT * FROM friendship WHERE approved = ? AND ((user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?))', (False, g.user['id'], id, id, g.user['id'])).fetchone()

    # get frienship between logged in user and this one, if it exists
    friendship = db.execute('SELECT * FROM friendship WHERE approved = ? AND ((user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?))', (True, g.user['id'], id, id, g.user['id'])).fetchone()

    # get all friends of this user (who owns this profile)
    userFriends = sql_data_to_list_of_dicts('SELECT * FROM friendship WHERE (user1_id = ? OR user2_id = ?) AND approved = ?', (id, id, True))

    profile = db.execute('SELECT * FROM profile WHERE user_id = ?', (id,)).fetchone()

    projects = db.execute('SELECT name, id, image_data FROM project WHERE user_id = ?', (id,)).fetchall()

    if user is None:
        flash('user error')

    if userFriends:
        for friend in userFriends:
            if friend['user1_id'] == id:
                friend['friendId'] = friend['user2_id']
                friend['friendUsername'] = db.execute('SELECT username FROM user WHERE id = ?', (friend['user2_id'],)).fetchone()['username']
            elif friend['user2_id'] == id:
                friend['friendId'] = friend['user1_id']
                friend['friendUsername'] = db.execute('SELECT username FROM user WHERE id = ?', (friend['user1_id'],)).fetchone()['username']
    
    return render_template('/user/profile.html', thisUser=user, profile=profile, projects=projects, userFriends=userFriends, friendship=friendship, request=request)

@login_required
@bp.route('/user/profile/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    db = get_db()

    if (request.method == 'POST'):

        username = request.form.get('username')
        image = request.files['image']
        bio = request.form.get('bio')
        visibility = request.form.get('privacy')


        if image:
            image_b64 = f'data:{image.mimetype};base64,{base64.b64encode(image.read()).decode("utf-8")}'
        else:
            image.filename = ''
            image_b64 = ''

    
        try:
            db.execute('UPDATE user SET username = ? WHERE id = ?', (username, id))
            db.execute(
                'UPDATE profile SET image_filename = ?, image_data = ?, bio = ?, visibility = ? WHERE id = ?',
                (image.filename, image_b64, bio, visibility, id)
            )
            db.commit()
        except db.IntegrityError as e:
            print("Error updating profile: ", e)


        return redirect(url_for('user.profile', id=id))
    else:
        user = db.execute(
        'SELECT * FROM user WHERE id = ?', (id,)
        ).fetchone()

        profile = db.execute('SELECT * FROM profile WHERE user_id = ?', (id,)).fetchone()
        return render_template('/user/edit.html', user=user, profile=profile)
    
@login_required
@bp.route('/user/addfriend/<int:id>', methods=['POST'])
def addFriend(id):

    db = get_db()

    created = datetime.datetime.today().strftime('%Y-%m-%d')
    friendship = None

    friendship = db.execute('SELECT * FROM friendship WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)', (g.user['id'], id, id, g.user['id'])).fetchone()

    if friendship is None:
        db.execute('INSERT INTO friendship (user1_id, user2_id, approved, created)'
                'VALUES (?, ?, ?, ?)',
                (g.user['id'], id, False, created))
        db.commit()
    else:
        db.execute('UPDATE friendship SET approved = ? WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)', (True, g.user['id'], id, id, g.user['id']))
        db.commit()
    
    
    return jsonify('friendship successfull')

@login_required
@bp.route('/user/removefriend/<int:id>', methods=['POST'])
def removeFriend(id):
    db = get_db()

    db.execute('DELETE FROM friendship WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)', (id, g.user['id'], g.user['id'], id))
    db.commit()

    return jsonify('friendship request removed')

@login_required
@bp.route('/user/addTodo', methods=['POST'])
def addTodo():
    todo = request.json

    db = get_db()

    if todo['id']:
        try:
            db.execute('UPDATE todo SET content = ? WHERE id = ?', (todo['input'], todo['id']))
            db.commit()
        except db.IntegrityError as e:
            print("Error updating todo: ", e)
    else:
        try:
            db.execute('INSERT INTO todo (user_id, content) VALUES (?, ?)', (g.user['id'], todo['input']))
            db.commit()
        except db.IntegrityError as e:
                print("Error adding todo: ", e)


    return jsonify('todo item added')

@bp.route('/user/deleteTodo/<int:id>', methods=['POST'])
def deleteTodo(id):

    db = get_db()
    try:
        db.execute('DELETE FROM todo WHERE user_id = ? AND id = ?', (g.user['id'], id))
        db.commit()
    except db.IntegrityError as e:
            print("Error deleting todo: ", e)

    return jsonify('todo item successfully deleted')
