import os
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort
import base64
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

    if (g.user):
        try:
            projects = db.execute(
                'SELECT id, image_blob, image_filename, name'
                ' FROM project'
                ' WHERE user_id = ?', (g.user['id'],)
            ).fetchall()

            friends = sql_data_to_list_of_dicts('SELECT * FROM friendship WHERE (user1_id = ? OR user2_id = ?) AND approved = ?', (g.user['id'], g.user['id'], True))

            requests = db.execute('SELECT * FROM friendship JOIN user ON user1_id = user.id WHERE approved = ? AND user2_id = ?', (False, g.user['id'])).fetchall()

        except db.IntegrityError as e:
            print("Error occured when getting projects: ", e)
        except db.OperationalError as e:
            print("Operational error occured while getting projects: ", e)
        except db.ProgrammingError as e:
            print("Programming error occured while getting projects: ", e)

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
    
    if projects is None:
        return render_template('dash/index.html')
    else:
        return render_template('dash/index.html', projects=projects, friends=friends, notifs=requests)
    
@bp.route('/members', methods=['GET'])
@login_required
def members():
    db = get_db()

    try:
        members = db.execute('SELECT * FROM user JOIN profile ON user.id = profile.user_id WHERE user.id != ?', (g.user['id'],)).fetchall()
    except db.IntegrityError as e:
        print('Error occured when getting users: ', e)
    
    return render_template('dash/members.html', members=members)

@bp.route('/project/create', methods=['GET', 'POST'])
@login_required
def create():
    error = None
    image_blob = None
    upload_blob = None

    # get form values, most are optional
    if request.method == 'POST':
        name = request.form.get('name')
        link = request.form.get('link')
        image = request.files['image']
        upload = request.files['upload']
        craft = request.form.get('craft')
        desc = request.form.get('desc')
        size = request.form.get('hook-needle-size')
        weight = request.form.get('yarn-weight')
        status = request.form.get('status')
        progress = request.form.get('progress')
        startDate = request.form.get('start-date')
        endDate = request.form.get('end-date')

        
        if image:
            image_blob = f'data:{image.mimetype};base64,{base64.b64encode(image.read()).decode("utf-8")}'
        
        if upload:
            upload_blob = f'data:{upload.mimetype};base64,{base64.b64encode(upload.read()).decode("utf-8")}'
        

        db = get_db()
        try:
            getName = db.execute('SELECT name FROM project WHERE name = ?', (name,)).fetchone()
        except db.IntegrityError as e:
            print("Error getting username: ", e)

        if not craft:
            error = 'You must select either crochet or knit!'

        if getName:
            error = 'Project name must be unique!'
        
        if not name:
            error = 'Project must have a name!'
            
        if error is None:
            try:
                db.execute(
                    'INSERT INTO project (user_id, name, link, upload_filename, upload_blob, image_filename, image_blob, which_craft, desc_small, hook_needle_size, yarn_weight, status, progress, start_date, end_date)'
                    'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (g.user['id'], name, link, upload.filename, upload_blob, image.filename, image_blob, craft, desc, size, weight, status, progress, startDate, endDate)
                )
            except db.IntegrityError as e:
                print("Error inserting project into db: ", e)

            db.commit()
            return redirect(url_for('dash.index')) 
        else:
            flash(error)
            return redirect(url_for('dash.create'))
        
    return render_template('dash/create.html')

@bp.route('/project/<int:id>', methods=['GET'])
def project(id):
    db = get_db()

    project = db.execute(
        'SELECT * FROM project JOIN user ON user_id == user.id WHERE project.id = ?', (id,)
    ).fetchone()

    return render_template('dash/project.html', project=project)

@bp.route('/note/<int:id>', methods=['GET'])
@login_required
def getNote(id):

    db = get_db()

    note = db.execute(
        'SELECT * FROM note WHERE user_id = ? AND project_id = ?', (g.user['id'], id)
    ).fetchone()

    if note is None:
        return jsonify('no note available')
    
    else:
        return note['the_note']

@bp.route('/note/<int:id>/create', methods=['POST'])
@login_required
def addNote(id):
    data = request.data

    db = get_db()

    db.execute(
        'INSERT OR REPLACE INTO note (user_id, project_id, the_note)'
        'VALUES (?, ?, ?)',
        (g.user['id'], id, data)
    )

    db.commit()
    return redirect(url_for('dash.project', id=id))

@bp.route('/project/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    db = get_db()
    error = None

    if (request.method == 'GET'):
        project = db.execute('SELECT * FROM project WHERE user_id = ? AND id = ?', (g.user['id'], id)).fetchone()

        if project is None:
            error = 'failed to get project info'

        if error:
            flash(error)
            return redirect(url_for('dash.project'))
        
        return render_template('dash/edit.html', project=project)
    else:
        name = request.form.get('name')
        link = request.form.get('link')
        image = request.files['image']
        upload = request.files['upload']
        craft = request.form.get('craft')
        desc = request.form.get('desc')
        size = request.form.get('hook-needle-size')
        weight = request.form.get('yarn-weight')
        status = request.form.get('status')
        progress = request.form.get('progress')
        startDate = request.form.get('start-date')
        endDate = request.form.get('end-date')

        upload_blob = f'data:{upload.mimetype};base64,{base64.b64encode(upload.read()).decode("utf-8")}'
        image_blob = f'data:{image.mimetype};base64,{base64.b64encode(image.read()).decode("utf-8")}'
        
        try:
            db.execute(
                'UPDATE project SET user_id = ?, name = ?, link = ?, upload_filename = ?, upload_blob = ?, image_filename = ?, image_blob = ?, which_craft = ?, desc_small = ?, hook_needle_size = ?, yarn_weight = ?, status = ?, progress = ?, start_date = ?, end_date = ? WHERE id = ?',
                (g.user['id'], name, link, upload.filename, upload_blob, image.filename, image_blob, craft, desc, size, weight, status, progress, startDate, endDate, id)
            )
            db.commit()
        except db.IntegrityError as e:
            print("Error updating project: ", e)

        return redirect(url_for('dash.project', id=id))
    
@bp.route('/project/delete/<int:id>', methods=['DELETE'])
@login_required
def delete(id):
    db = get_db()

    try:
        db.execute('DELETE FROM project WHERE id = ?', (id,))
        db.commit()
    except db.IntegrityError as e:
        print('Error deleting project: ', e)
        return jsonify('project failed to delete')
    
    return jsonify('project successfully deleted')