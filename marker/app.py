from flask import *
import requests
from flask_oauth import OAuth
from flask_github import GitHub
from github import Github as git
from model import *

# You must configure these 3 values from Google APIs console
# https://code.google.com/apis/console
GOOGLE_CLIENT_ID = '42073104430-pmelurs143kkkm5mbh1cqd58o7kptgsg.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = 'Uu1CaNcwKAOxyFgbTh-qR1jM'
GOOGLE_REDIRECT_URI = '/googleoauth2callback'  # one of the Redirect URIs from Google APIs console
GIT_CLIENT_ID='1d3f2d20958f5563461d'
GIT_CLIENT_SECRET='2dbcb4911df26167ade0323bfe29f4eadecb2a73'
GIT_REDIRECT_URI='/gitoauth2callback'

SECRET_KEY = 'development key'
DEBUG = True

app = Flask(__name__)
app.debug = DEBUG
app.secret_key = SECRET_KEY
oauth = OAuth()
app.config['GITHUB_CLIENT_ID'] = GIT_CLIENT_ID
app.config['GITHUB_CLIENT_SECRET'] = GIT_CLIENT_SECRET

# For GitHub Enterprise
app.config['GITHUB_BASE_URL'] = 'https://api.github.com/'
app.config['GITHUB_AUTH_URL'] = 'https://github.com/login/oauth/'

github = GitHub(app)

google = oauth.remote_app('google',
base_url='https://www.google.com/accounts/',
authorize_url='https://accounts.google.com/o/oauth2/auth',
request_token_url=None,
request_token_params={'scope': 'https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email',
'response_type': 'code'},
access_token_url='https://accounts.google.com/o/oauth2/token',
access_token_method='POST',
access_token_params={'grant_type': 'authorization_code'},
consumer_key=GOOGLE_CLIENT_ID,
consumer_secret=GOOGLE_CLIENT_SECRET)

def getUser():
    return session.get('user')

def isLogged():
    loged = True
    if session.get('user') is None:
        loged = False
    return loged

def getUserName():
    user=getUser()
    if user is not None:
        return user.get('name')
    return None

def getUserEmail():
    user=getUser()
    if user is not None:
        return user.get('email')
    return None

def getUserPicture():
    user=getUser()
    if user is not None:
        return user.get('picture')
    return None

def checkForUser():
    if not check_for_user_by_email(getUserEmail()):
        add_user(getUserName(), ' ', getUserEmail())

@app.route('/logout')
def logout():
    session.pop('user',None)
    return "logged out"

@app.route('/test')
def index():
    user=getUser()
    if user is not None:
        return str(getUserName())+ str(getUserEmail())+str(getUserPicture())
    return "None"

@app.route('/loginEmail',methods = ['POST', 'GET'])
def loginEmail():
    if request.method=='POST':
        userEmail=request.form['email']
        password=request.form['pass']
        if check_for_user_by_email(userEmail):
            userName = login_by_email(userEmail, password)
            if userName is not None:
                session['user']={'name':userName,'email':userEmail}
                return redirect(url_for('index'))
            flash('wrong user or pass try again')
            return redirect(url_for('loginEmail'))
        flash('welcome new user')
        session['user'] = {'email': userEmail,'name':userEmail.split('@')[0]}
        return redirect(url_for('index'))


@app.route('/loginGit')
def loginGit():
    return github.authorize()

@app.route(GIT_REDIRECT_URI)
@github.authorized_handler
def authorizedGit(oauth_token):
    if oauth_token is None:
        flash("Authorization failed.")
        return redirect(url_for('index'))
    g=git(oauth_token)
    user=g.get_user()
    userData={"email":user.get_emails()[0]['email'],"name":user.login,"picture":user.avatar_url}
    print(type(userData))
    session['user']=userData
    checkForUser()
    return userData


@app.route('/loginGoogle')
def loginGoogle():
    callback=url_for('authorizedGoogle', _external=True)
    return google.authorize(callback=callback)

@app.route(GOOGLE_REDIRECT_URI)
@google.authorized_handler
def authorizedGoogle(resp):
    access_token = resp['access_token']
    access_token=access_token,''
    access_token = access_token[0]
    headers = {'Authorization': 'OAuth ' + access_token}
    res = requests.get('https://www.googleapis.com/oauth2/v1/userinfo',headers= headers)
    data=res.json()
    session['user']=data
    checkForUser()
    return data

@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html',loged=isLogged())

@app.route('/login')
def login():
    return render_template('login.html',loged=isLogged())


@app.route('/profile')
def profile():
     queryList=get_srcs_by_email(session['user']['email'])
     srcList=[]
     for q in queryList:
         print(q)
         src=get_src_by_id(q)
         print(src)
         d={'id':q,'src':src[0],'language':src[1]}
         srcList.append(d)
     return render_template('profile.html',list=srcList,loged=isLogged())


@app.route('/newpaste')
def newpaste():
    return render_template('newpaste.html',loged=isLogged())

@app.route('/addNewPaste',methods = ['POST', 'GET'])
def addPaste():
    if request.method=='POST':

        lan=request.form['syntaxhighlighting']
        src = mark_text(request.form['paste_code'],lan)
        email=getUserEmail()
        id=add_src(src,lan,email)
        return redirect('http://localhost:5000/viewPaste/'+str(id))
    return 'something went wrong'

@app.route('/viewPaste/<int:srcID>')
def viewPaste(srcID):
    src=get_src_by_id(srcID)
    if src is not None:
        return render_template('paste.html',src=src[0],lan=src[1],loged=isLogged())

    return "404 not found"
if __name__ == '__main__' :
    app.run(debug=True)

