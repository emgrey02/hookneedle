from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
import base64
from app.auth import login_required
from app.db import get_db

bp = Blueprint('dash', __name__)

@bp.route('/')
def index():
    db = get_db()
    projects = db.execute(
        'SELECT p.id, link, image, name, which_craft, desc_small, notes, hook_needle_size, yarn_weight, status, progress, start_date, completed'
        ' FROM project p JOIN user u ON p.user_id = u.id'
    ).fetchall()
    return render_template('dash/index.html', projects=projects)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        name = request.form.get('name')
        link = request.form.get('link')
        image = request.files['image']
        craft = request.form['craft']
        desc = request.form.get('desc')
        size = request.form.get('hook-needle-size')
        weight = request.form.get('yarn-weight')
        status = request.form.get('status')
        progress = request.form.get('progress')
        startDate = request.form.get('start-date')
        completed = request.form.get('completed')

        image_b64 = base64.b64encode(image.read()).decode('utf-8')
        print(image_b64)

        db = get_db()
        db.execute(
            'INSERT INTO project (user_id, name, link, image, which_craft, desc_small, hook_needle_size, yarn_weight, status, progress, start_date, completed)'
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (g.user['id'], name, link, image_b64, craft, desc, size, weight, status, progress, startDate, completed)
        )
        db.commit()
        return redirect(url_for('dash.index'))
    return render_template('dash/create.html')

@bp.route('/project/<int:id>', methods=['GET'])
def getProject(id):
    db = get_db()
    project = db.execute(
        'SELECT * FROM project WHERE id = ?', (id,)
    ).fetchone()

    return render_template('dash/project.html', project=project)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    return redirect(url_for('dash.index'))