from flask import current_app, request, session, redirect


def _dev_mode():
    redirectTo = request.args.get('next', '/')
    session['username'] = 'testadmin'
    session['logged_in'] = True
    session['real_name'] = 'Test Admin'
    session['is_admin'] = 'True'
    session['role'] = 'editor'
    return redirect(redirectTo)


def _handle_swamid():
    session['username'] = request.headers['eppn']
    user = Users.query.filter(
        Users.username == session['username']
    ).first()
    if not user:
        session['logged_in'] = False
        return("Couldn't authenticate")
    session['logged_in'] = True
    session['real_name'] = request.headers['displayName']
    role = Role.query.filter(
        Role.id == user.role
    ).first()
    session['role'] = role.roleName
    if role.roleName == 'admin':
        print("Got admin")
        session['is_admin'] = 'True'
    return redirect(redirectTo)


def _prod_mode():
    if request.authorization:
        session['username'] = request.authorization['username']
        user = Users.query.filter(
            Users.username == session['username']
        ).first()
        if not user:
            session['logged_in'] = False
            return("Couldn't authenticate")
        role = Role.query.filter(
            Role.id == user.role
        ).first()
        session['role'] = role.roleName
        session['logged_in'] = True
        return redirect(redirectTo)
    elif request.headers['schacHomeOrganization'] == 'kb.se':
        return _handle_swamid()
    else:
        return('Can not authenticate')

def handle_logon():
    appMode = current_app.config['APPENV']
    print request.authorization
    redirectTo = request.args.get('next', '/')
    if appMode == 'dev':
        return _dev_mode()
    if appMode == 'production':
        return _prod_mode()

