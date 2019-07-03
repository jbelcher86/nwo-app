#!/usr/bin/env python2.7

from flask import Flask
from flask import render_template
from flask import url_for
from flask import request
from flask import redirect
from flask import jsonify
from flask import make_response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, User, Faction, Wrestler
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests
import random
import string
from flask import session as login_session


app = Flask(__name__)
APPLICATION_NAME = 'nWo Wrestlers'
CLIENT_ID = json.loads(open('client_secrets.json',
                       'r').read())['web']['client_id']
engine = create_engine('sqlite:///nwo.db',
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# User Helper Functions
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except BaseException:
        return None


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def createUser(login_session):
    newUser = User(
        name=login_session['username'],
        email=login_session['email'],
        picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    request.get_data()
    code = request.data.decode('utf-8')

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    # Submit request, parse response
    h = httplib2.Http()
    response = h.request(url, 'GET')[1]
    str_response = response.decode('utf-8')
    result = json.loads(str_response)

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data.get('name', '')
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: '
    output += '300px;border-radius: 150px;-webkit-border-radius: '
    output += '150px;-moz-border-radius: 150px;"> '
    return output


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase +
                                  string.digits) for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state, CLIENT_ID=CLIENT_ID)


# Resets login session and logs user out
@app.route('/logout')
def logout():
    if login_session['provider'] == 'google':
        gdisconnect()
        del login_session['access_token']
        del login_session['gplus_id']

    del login_session['username']
    del login_session['email']
    del login_session['picture']
    del login_session['user_id']
    del login_session['provider']

    return redirect(url_for('showFaction'))


# Log user out of google sign in
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    del login_session['access_token']
    del login_session['gplus_id']
    del login_session['username']
    del login_session['email']
    del login_session['picture']
    response = make_response(json.dumps('Successfully disconnected.'), 200)
    response.headers['Content-Type'] = 'application/json'
    return response


# App Route function for the homepage
@app.route('/')
@app.route('/factions')
def showFactions():
    print(login_session)
    factions = session.query(Faction).all()
    return render_template('factions.html',
                           factions=factions, login_session=login_session)


# App rout funtion for showing faction info
@app.route('/factions/<int:faction_id>/')
def showFactionDetail(faction_id):
    faction = session.query(Faction).filter_by(id=faction_id).one()
    wrestlers = session.query(Wrestler).filter_by(
        faction_id=faction_id).all()
    return render_template('wrestler.html', wrestlers=wrestlers,
                           faction=faction,
                           login_session=login_session)


# Create new factions
@app.route('/factions/new/', methods=['GET', 'POST'])
def newFaction():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newFaction = Faction(name=request.form['name'],
                             user_id=login_session['user_id'])
        session.add(newFaction)
        session.commit()
        return redirect(url_for('showFactions'))
    else:
        return render_template('newFaction.html', login_session=login_session)


# Edit factions
@app.route('/factions/<int:faction_id>/edit/', methods=['GET', 'POST'])
def editFaction(faction_id):
    editedFactions = session.query(
        Faction).filter_by(id=faction_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if editedFactions.user_id != login_session['user_id']:
        return "<script>function myFunction()\
             {alert('You Shouldn't Be Here');}</script>\
                 <body onload='myFunction()'>"
    if request.method == 'POST':
        if request.form['name']:
            editedFactions.name = request.form['name']
            return redirect(url_for('showFactions'))
    else:
        return render_template(
            'editFaction.html', factions=editedFactions,
            login_session=login_session)


# Delete factions

@app.route('/factions/<int:faction_id>/delete/', methods=['GET', 'POST'])
def deleteFaction(faction_id):
    factionToDelete = session.query(
        Faction).filter_by(id=faction_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if factionToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction()\
             {alert('You Shouldn't Be Here');}</script>\
                 <body onload='myFunction()'>"
    if request.method == 'POST':
        session.delete(factionToDelete)
        session.commit()
        return redirect(
            url_for('showFactions', faction_id=faction_id))
    else:
        return render_template(
            'deleteFaction.html', faction=factionToDelete,
            login_session=login_session)


# Add wrestler
@app.route(
    '/factions/<int:faction_id>/wrestler/new/', methods=['GET', 'POST'])
def newWrestler(faction_id):
    factions = session.query(Faction).filter_by(id=faction_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        new_wrestler = Wrestler(name=request.form['name'],
                                description=request.form[
                            'description'], finisher=request.form['finisher'],
                            faction_id=faction_id,
                            user_id=login_session['user_id'])
        session.add(new_wrestler)
        session.commit()
        return redirect(url_for('showFactionDetail', faction_id=faction_id))
    else:
        return render_template('newWrestler.html', faction_id=faction_id,
                               login_session=login_session)


# Edit Wrestler
@app.route('/factions/<int:faction_id>/wrestler/<int:wrestler_id>/edit',
           methods=['GET', 'POST'])
def editWrestler(faction_id, wrestler_id):
    editedWrestler = session.query(Wrestler).filter_by(id=wrestler_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if login_session['user_id'] != editedWrestler.user_id:
        return "<script>function myFunction()\
        {alert('You shouldn't be here');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        if request.form['name']:
            editedWrestler.name = request.form['name']
        if request.form['description']:
            editedWrestler.description = request.form['description']
        if request.form['finisher']:
            editedWrestler.finisher = request.form['finisher']
        session.add(editedWrestler)
        session.commit()
        return redirect(url_for('showFactionDetail',
                                faction_id=faction_id,
                                login_session=login_session))
    else:

        return render_template(
            'editWrestler.html', faction_id=wrestler_id,
            wrestler_id=wrestler_id, wrestler=editedWrestler,
            login_session=login_session)


# Delete Wrestler
@app.route('/factions/<int:faction_id>/wrestler/<int:wrestler_id>/delete',
           methods=['GET', 'POST'])
def deleteWrestler(faction_id, wrestler_id):
    deletedWrestler = session.query(Wrestler).filter_by(id=wrestler_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if deletedWrestler.user_id != login_session['user_id']:
        return "<script>function myFunction()\
         {alert('You shouldn't be here);}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        session.delete(deletedWrestler)
        session.commit()
        return redirect(url_for('showFactionDetail',
                                faction_id=faction_id,
                                login_session=login_session))
    else:
        return render_template('deleteWrestler.html',
                               wrestler=deletedWrestler)


# Return JSONS of wrestler and faction data
@app.route('/factions/JSON')
def factionJSON():
    factions = session.query(Faction).all()
    return jsonify(factions=[f.serialize for f in factions])


@app.route('/factions/<int:faction_id>/wrestler/JSON')
def factionWrestlersJSON(faction_id):
    f_wrestlers = session.query(Wrestler).filter_by(id=faction_id).all()
    return jsonify(f_wrestlers=[f.serialize for f in f_wrestlers])


@app.route('/factions/<int:faction_id>/wrestler/<int:wrestler_id>/JSON')
def wrestlersJSON(faction_id, wrestler_id):
    wrestler = session.query(Wrestler).filter_by(id=wrestler_id).one()
    return jsonify(wrestler=wrestler.serialize)


if __name__ == '__main__':

    app.debug = False
    app.secret_key = 'super_secret_key'
    app.run(host='0.0.0.0', port=5000)
