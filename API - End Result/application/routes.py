from application import app, db
from flask import render_template, request, json, Response, redirect, flash, url_for, session, jsonify
from application.models import User, UserParameters, Articles, Rating
from application.forms import LoginForm, RegisterForm, SearchForm, RefreshForm, TimeForm
from application.search import get_forest, predict
from application.bot1 import bot1_recommendation
from application.bot2 import bot2_recommendation
import pandas as pd
from pymongo import MongoClient
import datetime

SESSION_PERMANENT = False
client = MongoClient("mongodb://localhost:27017/")
abc = client["News_Recommender"]
articles = abc["articles"]
corpus_df = pd.DataFrame(list(articles.find()))
corpus_df['Category'] = corpus_df['Category'].replace(['News'],'Miscellaneous')

@app.route("/", methods=['GET','POST'])
@app.route("/index", methods=['GET','POST'])
@app.route("/home", methods=['GET','POST'])
def index():
    
    form = RefreshForm()

    if session.get('username'):
        if UserParameters.objects(user_id=session.get('user_id'), session_id = 1):
            recommendations = bot1_recommendation(corpus_df)
        else:
            recommendations = bot2_recommendation(corpus_df, session.get('user_id'))

    else:
        ip = request.remote_addr
        if not User.objects(ip=ip):
            user_id     = User.objects.count()
            user_id     += 1
            session['user_id'] = user_id
            User(user_id=user_id, ip=ip).save()
            UserParameters(user_id=user_id, session_id=1).save()
            recommendations = bot1_recommendation(corpus_df)
        else:
            user_id = User.objects(ip=ip).only('user_id').first().user_id
            if not (session.get('user_id')):
                session['user_id'] = user_id
                UserParameters.objects(user_id=session.get('user_id')).update_one(inc__session_id=1)

            recommendations = bot2_recommendation(corpus_df, user_id)    
            print(recommendations)      
    
    if form.validate_on_submit():
        UserParameters.objects(user_id=session.get('user_id')).update_one(inc__session_id=1)
        return redirect("/index")
    return render_template("index.html", index=True, form=form,recommendations=recommendations)

@app.route("/login", methods=['GET','POST'])
def login():
    if session.get('username'):
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        email       = form.email.data
        password    = form.password.data

        user = User.objects(email=email).first()
        if user and user.get_password(password):
            flash(f"{user.first_name}, you are successfully logged in!", "success")
            session['user_id'] = user.user_id
            session['username'] = user.first_name
            UserParameters.objects(user_id=session.get('user_id')).update_one(inc__session_id=1)
            return redirect("/index")
        else:
            flash("Sorry, something went wrong.","danger")
    return render_template("login.html", title="Login", form=form, login=True )

@app.route("/logout")
def logout():
    session['user_id']=False
    session.pop('username',None)
    return redirect(url_for('index'))

@app.route("/search", methods=['GET','POST'])
def search():

    form = SearchForm()
    if form.validate_on_submit():
        phrase = form.phrase.data
        return redirect(url_for('search_results', phrase=phrase))
    return render_template("search.html", title="Search", form=form, search = True)

@app.route("/search/<phrase>")
def search_results(phrase):
    
    test = corpus_df
    permutations = 128
    test['text'] = test['Headline'] + ' ' + test['Entire_News']
    forest = get_forest(test, permutations)

    num_recommendations = 10
    results = predict(phrase, corpus_df, permutations, num_recommendations, forest)
    return render_template("search_results.html", title="Search for:", phrase=phrase, search = True, results=results)

@app.route("/register", methods=['POST','GET'])
def register():
    if session.get('username'):
        return redirect(url_for('index'))
    form = RegisterForm()
    if form.validate_on_submit():
        user_id     = User.objects.count()
        user_id     += 1

        email       = form.email.data
        password    = form.password.data
        first_name  = form.first_name.data
        last_name   = form.last_name.data
        ip          = None

        user = User(user_id=user_id, email=email, first_name=first_name, last_name=last_name, ip=ip)
        user.set_password(password)
        user.save()
        UserParameters(user_id=user_id, session_id=0).save()
        flash("You are successfully registered!","success")
        return redirect(url_for('index'))
    return render_template("register.html", title="Register", form=form, register=True)


@app.route("/news/<headline>")
def news(headline):
    print(headline)
    news_df = corpus_df[corpus_df["Headline"] == headline]
    news = news_df.to_dict("records")
    return render_template("news.html", newss=news)
