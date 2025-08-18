from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort
import base64
from app.auth import login_required
from app.db import get_db

bp = Blueprint('dash', __name__)

@bp.route('/')
@login_required
def index():
    db = get_db()
    projects = None
    # display user's projects
    try:
        projects = db.execute(
            'SELECT id, link, image_filename, image_data, name'
            ' FROM project'
            ' WHERE user_id = ?', (g.user['id'],)
        ).fetchall()
    except db.IntegrityError as e:
        print("Error occured when getting projects: ", e)
    except db.OperationalError as e:
        print("Operational error occured while getting projects: ", e)
    except db.ProgrammingError as e:
        print("Programming error occured while getting projects: ", e)

    if projects is None:
        return render_template('dash/index.html')
    else:
        return render_template('dash/index.html', projects=projects)
    
@bp.route('/members', methods=['GET'])
@login_required
def members():
    db = get_db()

    try:
        members = db.execute('SELECT * FROM user').fetchall()
    except db.IntegrityError as e:
        print('Error occured when getting users: ', e)
    
    return render_template('dash/members.html', members=members)

@bp.route('/project/create', methods=['GET', 'POST'])
@login_required
def create():
    error = None

    # get form values, most are optional
    if request.method == 'POST':
        name = request.form.get('name')
        link = request.form.get('link')
        image = request.files['image']
        craft = request.form.get('craft')
        desc = request.form.get('desc')
        size = request.form.get('hook-needle-size')
        weight = request.form.get('yarn-weight')
        status = request.form.get('status')
        progress = request.form.get('progress')
        startDate = request.form.get('start-date')
        completed = request.form.get('completed')


        # convert image to base64
        image_b64 = f'data:{image.mimetype};base64,{base64.b64encode(image.read()).decode("utf-8")}'

        db = get_db()
        try:
            getName = db.execute('SELECT name FROM project WHERE user_id = ? AND name = ?', (g.user['id'], name)).fetchone()
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
                    'INSERT INTO project (user_id, name, link, image_filename, image_data, image_mimetype, which_craft, desc_small, hook_needle_size, yarn_weight, status, progress, start_date, completed)'
                    'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (g.user['id'], name, link, image.filename, image_b64, image.mimetype, craft, desc, size, weight, status, progress, startDate, completed)
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
        'SELECT * FROM project WHERE id = ?', (id,)
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
        craft = request.form.get('craft')
        desc = request.form.get('desc')
        size = request.form.get('hook-needle-size')
        weight = request.form.get('yarn-weight')
        status = request.form.get('status')
        progress = request.form.get('progress')
        startDate = request.form.get('start-date')
        completed = request.form.get('completed')

        # convert image to base64
        print(image.filename)
        image_b64 = f'data:{image.mimetype};base64,{base64.b64encode(image.read()).decode("utf-8")}'

        try:
            db.execute(
                'UPDATE project SET user_id = ?, name = ?, link = ?, image_filename = ?, image_data = ?, image_mimetype = ?, which_craft = ?, desc_small = ?, hook_needle_size = ?, yarn_weight = ?, status = ?, progress = ?, start_date = ?, completed = ? WHERE id = ?',
                (g.user['id'], name, link, image.filename, image_b64, image.mimetype, craft, desc, size, weight, status, progress, startDate, completed, id)
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