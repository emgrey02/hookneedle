from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort
import base64
from app.auth import login_required
from app.db import get_db
import datetime

bp = Blueprint('user', __name__)

@login_required
@bp.route('/user/profile/<int:id>')
def profile(id):

    db = get_db()

    user = db.execute(
        'SELECT * FROM user WHERE id = ?', (id,)
    ).fetchone()

    requests = db.execute('SELECT * FROM friendship JOIN user as u ON user2_id = u.id WHERE user1_id IN (SELECT user2_id FROM friendship) AND user2_id NOT IN (SELECT user1_id FROM friendship) OR user2_id IN (SELECT user2_id FROM friendship) AND user1_id IN (SELECT user1_id FROM friendship)').fetchall()

    userFriends = db.execute('SELECT * FROM friendship JOIN user as u ON user2_id = u.id WHERE user1_id IN (SELECT user2_id FROM friendship) AND user2_id IN (SELECT user1_id FROM friendship) AND user1_id = ?', (g.user['id'],)).fetchall()

    projects = db.execute('SELECT * FROM project WHERE user_id = ?', (id,)).fetchall()

    # determine whether we are friends with this user or if either one has sent a request
    addFriendBtn = False
    friends = False
    # if we are looking at someone else's profile
    #2 1
    if g.user['id'] != id:
        print(id)
        # for each of our friends
        if len(userFriends) == 0:
            print(f'user {g.user['id']} has no friends')
            addFriendBtn = True
        else:
            print(f'user {g.user['id']} has friends')
            for friend in userFriends:
                # if we're not friends
                if friend['user2_id'] == id:
                    print(f'user {g.user['id']} is friends with user {id}')
                    friends = True
    
    acceptFriendRequest = False
    friendshipRequested = False
    
    if not friends:
        for request in requests:
            if request['user1_id'] == id and request['user2_id'] == g.user['id']:
                print(f'user {id} has sent a request to user {g.user['id']}')
                acceptFriendRequest = True
            if request['user1_id'] == g.user['id'] and request['user2_id'] == id:
                print(f'user {g.user['id']} has sent a request to user {id}')
                friendshipRequested = True
        if not addFriendBtn:
            addFriendBtn = True

    profile = db.execute('SELECT * FROM profile WHERE user_id = ?', (id,)).fetchone()

    projects = db.execute('SELECT name, id FROM project WHERE user_id = ?', (id,)).fetchall()

    if profile is None:
        profile = []

    if user is None:
        flash('user error')

    return render_template('/user/profile.html', user=user, profile=profile, projects=projects, userFriends=userFriends, addFriendBtn=addFriendBtn, acceptFriendRequest=acceptFriendRequest, friendshipRequested=friendshipRequested, friends=friends)

@login_required
@bp.route('/user/profile/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    db = get_db()

    if (request.method == 'POST'):

        username = request.form.get('username')
        image = request.files['image']
        bio = request.form.get('bio')

        image_b64 = f'data:{image.mimetype};base64,{base64.b64encode(image.read()).decode("utf-8")}'

        profile = db.execute('SELECT * FROM profile WHERE user_id = ?', (id,)).fetchone()

        if profile is None:
            try:
                db.execute(
                    'INSERT INTO profile (user_id, image_filename, image_data, image_mimetype, bio)'
                    'VALUES (?, ?, ?, ?, ?)',
                    (id, image.filename, image_b64, image.mimetype, bio)
                )
                db.commit()
            except db.IntegrityError as e:
                print('Error creating profile: ', e)
        else:
            try:
                db.execute('UPDATE user SET username = ? WHERE id = ?', (username, id))
                db.execute(
                    'UPDATE profile SET image_filename = ?, image_data = ?, image_mimetype = ?, bio = ? WHERE id = ?',
                    (image.filename, image_b64, image.mimetype, bio, id)
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
    
    db.execute('INSERT INTO friendship (user1_id, user2_id, created)'
            'VALUES (?, ?, ?)',
            (g.user['id'], id, created))
    db.commit()
    
    
    return redirect(url_for('user.profile', id=id))

@login_required
@bp.route('/user/<int:id>/friends', methods=['GET'])
def friends(id):
    db = get_db()

    friends = db.execute('SELECT * FROM friendship JOIN user as u ON user2_id = u.id WHERE user1_id IN (SELECT user2_id FROM friendship) AND user2_id IN (SELECT user1_id FROM friendship) AND user1_id = ?', (id,)).fetchall()

    return render_template('/user/friends.html', friends=friends)