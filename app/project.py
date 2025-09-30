from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
import base64
from app.auth import login_required
from app.db import get_db
import datetime;
from postgrest.exceptions import APIError

bp = Blueprint('project', __name__)

@bp.route('/project/<int:id>', methods=['GET'])
def project(id):
    db = get_db()
    plan = None

    project = db.table('project').select('*').eq("id", id).execute().data[0]

    plan = db.table('project_plan').select('*').eq("project_id", id).execute().data[0]
    
    return render_template('project/project.html', project=project, plan=plan)

@bp.route('/project/create', methods=['GET', 'POST'])
@login_required
def create():
    error = None
    image_data = None
    upload_data = None

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
        visibility = request.form.get('visibility')

        db = get_db()

        getName = db.table('project').select('name').eq("name", name).execute().data

        if not craft:
            error = 'You must select either crochet or knit!'

        if getName != []:
            error = 'Project name must be unique!'
        
        if not name:
            error = 'Project must have a name!'

        if startDate:
            startDate = datetime.datetime.strptime(startDate, '%Y-%m-%d').strftime('%m-%d-%Y')
        
        if endDate:
            endDate = datetime.datetime.strptime(endDate, '%Y-%m-%d').strftime('%m-%d-%Y');

        if image:
            image_data = f'data:{image.mimetype};base64,{base64.b64encode(image.read()).decode("utf-8")}'
        
        if upload:
            upload_data = f'data:{upload.mimetype};base64,{base64.b64encode(upload.read()).decode("utf-8")}'
            
        if error is None:
            try:
                db.table('project').insert({'user_id': g.user['id'], "name": name, "link": link, "upload_filename": upload.filename, "upload_data": upload_data, "image_filename": image.filename, "image_data": image_data, "which_craft": craft, "desc_small": desc, "hook_needle_size": size, "yarn_weight": weight, "status": status, "progress": progress, "start_date": startDate, "end_date": endDate, "visibility": visibility}).execute()
            except APIError as e:
                print("Error inserting project into db: ", e)

            return redirect(url_for('dash.index')) 
        else:
            flash(error)
            return redirect(url_for('project.create'))
        
    return render_template('project/create.html')


@bp.route('/project/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    db = get_db()
    error = None
    image_data = None
    upload_data = None

    if (request.method == 'GET'):
        project = db.table('project').select('*').eq("user_id", g.user['id']).eq("id", id).execute().data[0]

        if project == []:
            error = 'failed to get project info'

        if error:
            flash(error)
            return redirect(url_for('project.project'))
        
        return render_template('project/edit.html', project=project)
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
        visibility = request.form.get('visibility')

        if upload:
            upload_data = f'data:{upload.mimetype};base64,{base64.b64encode(upload.read()).decode("utf-8")}'

        if image:
            image_data = f'data:{image.mimetype};base64,{base64.b64encode(image.read()).decode("utf-8")}'
        
        if startDate:
            startDate = datetime.datetime.strptime(startDate, '%Y-%m-%d').strftime('%m-%d-%Y')
        
        if endDate:
            endDate = datetime.datetime.strptime(endDate, '%Y-%m-%d').strftime('%m-%d-%Y')

        try:
            db.table('project').insert({'user_id': g.user['id'], "name": name, "link": link, "upload_filename": upload.filename, "upload_data": upload_data, "image_filename": image.filename, "image_data": image_data, "which_craft": craft, "desc_small": desc, "hook_needle_size": size, "yarn_weight": weight, "status": status, "progress": progress, "start_date": startDate, "end_date": endDate, "visibility": visibility}).eq("id", id).execute()

        except APIError as e:
            print("Error updating project: ", e)

        return redirect(url_for('project.project', id=id))
    
@bp.route('/project/delete/<int:id>', methods=['DELETE'])
@login_required
def delete(id):
    db = get_db()

    try:
        db.table('project').delete().eq("id", id).execute()
    except APIError as e:
        print('Error deleting project: ', e)
        return jsonify('project failed to delete')
    
    return jsonify('project successfully deleted')

@bp.route('/note/<int:id>', methods=['GET'])
@login_required
def get_note(id):

    db = get_db()

    note = db.table('note').select("*").eq("user_id", g.user['id']). eq("project_id", id).execute().data[0]

    if note == []:
        return jsonify('Failed to get note')
    
    else:
        return note['the_note']

@bp.route('/note/<int:id>/create', methods=['POST'])
@login_required
def add_note(id):
    data = request.json

    db = get_db()

    try:
        db.table('note').upsert({"user_id": g.user['id'], "project_id": id, "the_note": data}).execute()

    except APIError as e:
        print("Error adding note to project:", e)
                        
    return redirect(url_for('project.project', id=id))

@bp.route('/plan/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_plan(id):

    db = get_db();
    if request.method == 'POST':
        daily = None
        weekly = None

        daily = request.form.get('daily')
        weekly = request.form.get('weekly')

        try:
            db.table('project_plan').upsert({"project_id": id, "daily_goal": daily, "weekly_goal": weekly}).execute()

        except APIError as ex:
            raise Exception("An unexpected database query exception: ", str(ex))
        
        return redirect(url_for('project.project', id=id))

    else:

        plan = db.table('project_plan').select('*').eq("project_id", id).execute().data[0]

        return render_template('project/plan.html', plan=plan)
