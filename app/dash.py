import datetime
from flask import (
    Blueprint, flash, g, render_template, request, jsonify
)

from app.auth import login_required
from app.db import get_db

from postgrest.exceptions import APIError

bp = Blueprint('dash', __name__)

@bp.route('/')
def index():
    db = get_db()
    projects = None
    requests = None
    friends = None
    todos = None
    error = None

    if (g.user):
        try:
            # projects = db.execute(
            #     'SELECT id, image_data, image_filename, name'
            #     ' FROM project'
            #     ' WHERE user_id = ?', (g.user['id'],)
            # ).fetchall()
            projects = db.table('project').select('id, image_data, image_filename, name').eq('user_id', g.user['id']).execute().data

            # friends = sql_data_to_list_of_dicts('SELECT * FROM friendship WHERE (user1_id = ? OR user2_id = ?) AND approved = ?', (g.user['id'], g.user['id'], True))

            friends = db.table('friendship').select('*').eq('approved', True).or_(f"user1_id.eq.{g.user['id']}, user2_id.eq.{g.user['id']}").execute().data

            # requests = db.execute('SELECT * FROM friendship JOIN user ON user1_id = user.id WHERE approved = ? AND user2_id = ?', (False, g.user['id'])).fetchall()

            requests = db.from_('friendship').select('user1_id, user!user1_id(id, username)').eq("approved", False).eq("user2_id", g.user['id']).execute().data
            print(requests)

            # todos = db.execute('SELECT * FROM todo WHERE user_id = ?', (g.user['id'],)).fetchall()

            todos = db.table('todo').select('*').eq('user_id', g.user['id']).execute().data
        except APIError as e:
            print(f"An API error occurred: {e}")
            error = f"An API error occurred: {e.details}"
       
    if error:
        flash(error)
    
    # get username + image data for your friends
    if friends:
        for friend in friends:
            if friend['user1_id'] == g.user['id']:
                friend['friendId'] = friend['user2_id']
                # friend['friendUsername'] = db.execute('SELECT username FROM user WHERE id = ?', (friend['user2_id'],)).fetchone()['username']
                friend['friendUsername'] = db.table('user').select('username').eq('id', friend['user2_id']).limit(1).execute().data[0]['username']

                # friend['image_data'] = db.execute('SELECT image_data FROM profile WHERE user_id = ?', (friend['user2_id'],)).fetchone()['image_data']
                friend['image_data'] = db.table('profile').select('image_data').eq('user_id', friend['user2_id']).limit(1).execute().data[0]['image_data']

            else:
                friend['friendId'] = friend['user1_id']
                # friend['friendUsername'] = db.execute('SELECT username FROM user WHERE id = ?', (friend['user1_id'],)).fetchone()['username']
                friend['friendUsername'] = db.table('user').select('username').eq('id', friend['user1_id']).limit(1).execute().data[0]['username']

                # friend['image_data'] = db.execute('SELECT image_data FROM profile WHERE user_id = ?', (friend['user1_id'],)).fetchone()['image_data']
                friend['image_data'] = db.table('profile').select('image_data').eq('user_id', friend['user1_id']).limit(1).execute().data[0]['image_data']

            
    
    return render_template('dash/index.html', projects=projects, friends=friends, notifs=requests, todos=todos)
    
@bp.route('/members', methods=['GET'])
@login_required
def members():
    db = get_db()

    try:
        # members = db.execute('SELECT * FROM user JOIN profile ON user.id = profile.user_id WHERE user.id != ?', (g.user['id'],)).fetchall()
        members = db.from_('user').select('id, username, profile(image_filename, image_data)').execute().data
    except APIError as e:
        print('Error occured when getting users: ', e)
    
    
    return render_template('dash/members.html', members=members)


@login_required
@bp.route('/dash/completeTodo/<int:id>', methods=['POST'])
def complete_todo(id):
    db = get_db()

    # thisTodo = db.execute('SELECT * from todo WHERE id = ?', (id,)).fetchone()
    thisTodo = db.table('todo').select('*').eq("id", id).limit(1).execute().data[0]
    if thisTodo['completed']:
        try:
            # db.execute('UPDATE todo SET completed = False WHERE id = ?', (id,))
            # db.commit()
            db.table('todo').update({"completed": False}).eq("id", id).execute()
        except APIError as e:
            print("Error toggling todo completion: ", e)
    else:
        try:
            # db.execute('UPDATE todo SET completed = True WHERE id = ?', (id,))
            # db.commit()
            db.table('todo').update({"completed": True}).eq("id", id).execute()
        except APIError as e:
            print("Error toggling todo completion: ", e)
    
    return jsonify('toggled todo completion')



@login_required
@bp.route('/dash/addTodo', methods=['POST'])
def add_todo():
    todo = request.json

    created = datetime.datetime.today().strftime('%m-%d-%Y')

    db = get_db()

    if todo['id']:
        try:
            # db.execute('UPDATE todo SET content = ? WHERE id = ?', (todo['input'], todo['id']))
            # db.commit()
            db.table('todo').update({"content": todo['input']}).eq("id", todo['id']).execute()
        except APIError as e:
            print("Error updating todo: ", e)
    else:
        try:
            # db.execute('INSERT INTO todo (user_id, content, created, completed) VALUES (?, ?, ?, ?)', (g.user['id'], todo['input'], created, False))
            # db.commit()
            db.table('todo').insert({"user_id": g.user['id'], "content": todo['input'], "created": created, "completed": False }).execute()
        except APIError as e:
                print("Error adding todo: ", e)


    return jsonify('todo item added')

@bp.route('/dash/deleteTodo/<int:id>', methods=['POST'])
def delete_todo(id):

    db = get_db()
    try:
        # db.execute('DELETE FROM todo WHERE id = ?', (id,))
        # db.commit()
        db.table("todo").delete().eq("id", id).execute()
    except APIError as e:
            print("Error deleting todo: ", e)

    return jsonify('todo item successfully deleted')