from flask import Flask, render_template, request, redirect, url_for, flash
from flask import session as login_session
import random
import string
from model import model
from validation import Validator
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import httplib2
import json
import requests
from flask import make_response, jsonify


app = Flask(__name__)
CLIENT_ID = json.loads(open("client_secrets.json", 'r')
                       .read())['web']['client_id']
APPLICATION_NAME = "catalogProject"


def dump_json_response(msg, status):
    response = make_response(json.dumps(msg), status)
    response.headers['Content-Type'] = 'application/json'
    return response


def is_user():
    """check if user signed in"""
    return 'username' in login_session


def serialize_category_items(obj):
    return {
        'id': obj.id,
        'name': obj.name,
        'description': obj.description,
        'category_name': obj.cname
    }


@app.route('/')
@app.route('/categories')
def home():
    # get all categories and last items
    categories = model.all_categories()
    items = model.last_items()
    return render_template("home.html",
                           items=items,
                           categories=categories,
                           is_user=is_user(),
                           login_session=login_session)


@app.route('/categories/<int:cid>/')
@app.route('/categories/<int:cid>/items')
def category_items(cid):
    # get all categories and the selected category and its items
    categories = model.all_categories()
    selected_category, items = model.category_items(cid)

    return render_template("category_items.html",
                           categories=categories,
                           selected_category=selected_category,
                           items=items,
                           count_items_in_category=model.count_items_in_category(cid),
                           is_user=is_user(),
                           login_session=login_session
                           )


@app.route('/categories/<int:cid>/items/<int:iid>')
def read_item(cid, iid):
    category, item, category_has_item = \
        model.category_item(cid, iid)
    authorized = is_user() and item.user_id == login_session['id']
    return render_template("read_item.html",
                           category=category,
                           item=item,
                           category_has_item=category_has_item,
                           is_user=is_user(),
                           login_session=login_session,
                           authorized=authorized
                           )


@app.route('/categories/0/items/create/', methods=['post', 'get'])
def create_item():
    if not is_user():
        return redirect(url_for("login"))
    # for form validation get an instance
    validate = Validator()
    if request.method == "POST":
        # get form fields values in variables
        name, description, category_id = \
            request.form.get('name').strip(), \
            request.form.get('description').strip(), \
            request.form.get('category_id')

        # validate form fields
        validate.validate(name, 'Name')
        validate.validate(description, 'Description')
        validate.validate(description, 'Category Name')
        # if form is valid create this item and send flash message
        if validate.valid_form():
            model.create_item(name=name,
                              description=description,
                              category_id=category_id,
                              user_id=login_session['id']
                              )
            flash("Item Created Successfully")
            return redirect(url_for("home"))

    categories = model.all_categories()
    return render_template("create_item.html",
                           categories=categories,
                           form_errors=validate.get_form_errors(),
                           is_user=is_user(),
                           login_session=login_session
                           )


# show form of updating and processing updating
@app.route('/categories/<int:cid>/items/<int:iid>/edit',
           methods=['get', 'post'])
def update_item(cid, iid):
    # from validation instance
    validate = Validator()
    selected_category, item, category_has_item = \
        model.category_item(iid=iid, cid=cid)
    # boolean checks if user is authorized to access this page
    authorized = category_has_item and is_user()\
                 and item.user_id == login_session['id']
    if not authorized:
        return redirect(url_for('login'))
    categories = model.all_categories()
    if request.method == 'POST':
        # get fields into variables
        iid, name, description, category_id = \
            request.form.get('id'), \
            request.form.get('name').strip(), \
            request.form.get('description').strip(), \
            request.form.get('category_id')
        # validate form
        validate.validate(field=name, field_name='Name')
        validate.validate(description, 'Description')
        validate.validate(category_id, "Category Name")
        # if form valid update
        if validate.valid_form():
            item = model.update_item(item,
                                     name=name,
                                     description=description,
                                     cid=category_id)
            # set message shows updated done successfully
            msg = "%s Item Updated Successfully" % name
            flash(msg)
            return redirect(url_for("update_item",
                                    iid=item.id, cid=item.category_id))

    return render_template("update_item.html",
                           categories=categories,
                           selected_category=selected_category,
                           item=item,
                           form_errors=validate.get_form_errors(),
                           category_has_item=category_has_item,
                           is_user=is_user(),
                           login_session=login_session
                           )


@app.route('/categories/<int:cid>/items/<int:iid>/delete',
           methods=['post', 'get'])
def delete_item(cid, iid):
    item = model.category_item(cid, iid)[1]
    if item is not None:
        if not is_user() and item.user_id != login_session['user_id']:
            return redirect(url_for('login'))
        model.delete(item)
        flash("Item deleted successfully")
    else:
        flash("Oops some thing went wrong!")
    return redirect(url_for("home"))


# google account connect by oAuth2
@app.route("/gconnect", methods=["POST"])
def gconnect():
    if is_user():
        return redirect(url_for("home"))
    # protectipn from CSRF attacks
    if request.args.get("state") != login_session["state"]:
        return dump_json_response("invalid state parameter", 401)
    code = request.data
    try:
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        return dump_json_response("failed to upgrade the authorization code",
                                  401)

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    if result.get('error') is not None:
        return dump_json_response(result.get('error'), 401)
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        return dump_json_response("token's user ID doesn't match given user",
                                  401)
    if result['issued_to'] != CLIENT_ID:
        return dump_json_response("token's client ID "
                                  "doesn't match given user", 401)
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        return dump_json_response("Current user is already connected", 200)

    # store the access token in the session for later use
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    # get user data
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()
    login_session['username'] = data['name']
    login_session['email'] = data['email']
    login_session['picture'] = data['picture']
    user_id = model.get_user_id(email=login_session['email'])
    # if this user is not signed sign him up
    if user_id is None:
        user_id = model.create_user(login_session=login_session)

    login_session['id'] = user_id
    return "<h1>%s</h1>" % login_session['username']


@app.route('/gdissconnect')
def gdissconnect():
    # if not signed redirect
    if not is_user():
        return redirect(url_for("home"))
    access_token = login_session.get('access_token')
    if access_token is None:
        return dump_json_response("user is not connected!", 401)
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
          % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        flash("disconnected successfully")
        return redirect(url_for("login"))
    else:
        return dump_json_response("failed to revoke token for given user", 401)


@app.route("/login")
def login():
    # if signed redirect him from login page
    if is_user():
        return redirect(url_for("home"))
    # CSRF token
    state = ''.join(random.choice(string.ascii_uppercase+string.digits)
                    for x in range(1, 32))
    login_session["state"] = state
    return render_template("login.html", state=state)


# json end points part
@app.route('/json/categories/<int:cid>/items')
def json_categories(cid):
    category, items = model.category_items(cid)
    return jsonify(category=category.serialize,
                   items=[serialize_category_items(i) for i in items])


@app.route('/json/categories/<int:cid>/items/<int:iid>')
def json_category(cid, iid):
    category, item, category_has_item =\
        model.category_item(cid, iid)
    if category_has_item:
        return jsonify(category=category.serialize,
                       item=item.serialize)
    else:
        return dump_json_response("no such item", 401)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
