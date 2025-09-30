from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort
import base64
from app.auth import login_required
from app.db import get_db
import datetime
from postgrest.exceptions import APIError

bp = Blueprint('user', __name__)

@login_required
@bp.route('/user/profile/<int:id>')
def profile(id):
    error = None
    db = get_db()

    # user = db.execute(
    #     'SELECT * FROM user WHERE id = ?', (id,)
    # ).fetchone()
    try:
        # get user for this profile
        user = db.table('user').select('*').eq("id", id).limit(1).execute().data[0]

        # get request between logged in user and this one, if it exists
        
        # request = db.execute('SELECT * FROM friendship WHERE approved = ? AND ((user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?))', (False, g.user['id'], id, id, g.user['id'])).fetchone()

        request = db.table('friendship').select('*').eq("approved", False).or_(f"and(user1_id.eq.{g.user['id']}, user2_id.eq.{id}), and(user1_id.eq.{id}, user2_id.eq.{g.user['id']})").limit(1).execute().data

        if request != []:
            request = request[0]
        


        # get frienship between logged in user and this one, if it exists
        
        # friendship = db.execute('SELECT * FROM friendship WHERE approved = ? AND ((user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?))', (True, g.user['id'], id, id, g.user['id'])).fetchone()

        friendship = db.table('friendship').select('*').eq("approved", True).or_(f"and(user1_id.eq.{g.user['id']}, user2_id.eq.{id}), and(user1_id.eq.{id}, user2_id.eq.{g.user['id']})").limit(1).execute().data

        if friendship != []:
            friendship = friendship[0]
        

        # get all friends of this user (who owns this profile)
        # userFriends = sql_data_to_list_of_dicts('SELECT * FROM friendship WHERE (user1_id = ? OR user2_id = ?) AND approved = ?', (id, id, True))

        userFriends = db.table('friendship').select('*').eq("approved", True).or_(f"user1_id.eq.{id}, user2_id.eq.{id}").execute().data

        # profile = db.execute('SELECT * FROM profile WHERE user_id = ?', (id,)).fetchone()

        profile = db.table('profile').select('*').eq("user_id", id).limit(1).execute().data[0]

        # projects = db.execute('SELECT name, id, image_data FROM project WHERE user_id = ?', (id,)).fetchall()

        projects = db.table('project').select('name, id, image_data').eq("user_id", id).execute().data
   
    except APIError as e:
        print(f"An API error occurred: {e}")
        error = f"An API error occurred: {e.details}"

    if user is None:
        abort(404, "user doesn't exist")

    if userFriends:
        for friend in userFriends:
            if friend['user1_id'] == id:
                friend['friendId'] = friend['user2_id']
                # friend['friendUsername'] = db.execute('SELECT username FROM user WHERE id = ?', (friend['user2_id'],)).fetchone()['username']
                friend['friendUsername'] = db.table('user').select('username').eq('id', friend['user2_id']).limit(1).execute().data[0]['username']

                # friend['image_data'] = db.execute('SELECT image_data FROM profile WHERE user_id = ?', (friend['user2_id'],)).fetchone()['image_data']
                friend['img'] = db.table('profile').select('image_data').eq('user_id', friend['user2_id']).limit(1).execute().data[0]['image_data']

            elif friend['user2_id'] == id:
                friend['friendId'] = friend['user1_id']
                # friend['friendUsername'] = db.execute('SELECT username FROM user WHERE id = ?', (friend['user1_id'],)).fetchone()['username']
                friend['friendUsername'] = db.table('user').select('username').eq('id', friend['user1_id']).limit(1).execute().data[0]['username']

                # friend['image_data'] = db.execute('SELECT image_data FROM profile WHERE user_id = ?', (friend['user1_id'],)).fetchone()['image_data']
                friend['img'] = db.table('profile').select('image_data').eq('user_id', friend['user1_id']).limit(1).execute().data[0]['image_data']

    if error:
        flash(error)
    
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
            # db.execute('UPDATE user SET username = ? WHERE id = ?', (username, id))
            db.table('user').update({"username": username}).eq("id", id).execute()
            # db.execute(
            #     'UPDATE profile SET image_filename = ?, image_data = ?, bio = ?, visibility = ? WHERE id = ?',
            #     (image.filename, image_b64, bio, visibility, id)
            # )
            # db.commit()
            db.table("profile").update({"image_filename": image.filename, "image_data": image_b64, "bio": bio, "visibility": visibility}).eq("user_id", id).execute()

        except APIError as e:
            print("Error updating profile: ", e)


        return redirect(url_for('user.profile', id=id))
    else:
        # user = db.execute(
        # 'SELECT * FROM user WHERE id = ?', (id,)
        # ).fetchone()
        try:
            user = db.table('user').select('*').eq("id", id).execute().data[0]

        # profile = db.execute('SELECT * FROM profile WHERE user_id = ?', (id,)).fetchone()

            profile = db.table('profile').select('*').eq("user_id", id).execute().data[0]
        except APIError as e:
            print("failed to get user info", e)

        return render_template('/user/edit.html', user=user, profile=profile)
    
@login_required
@bp.route('/user/addfriend/<int:id>', methods=['POST'])
def add_friend(id):

    db = get_db()

    created = datetime.datetime.today().strftime('%m-%d-%Y')

    # friendship = db.execute('SELECT * FROM friendship WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)', (g.user['id'], id, id, g.user['id'])).fetchone()

    try:
        friendship = db.table('friendship').select('*').or_(f"and(user1_id.eq.{g.user['id']}, user2_id.eq.{id}), and(user1_id.eq.{id}, user2_id.eq.{g.user['id']})").limit(1).execute().data
    except APIError as e:
        print("Failed to get friendship status", e)

    if friendship == []:
        # db.execute('INSERT INTO friendship (user1_id, user2_id, approved, created)'
        #         'VALUES (?, ?, ?, ?)',
        #         (g.user['id'], id, False, created))
        # db.commit()

        try:
            db.table('friendship').insert({"user1_id": g.user['id'], "user2_id": id, "approved": False, "created": created}).execute()
        except APIError as e:
            print("Failed to send friend request", e)
    else:
        # db.execute('UPDATE friendship SET approved = ? WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)', (True, g.user['id'], id, id, g.user['id']))
        # db.commit()
        try:
            db.table('friendship').update({"approved": True}).or_(f"and(user1_id.eq.{g.user['id']}, user2_id.eq.{id}), and(user1_id.eq.{id}, user2_id.eq.{g.user['id']})").execute()
        except APIError as e:
            print("Failed to accept friend request", e)
    
    return jsonify('friendship successfull')

@login_required
@bp.route('/user/removefriend/<int:id>', methods=['POST'])
def remove_friend(id):
    db = get_db()

    # db.execute('DELETE FROM friendship WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)', (id, g.user['id'], g.user['id'], id))
    # db.commit()
    try:
        db.table('friendship').delete().or_(f"and(user1_id.eq.{id}, user2_id.eq.{g.user['id']}), and(user1_id.eq.{g.user['id']}, user2_id.eq.{id})").execute()
    except APIError as e:
        print("Error while deleting friend: ", e)

    return jsonify('friendship request removed')

@login_required
@bp.route('/user/img', methods=['GET'])
def get_user_img():

    db = get_db()

    # profile = db.execute('SELECT * FROM profile WHERE user_id = ?', (g.user['id'],)).fetchone()

    profile = db.table('profile').select('*').eq('user_id', g.user['id']).limit(1).execute().data[0]

    return jsonify(profile['image_data'])