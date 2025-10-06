from flask import Flask, request, render_template

import Parsing_politics_science_health as PSH
import Parsing_sport_IT_education as SIE



app = Flask(__name__)

cnt = list(range(1))


@app.route('/')
def base():
    arr = SIE.parse_latest_news_it(SIE.URL_IT)
    return render_template('base.html', 
                            news=arr["news"],
                            countF=cnt)


@app.route('/pronget')
def pronget():
    return render_template('pronget.html', name='Dima')


@app.route('/pol')
def pol():
    arr = PSH.parse_latest_news_politics(PSH.URL_POLITICS)
    return render_template('pol.html',
                           news=arr["news"]
                           )


@app.route('/it')
def it():
    arr = SIE.parse_latest_news_it(SIE.URL_IT)
    return render_template('it.html',
                           news=arr["news"]
                           )


@app.route('/sp')
def sp():
    arr = SIE.parse_latest_news_sport(SIE.URL_SPORT)
    return render_template('sport.html',
                           news=arr["news"]
                           )


@app.route('/educ')
def educ():
    arr = SIE.parse_latest_news_education(SIE.URL_EDUCATION)
    return render_template('educ.html',
                           news=arr["news"]
                           )


@app.route('/healph')
def heal():
    arr = PSH.parse_latest_news_health(PSH.URL_HEALTH)
    return render_template('heal.html',
                           news=arr["news"]
                           )


@app.route('/science')
def scin():
    arr = PSH.parse_latest_news_science(PSH.URL_SCIENCE)
    return render_template('scin.html',
                           news=arr["news"]
                           )



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == 'Maxim' and password == '1234':
            print(username + "  " + password)
            return base()
        else:
            return render_template('login.html')
    else:
        return render_template('login.html')


if __name__ == '__main__':
    app.run(debug = True, port=8000)

    
                                                