from flask import current_app, request, session, redirect
from lib import models


def _dev_mode():
    session['username'] = 'testadmin'
    session['logged_in'] = True
    session['real_name'] = 'Test Admin'
    session['is_admin'] = 'True'
    session['role'] = 'editor'
    return redirect(request.args.get('next', '/'))


def _handle_swamid():
    session['username'] = request.headers['eppn']
    user = models.Users.query.filter(
        models.Users.username == session['username']
    ).first()
    if not user:
        session['logged_in'] = False
        return("Couldn't authenticate")
    session['logged_in'] = True
    session['real_name'] = request.headers['displayName'].strip('\n')
    role = models.Role.query.filter(
        models.Role.id == user.role
    ).first()
    session['role'] = role.roleName
    if role.roleName == 'admin':
        session['is_admin'] = 'True'
    return redirect(request.args.get('next', '/'))


def _prod_mode():
    if request.authorization:
        session['username'] = request.authorization['username']
        user = models.Users.query.filter(
            models.Users.username == session['username']
        ).first()
        if not user:
            session['logged_in'] = False
            return("Couldn't authenticate")
        role = models.Role.query.filter(
            models.Role.id == user.role
        ).first()
        session['role'] = role.roleName
        session['logged_in'] = True
        return redirect(request.args.get('next', '/'))
    elif request.headers['schacHomeOrganization'] == 'kb.se':
        return _handle_swamid()
    else:
        return('Can not authenticate')


def handle_logon():
    appMode = current_app.config['APPENV']
    if appMode == 'dev':
        return _dev_mode()
    if appMode == 'production':
        return _prod_mode()
