from flask import Flask, render_template, url_for, redirect, request, session, flash
from wtforms import Form, StringField, TextAreaField, PasswordField, SelectField, validators
from bs4 import BeautifulSoup as soup
from urllib.request import Request, urlopen as uReq
import psycopg2 as dbapi2
import os, random, re, operator, time
import urllib.parse
import urllib.request


app = Flask(__name__)
app.secret_key = "super secret key"

##### DATABASE ( HEROKU or POSGRESQL ) ######

DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL is not None:
    config = DATABASE_URL
else:
    config = """dbname='se1' user='postgres' password='1'"""
########################################


##### PRODUCT CLASS ######

class Product(object):
    def __init__(self, attr, price, link, img, fav, logo,intprice):
        self.attr = attr
        self.price = price
        self.link = link
        self.image = img
        self.fav = fav
        self.logo = logo
        self.intprice = intprice

Products = []
logged_in = False

########################################



##### INDEX ( SEARCH ) ######

@app.route("/",methods=["POST","GET"])
def index():
    if request.method == 'POST':
        searchtext = request.form['search']
        session['searchtext'] = searchtext
        if searchtext == '':
            return render_template("index.html")
        elif not(is_ascii(searchtext)):
            flash('Search text cannot include Turkish character!', 'danger')
            return redirect(url_for("index")),404
        else:
            SearchParse(searchtext)
            return redirect(url_for("listele", i = 1))
    return render_template("index.html")

########################################


##### USER OPERATIONS ######

class RegisterForm(Form):
    name = StringField('', [validators.Length(min=1, max=50)])
    surname = StringField('', [validators.Length(min=1, max=50)])
    username = StringField('', [validators.Length(min=4, max=25)])
    email = StringField('', [validators.Length(min=4, max=50)])
    password = PasswordField('', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords dont match')
    ])
    confirm = PasswordField('')

@app.route("/register",methods=["POST","GET"])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name=form.name.data
        surname=form.surname.data
        email=form.email.data
        username = form.username.data
        password = form.password.data

        connection = dbapi2.connect(config)
        cursor = connection.cursor()
        cursor.execute("""SELECT * FROM users WHERE username = %s """,[username])
        if cursor.rowcount > 0:
            flash('Username already exist!','danger')
            return redirect(url_for("register")),404
        else:
            cursor.execute("""SELECT * FROM users WHERE email = %s """, [email])
            if cursor.rowcount > 0:
                flash('E-mail already exist!', 'danger')
                cursor.close()
                return redirect(url_for("register"))
            else:
                cursor.execute("""INSERT INTO users(ad,soyad,email,username,password) VALUES(%s, %s, %s,%s, %s)""",
                               (name,surname,email,username,password))
                connection.commit()
                cursor.close()
                flash('You are registered.', 'success')
                return redirect(url_for("login"))

    return render_template("register.html", form=form)

@app.route("/login",methods=["POST","GET"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password_form = request.form['password']

        connection = dbapi2.connect(config)
        cursor = connection.cursor()
        exist = cursor.execute("""SELECT * FROM users WHERE username = %s""", [username])
        row_count = 0
        for row in cursor:
            row_count += 1
        exist = cursor.execute("""SELECT * FROM users WHERE username = %s""", [username])
        if row_count > 0:
            user = cursor.fetchone()
            userid = user[0]
            userisim = user[1]
            usersoyisim = user[2]
            useremail = user[3]
            username = user[4]
            password = user[5]
            if password == password_form:
                session['logged_in'] = True
                session['username'] = username
                session['userid'] = userid
                session['userisim'] = userisim
                session['usersoyisim'] = usersoyisim
                session['useremail'] = useremail

                global logged_in
                logged_in = True
                #
                return redirect(url_for("index"))
            else:
                flash('Username or Password is incorrect!','danger')
                return render_template("login.html"),404
            cursor.close()
        else:
            flash('Username or Password is incorrect!', 'danger')
            return render_template("login.html"),404

    return render_template("login.html")

@app.route("/profile",methods=["POST","GET"])
def profile():
    return render_template("profile.html")

@app.route("/updateprofile",methods=["POST","GET"])
def updateprofile():

    if request.method == "POST":
        userid = session['userid']

        useremail = request.form['useremail']
        oldpassword = request.form['oldpassword']
        newpasswordfirst = request.form['newpasswordfirst']
        newpasswordsecond = request.form['newpasswordsecond']

        connection = dbapi2.connect(config)
        cursor = connection.cursor()
        cursor.execute("""SELECT * FROM users WHERE email = %s """, [useremail])
        if cursor.rowcount > 0:
            flash('E-mail already exist!', 'danger')
            cursor.close()
            return redirect(url_for("updateprofile"))
        else:
            cursor.execute("""SELECT * FROM users WHERE id = %s""", [userid])
            user = cursor.fetchone()
            if useremail == "" and oldpassword == "":
                flash('Fields cannot be empty!', 'danger')
                cursor.close()
                redirect(url_for("updateprofile"))
            elif useremail and oldpassword == "" and newpasswordfirst == "" and newpasswordsecond == "":
                cursor.execute("""UPDATE users SET email = '""" + useremail + """' WHERE username = '""" + session[
                    'username'] + """'""")
                connection.commit()
                cursor.close()
                session['useremail'] = useremail
                flash('Changed Credentials.', 'success')
                return redirect(url_for("profile"))
            elif oldpassword != user[5]:
                flash('Old password does not match!', 'danger')
                cursor.close()
                redirect(url_for("updateprofile"))
            elif oldpassword == "" or newpasswordfirst == "" or newpasswordsecond == "":
                flash('Password fields cannot be empty!', 'danger')
                cursor.close()
                redirect(url_for("updateprofile"))
            elif newpasswordfirst != newpasswordsecond:
                flash('New passwords does not match!', 'danger')
                cursor.close()
                redirect(url_for("updateprofile"))
            else:
                if useremail:
                    cursor.execute(
                        """UPDATE users SET password = '""" + newpasswordfirst + """' , email = '""" + useremail + """' WHERE username = '""" +
                        session['username'] + """'""")
                    session['useremail'] = useremail
                else:
                    cursor.execute(
                        """UPDATE users SET password = '""" + newpasswordfirst + """' WHERE username = '""" + session[
                            'username'] + """'""")
                connection.commit()
                cursor.close()
                flash('Changed Credentials.', 'success')
                return redirect(url_for("profile"))
    return render_template("updateprofile.html")

@app.route("/logout",methods=["POST","GET"])
def logout():
    session.clear()
    global logged_in
    logged_in = False
    return redirect(url_for("index"))

########################################


##### SEARCH FUNCTION ######

def SearchParse(searchtext):
    Products.clear()
    searchtext = (re.sub("[ ]", "+", searchtext))

    Amazon(searchtext)
    N11(searchtext)
    itopya(searchtext)
    Hepsiburada(searchtext)

    Products.sort(key=operator.attrgetter('intprice'))

##### SEARCH WEBSITES ######

def itopya(searchtext):
    global Products
    def find_between(s, first, last):
        try:
            start = s.index(first) + len(first)
            end = s.index(last, start)
            return s[start:end]
        except ValueError:
            return ""
    ff='price: "'
    ll = '",'

    url = "https://www.itopya.com/"  + searchtext + "/notebook/"
    user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'
    values = {'name': 'Michael Foord',
              'location': 'Northampton',
              'language': 'Python'}
    headers = {'User-Agent': user_agent}
    data = urllib.parse.urlencode(values)
    data = data.encode('ascii')
    req = urllib.request.Request(url, data, headers)
    with urllib.request.urlopen(req) as response:
        the_page = response.read()
    page_soup = soup(the_page, "html.parser")
    container = page_soup.findAll("div", {"class": "product col-md-3"})

    length = len(container)
    for count in range(0, length):
        c = container[count]
        script = c.script.text
        price = find_between(script, ff, ll)
        linkimg = c.find("div", {"class": "image col-md-8 text-center"})
        link = linkimg.a["href"]
        img = linkimg.a.img["src"]
        attributes = (c.find("div", {"class": "product-title col-md-12"})).a.text
        price = price + " TL"
        price_new = price.split('.')[0]
        fav = True
        logo = "../static/img/icon/itopya.png"
        Products.append(Product(attributes, price, link, img, fav, logo, int(price_new)))

def Amazon(searchtext):
    global Products
    my_url = "https://www.amazon.com.tr/s?k=" + searchtext + "&rh=n%3A12601898031&__mk_tr_TR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&ref=nb_sb_noss"
    uClient = uReq(my_url)
    page_html = uClient.read()
    uClient.close()

    page_soup = soup(page_html, "html.parser")
    container = page_soup.findAll("div", {"class": "sg-col-4-of-24 sg-col-4-of-12 sg-col-4-of-36 s-result-item sg-col-4-of-28 sg-col-4-of-16 sg-col sg-col-4-of-20 sg-col-4-of-32"})

    lenght = len(container)
    for i in range(0, lenght - 2):
        contain = container[i].find("span", {"data-component-type": "s-product-image"})
        link = contain.a["href"]
        link = "https://www.amazon.com.tr" + link
        print(link)
        contain = container[i].find("div", {"class": "a-section aok-relative s-image-square-aspect"})
        img = contain.img["src"]
        contain = container[i].find("span", {"class": "a-size-base-plus a-color-base a-text-normal"})
        attr = contain.text

        if container[i].find("span", {"class": "a-price-whole"}):
            price = container[i].find("span", {"class": "a-price-whole"}).text
            price_new = price.replace(",", "")
            price_int = price_new.replace(".", "")
        else:
            contain = container[i].find("div", {"class": "a-row a-size-base a-color-secondary"})
            price = contain.find("span", {"class": "a-color-base"}).text
            price = price[1:]
            new_price = price.split(",")[0]
            price_int = new_price.replace(".", "")
        fav = True
        logo = "../static/img/icon/amazon.png"
        price = price + "00 TL"
        Products.append(Product(attr, price, link, img, fav, logo, int(price_int)))

def N11(searchtext):
    global Products
    my_url = "https://www.n11.com/bilgisayar/dizustu-bilgisayar?q=" + searchtext + "&srt=PRICE_LOW"
    uClient = uReq(my_url)
    page_html = uClient.read()
    uClient.close()

    page_soup = soup(page_html, "html.parser")
    container = page_soup.findAll("div", {"class": "listView"})
    contain = container[0].findAll("li", {"class": "column"})

    lenght = len(contain)
    for i in range(0, lenght):
        temp = contain[i].find("div", {"class": "pro"})
        link = temp.a["href"]
        temp = contain[i].find("a", {"class": "plink"})
        attr = temp.img["alt"]
        img = temp.img["data-original"]
        temp = contain[i].find("div", {"class": "proDetail"})
        price = temp.ins.text
        price = re.sub(r"\s+", '', price)
        price_new = price.split(",")[0]
        price_int = price_new.replace(".", "")
        fav = True
        logo = "../static/img/icon/n11.png"
        if int(price_int) > 500:
            Products.append(Product(attr, price, link, img, fav, logo, int(price_int)))

def Hepsiburada(searchtext):
    global Products
    my_url = "https://www.hepsiburada.com/ara?q=" + searchtext + "&kategori=2147483646_3000500_98&siralama=artanfiyat"
    uClient = uReq(my_url)
    page_html = uClient.read()
    uClient.close()

    page_soup = soup(page_html, "html.parser")
    container = page_soup.findAll("li", {"class": "search-item col lg-1 md-1 sm-1 custom-hover not-fashion-flex"})

    lenght = len(container)
    for i in range(0, lenght):
        check = container[i].find("span", {"class": "out-of-stock-text"})
        if not check:
            link = container[i].a["href"]
            link = "https://www.hepsiburada.com" + link
            contain = container[i].find("div", {"class": "carousel-lazy-item"})
            img = contain.img["src"]
            attr = contain.img["alt"]
            contain = container[i].find("div", {"class": "price-value"})
            if contain:
                price = contain.text
                price = re.sub(r"\s+", '', price)
            else:
                contain = container[i].find("span", {"class": "price product-price"})
                price = contain.text
            price_new = price.split(",")[0]
            price_new = price_new.replace(".", "")
            price_int = int(price_new)
            fav = True
            logo = "../static/img/icon/hb.png"
            Products.append(Product(attr, price, link, img, fav, logo, price_int))

########################################


##### LIST PRODUCTS ######

@app.route("/listele/<int:i>",methods=["POST","GET"])
def listele(i):
    if (logged_in):
        getWishList()
    length = len(Products)
    urunler = []
    if i == 1 and length < 20:
        o = 0
        p = length
    if i == 1 and length >= 20:
        o = 0
        p = 20
    if i == 2 and length < 40:
        o = 20
        p = length
    if i == 2 and length >= 40:
        o = 20
        p = 40
    if i == 3 and length < 60:
        o = 40
        p = length
    if i == 3 and length >= 60:
        o = 40
        p = 60
    if i == 4 and length < 80:
        o = 60
        p = length
    if i == 4 and length >= 80:
        o = 60
        p = 80
    if i == 5 and length < 100:
        o = 80
        p = length
    if i == 5 and length >= 100:
        o = 80
        p = 100
    if i == 6 and length < 120:
        o = 100
        p = length
    if i == 6 and length >= 120:
        o = 100
        p = 120
    if i == 7 and length < 140:
        o = 120
        p = length
    if i == 7 and length >= 140:
        o = 120
        p = 140
    if i == 8 and length < 160:
        o = 140
        p = length
    if i == 8 and length >= 160:
        o = 140
        p = 160
    if i == 9 and length < 180:
        o = 160
        p = length
    if i == 9 and length >= 180:
        o = 160
        p = 180

    sayfasayisi = (int(length/20)) + 1
    sayfasayisi += 1
    return render_template("listele.html", i=i, length=length, o=o, p=p, products = Products, sayfasayisi = sayfasayisi)

########################################


##### SELECTING ATTRIBUTES FOR PRODUCTS ######

@app.route("/selectingAttribute",methods=["POST","GET"])
def selectingAttribute():
    global Products
    if request.method == "POST":
        Products.clear()
        brand = request.form['brand']
        cpu = request.form['cpu']
        ram = request.form['ram']
        storagemedia = request.form['storagemedia']
        minprice = request.form['minprice']
        maxprice = request.form['maxprice']

        AttributeHepsiBurada(brand,cpu,ram,storagemedia)
        AttributeN11(brand, cpu, ram, storagemedia)
        AttributeAmazon(brand, cpu, ram, storagemedia)
        Attributeitopya(brand, cpu, ram, storagemedia)

        Products.sort(key=operator.attrgetter('intprice'))

        if minprice == '':
            minprice = "0"
            minprice = int(minprice)
        else:
            minprice = int(minprice)
        if maxprice == '':
            maxprice = "50000"
            maxprice = int(maxprice)
        else:
            maxprice = int(maxprice)
        if minprice>=maxprice:
            flash('Min Price cannot be greater than Max Price!', 'danger')
            return render_template("selectingAttribute.html"), 404
        elif minprice < 0 or maxprice < 0:
            flash('Min Price or Max Price cannot be lower than zero!', 'danger')
        elif maxprice < 500:
            flash('Max Price cannot be lower than "500"!', 'danger')
        else:
            priceFilter(minprice,maxprice)
        return redirect(url_for("listele", i=1))
    return render_template("selectingAttribute.html")

##### SELECTING ATTRIBUTES FROM WEBSITES ######

def Attributeitopya(brand, cpu, ram, storagemedia):
    global Products
    Cpu = {"i7": "f=n&oid={_4849_:[4854]}",
           "i5": "f=n&oid={_4849_:[4855]}",
           "i3": "f=n&oid={_4849_:[4856]}"}

    Ram = {"4gb": "f=n&oid={_4947_:[4950]}",
           "8gb": "f=n&oid={_4947_:[4951]}",
           "16gb": "f=n&oid={_4947_:[4952]}",
           "32gb": "f=n&oid={_4947_:[4953]}"}

    StorageMedia = {"HDD": "f=n&oid={_4928_:[4931,4932,4934]}",
                    "SSD": "f=n&oid={_4929_:[4939,4940,4943,4944,5025]}"}
    count = 0
    if brand != "brands":
        my_url = "https://www.itopya.com/"+  brand   +"/notebook/"
    else:
        my_url = "https://www.itopya.com/bilgisayar/notebooklar/notebook/"

    num = len(my_url)

    dash = Cpu.get(cpu, 0)
    if dash:
        if count > 0:
            my_url = my_url + ","
            num = num + 1
        else:
            my_url = my_url + "?"
            num = num + 1
        my_url = insert_dash(my_url, num, dash)
        num = num + len(dash)
        count = count + 1

    dash = Ram.get(ram, 0)
    if dash:
        if count > 0:
            my_url = my_url + ","
            num = num + 1
        else:
            my_url = my_url + "?"
            num = num + 1
        my_url = insert_dash(my_url, num, dash)
        num = num + len(dash)
        count = count + 1

    dash = StorageMedia.get(storagemedia, 0)
    if dash:
        if count > 0:
            my_url = my_url + ","
            num = num + 1
        else:
            my_url = my_url + "?"
            num = num + 1
        my_url = insert_dash(my_url, num, dash)
        num = num + len(dash)
        count = count + 1

    def find_between(s, first, last):
        try:
            start = s.index(first) + len(first)
            end = s.index(last, start)
            return s[start:end]
        except ValueError:
            return ""
    ff='price: "'
    ll = '",'

    url = my_url
    user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'
    values = {'name': 'Michael Foord',
              'location': 'Northampton',
              'language': 'Python'}
    headers = {'User-Agent': user_agent}

    data = urllib.parse.urlencode(values)
    data = data.encode('ascii')
    req = urllib.request.Request(url, data, headers)
    with urllib.request.urlopen(req) as response:
        the_page = response.read()
    page_soup = soup(the_page, "html.parser")
    container = page_soup.findAll("div", {"class": "product col-md-3"})

    length = len(container)
    for count in range(0, length):
        c = container[count]
        script = c.script.text
        price = find_between(script, ff, ll)
        linkimg = c.find("div", {"class": "image col-md-8 text-center"})
        link = linkimg.a["href"]
        img = linkimg.a.img["src"]
        attributes = (c.find("div", {"class": "product-title col-md-12"})).a.text
        price = price + " TL"
        price_new = price.split('.')[0]
        fav = True
        logo = "../static/img/icon/itopya.png"
        Products.append(Product(attributes, price, link, img, fav, logo, int(price_new)))

def AttributeAmazon(brand, cpu, ram, storagemedia):
    global Products

    Brand = {
        "acer": "https://www.amazon.com.tr/s?k=acer&rh=n%3A12601898031&__mk_tr_TR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&ref=nb_sb_noss",
        "apple": "https://www.amazon.com.tr/s?i=computers&bbn=12601898031&rh=n%3A12466439031%2Cn%3A12466440031%2Cn%3A12601898031%2Cp_89%3AApple&dc&fst=as%3Aoff&qid=1576946952&rnid=12783585031&ref=sr_nr_p_n_feature_sixteen_browse-bin_1",
        "asus": "https://www.amazon.com.tr/s?i=computers&bbn=12601898031&rh=n%3A12466439031%2Cn%3A12466440031%2Cn%3A12601898031%2Cp_89%3AAsus%2Cp_36%3A12794913031&dc&fst=as%3Aoff&qid=1576947034&rnid=12783133031&ref=sr_nr_p_36_4",
        "lenovo": "https://www.amazon.com.tr/s?i=computers&bbn=12601898031&rh=n%3A12466439031%2Cn%3A12466440031%2Cn%3A12601898031%2Cp_36%3A320-1000000%2Cp_89%3ALenovo&dc&fst=as%3Aoff&qid=1576941948&rnid=13493765031&ref=sr_nr_p_89_1",
        "hp"	: "https://www.amazon.com.tr/s?i=computers&bbn=12601898031&rh=n%3A12466439031%2Cn%3A12466440031%2Cn%3A12601898031%2Cp_36%3A320-1000000%2Cp_89%3AHP&dc&fst=as%3Aoff&qid=1576941975&rnid=13493765031&ref=sr_nr_p_89_2",
        "casper" : "https://www.amazon.com.tr/s?i=computers&bbn=12601898031&rh=n%3A12466439031%2Cn%3A12466440031%2Cn%3A12601898031%2Cp_36%3A320-1000000%2Cp_89%3ACasper&dc&fst=as%3Aoff&qid=1576942002&rnid=13493765031&ref=sr_nr_p_89_3",
        "dell"   : "https://www.amazon.com.tr/s?i=computers&bbn=12601898031&rh=n%3A12466439031%2Cn%3A12466440031%2Cn%3A12601898031%2Cp_36%3A320-1000000%2Cp_89%3ADell&dc&fst=as%3Aoff&qid=1576942033&rnid=13493765031&ref=sr_nr_p_89_4",
        "msi"	  : "https://www.amazon.com.tr/s?i=computers&bbn=12601898031&rh=n%3A12466439031%2Cn%3A12466440031%2Cn%3A12601898031%2Cp_36%3A320-1000000%2Cp_89%3AMSI&dc&fst=as%3Aoff&qid=1576942054&rnid=13493765031&ref=sr_nr_p_89_4"}

    Ram = {"4gb": "https://www.amazon.com.tr/s?i=computers&bbn=12601898031&rh=n%3A12466439031%2Cn%3A12466440031%2Cn%3A12601898031%2Cp_36%3A320-1000000%2Cp_n_feature_sixteen_browse-bin%3A12783589031&dc&fst=as%3Aoff&qid=1576942143&rnid=12783585031&ref=sr_nr_p_n_feature_sixteen_browse-bin_4",
           "8gb": "https://www.amazon.com.tr/s?i=computers&bbn=12601898031&rh=n%3A12466439031%2Cn%3A12466440031%2Cn%3A12601898031%2Cp_36%3A320-1000000%2Cp_n_feature_sixteen_browse-bin%3A12783591031&dc&fst=as%3Aoff&qid=1576942193&rnid=12783585031&ref=sr_nr_p_n_feature_sixteen_browse-bin_5",
           "16gb": "https://www.amazon.com.tr/s?i=computers&bbn=12601898031&rh=n%3A12466439031%2Cn%3A12466440031%2Cn%3A12601898031%2Cp_36%3A320-1000000%2Cp_n_feature_sixteen_browse-bin%3A12783592031&dc&fst=as%3Aoff&qid=1576942233&rnid=12783585031&ref=sr_nr_p_n_feature_sixteen_browse-bin_6",
           "32gb": "https://www.amazon.com.tr/s?i=computers&bbn=12601898031&rh=n%3A12466439031%2Cn%3A12466440031%2Cn%3A12601898031%2Cp_36%3A320-1000000%2Cp_n_feature_sixteen_browse-bin%3A12783592031&dc&fst=as%3Aoff&qid=1576942233&rnid=12783585031&ref=sr_nr_p_n_feature_sixteen_browse-bin_6"}

    Combine = {
            "acer-4gb": "https://www.amazon.com.tr/s?k=acer+4gb&rh=n%3A12601898031&__mk_tr_TR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&ref=nb_sb_noss",
            "acer-8gb":"https://www.amazon.com.tr/s?k=acer+8gb&rh=n%3A12601898031&__mk_tr_TR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&ref=nb_sb_noss",
            "acer-16gb":"https://www.amazon.com.tr/s?k=acer+8gb&rh=n%3A12601898031&__mk_tr_TR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&ref=nb_sb_noss",
            "acer-32gb":"https://www.amazon.com.tr/s?k=acer+8gb&rh=n%3A12601898031&__mk_tr_TR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&ref=nb_sb_noss",
             "apple-4gb": "https://www.amazon.com.tr/s?bbn=12601898031&rh=n%3A12466439031%2Cn%3A%2112466440031%2Cn%3A12601898031%2Cp_n_feature_four_browse-bin%3A12783168031%2Cp_89%3AApple&dc&fst=as%3Aoff&qid=1576997441&rnid=13493765031&ref=sr_in_-2_p_89_0",
             "apple-8gb": "https://www.amazon.com.tr/s?bbn=12601898031&rh=n%3A12466439031%2Cn%3A%2112466440031%2Cn%3A12601898031%2Cp_n_feature_four_browse-bin%3A12783168031%2Cp_89%3AApple&dc&fst=as%3Aoff&qid=1576997441&rnid=13493765031&ref=sr_in_-2_p_89_0",
             "apple-16gb": "https://www.amazon.com.tr/s?bbn=12601898031&rh=n%3A12466439031%2Cn%3A%2112466440031%2Cn%3A12601898031%2Cp_n_feature_four_browse-bin%3A12783168031%2Cp_89%3AApple&dc&fst=as%3Aoff&qid=1576997441&rnid=13493765031&ref=sr_in_-2_p_89_0",
             "apple-32gb": "https://www.amazon.com.tr/s?bbn=12601898031&rh=n%3A12466439031%2Cn%3A%2112466440031%2Cn%3A12601898031%2Cp_n_feature_four_browse-bin%3A12783168031%2Cp_89%3AApple&dc&fst=as%3Aoff&qid=1576997441&rnid=13493765031&ref=sr_in_-2_p_89_0",
             "asus-4gb":"https://www.amazon.com.tr/s?k=asus+4gb&i=computers&rh=n%3A12601898031%2Cp_n_feature_sixteen_browse-bin%3A12783589031&dc&__mk_tr_TR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&qid=1576997684&rnid=12783585031&ref=sr_nr_p_n_feature_sixteen_browse-bin_4",
             "asus-8gb":"https://www.amazon.com.tr/s?k=asus+8gb&i=computers&rh=n%3A12601898031%2Cp_36%3A390000-&__mk_tr_TR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&qid=1576997723&rnid=12783133031&ref=sr_nr_p_36_3",
             "asus-16gb":"https://www.amazon.com.tr/s?k=asus+16gb&rh=n%3A12601898031&__mk_tr_TR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&ref=nb_sb_noss",
             "asus-32gb":"https://www.amazon.com.tr/s?k=asus+32gb&rh=n%3A12601898031&__mk_tr_TR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&ref=nb_sb_noss",
             "lenovo-4gb":"https://www.amazon.com.tr/s?k=lenovo+4gb&i=computers&rh=n%3A12601898031%2Cp_n_feature_sixteen_browse-bin%3A12783589031&dc&__mk_tr_TR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&qid=1576997817&rnid=12783585031&ref=sr_nr_p_n_feature_sixteen_browse-bin_4",
             "lenovo-8gb":"https://www.amazon.com.tr/s?k=lenovo+8gb&rh=n%3A12601898031&__mk_tr_TR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&ref=nb_sb_noss",
             "lenovo-16gb":"https://www.amazon.com.tr/s?k=lenovo+16gb&i=computers&rh=n%3A12601898031%2Cp_36%3A300000-&__mk_tr_TR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&qid=1576997850&rnid=12783133031&ref=sr_nr_p_36_1",
             "lenovo-32gb":"https://www.amazon.com.tr/s?k=lenovo+16gb&i=computers&rh=n%3A12601898031%2Cp_36%3A300000-&__mk_tr_TR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&qid=1576997850&rnid=12783133031&ref=sr_nr_p_36_1",
             "hp-4gb":"https://www.amazon.com.tr/s?k=hp+4gb&rh=n%3A12601898031&__mk_tr_TR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&ref=nb_sb_noss",
             "hp-8gb":"https://www.amazon.com.tr/s?k=hp+8gb&rh=n%3A12601898031&__mk_tr_TR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&ref=nb_sb_noss",
             "hp-16gb":"https://www.amazon.com.tr/s?k=hp+16gb&rh=n%3A12601898031&__mk_tr_TR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&ref=nb_sb_noss",
            "hp-32gb":"https://www.amazon.com.tr/s?k=hp+16gb&rh=n%3A12601898031&__mk_tr_TR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&ref=nb_sb_noss",
            "casper-4gb":"https://www.amazon.com.tr/s?k=casper+4gb&rh=n%3A12601898031&__mk_tr_TR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&ref=nb_sb_noss",
            "casper-8gb":"https://www.amazon.com.tr/s?k=casper+8gb&rh=n%3A12601898031&__mk_tr_TR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&ref=nb_sb_noss",
            "casper-16gb":"https://www.amazon.com.tr/s?k=casper+16gb&rh=n%3A12601898031&__mk_tr_TR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&ref=nb_sb_noss",
            "casper-32gb":"https://www.amazon.com.tr/s?k=casper+16gb&rh=n%3A12601898031&__mk_tr_TR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&ref=nb_sb_noss",
            "dell-4gb":"https://www.amazon.com.tr/s?k=dell+4gb&rh=n%3A12601898031&__mk_tr_TR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&ref=nb_sb_noss",
            "dell-8gb":"https://www.amazon.com.tr/s?k=dell+8gb&rh=n%3A12601898031&__mk_tr_TR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&ref=nb_sb_noss",
            "dell-16gb":"https://www.amazon.com.tr/s?k=dell+16gb&rh=n%3A12601898031&__mk_tr_TR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&ref=nb_sb_noss",
            "dell-32gb":"https://www.amazon.com.tr/s?k=dell+16gb&rh=n%3A12601898031&__mk_tr_TR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&ref=nb_sb_noss",
            "msi-4gb":"https://www.amazon.com.tr/s?k=msi+8gb&rh=n%3A12601898031&__mk_tr_TR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&ref=nb_sb_noss",
            "msi-8gb":"https://www.amazon.com.tr/s?k=msi+8gb&rh=n%3A12601898031&__mk_tr_TR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&ref=nb_sb_noss",
            "msi-16gb":"https://www.amazon.com.tr/s?k=msi+16gb&rh=n%3A12601898031&__mk_tr_TR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&ref=nb_sb_noss",
            "msi-32gb": "https://www.amazon.com.tr/s?k=msi+32gb&rh=n%3A12601898031&__mk_tr_TR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&ref=nb_sb_noss"}

    if brand == "brands" and ram == "ram":
        my_url = "https://www.amazon.com.tr/s?bbn=12601898031&rh=n%3A12466439031%2Cn%3A%2112466440031%2Cn%3A12601898031%2Cp_n_feature_four_browse-bin%3A12783168031&dc&fst=as%3Aoff&qid=1576945686&rnid=12783165031&ref=lp_12601898031_nr_p_n_feature_four_bro_2"
    elif brand != "brands" and ram != "ram":
        x = brand + "-" + ram
        my_url = Combine[x]
    elif brand != "brands" and ram == "ram":
        my_url = Brand[brand]
    else:
        my_url = Ram[ram]

    uClient = uReq(my_url)
    page_html = uClient.read()
    uClient.close()

    page_soup = soup(page_html, "html.parser")
    container = page_soup.findAll("div", {
        "class": "sg-col-4-of-24 sg-col-4-of-12 sg-col-4-of-36 s-result-item sg-col-4-of-28 sg-col-4-of-16 sg-col sg-col-4-of-20 sg-col-4-of-32"})

    lenght = len(container)
    for i in range(0, lenght - 2):
        contain = container[i].find("span", {"data-component-type": "s-product-image"})
        link = contain.a["href"]
        link =  "https://www.amazon.com.tr" + link
        contain = container[i].find("div", {"class": "a-section aok-relative s-image-square-aspect"})
        img = contain.img["src"]
        contain = container[i].find("span", {"class": "a-size-base-plus a-color-base a-text-normal"})
        attr = contain.text

        if container[i].find("span", {"class": "a-price-whole"}):
            price = container[i].find("span", {"class": "a-price-whole"}).text
            price_new = price.replace(",", "")
            price_int = price_new.replace(".", "")
        else:
            contain = container[i].find("div", {"class": "a-row a-size-base a-color-secondary"})
            price = contain.find("span", {"class": "a-color-base"}).text
            price = price[1:]
            new_price = price.split(",")[0]
            price_int = new_price.replace(".", "")
        fav = True
        logo = "../static/img/icon/amazon.png"
        price = price + "00 TL"
        Products.append(Product(attr, price, link, img, fav, logo, int(price_int)))

def AttributeN11(brand,cpu,ram,storagemedia):
    global Products
    Cpu = {"i7": "islemci=Intel+Core+%C4%B07",
           "i5": "islemci=Intel+Core+%C4%B05",
           "i3": "islemci=Intel+Core+%C4%B03"}

    Ram = {"4gb": "sistembellegigb=4+Gb",
           "8gb": "sistembellegigb=8+Gb",
           "16gb": "sistembellegigb=16+Gb",
           "32gb": "sistembellegigb=32+Gb"}

    StorageMedia = {"HDD": "ssd=Yok",
                    "SSD": "ssd=256+Gb-512+Gb-128+Gb-1+Tb-240+Gb-480+Gb-120+Gb-32+Gb-250+Gb-2+Tb-64+Gb-4+Tb"}

    brand = brand.capitalize()
    count = 0
    if brand != "Brands":
        my_url = "https://www.n11.com/bilgisayar/dizustu-bilgisayar?m=" + brand
        count = count + 1
    else:
        my_url = "https://www.n11.com/bilgisayar/dizustu-bilgisayar"

    num = len(my_url)
    dash = Cpu.get(cpu, 0)
    if dash:
        if count > 0:
            my_url = my_url + "&"
            num = num + 1
        else:
            my_url = my_url + "?"
            num = num + 1
        my_url = insert_dash(my_url, num, dash)
        num = num + len(dash)
        count = count + 1

    dash = Ram.get(ram, 0)
    if dash:
        if count > 0:
            my_url = my_url + "&"
            num = num + 1
        else:
            my_url = my_url + "?"
            num = num + 1
        my_url = insert_dash(my_url, num, dash)
        num = num + len(dash)
        count = count + 1

    dash = StorageMedia.get(storagemedia, 0)
    if dash:
        if count > 0:
            my_url = my_url + "&"
            num = num + 1
        else:
            my_url = my_url + "?"
            num = num + 1
        my_url = insert_dash(my_url, num, dash)
        num = num + len(dash)
        count = count + 1

    uClient = uReq(my_url)
    page_html = uClient.read()
    uClient.close()

    page_soup = soup(page_html, "html.parser")

    container = page_soup.findAll("div", {"class": "listView"})
    contain = container[0].findAll("li", {"class": "column"})

    lenght = len(contain)
    for i in range(0, lenght):
        temp = contain[i].find("div", {"class": "pro"})
        link = temp.a["href"]

        temp = contain[i].find("a", {"class": "plink"})
        attr = temp.img["alt"]
        img = temp.img["data-original"]

        temp = contain[i].find("div", {"class": "proDetail"})
        price = temp.ins.text
        price = re.sub(r"\s+", '', price)
        price_new = price.split(",")[0]
        price_int = price_new.replace(".", "")
        fav = True
        logo = "../static/img/icon/n11.png"
        if int(price_int) > 500:
            Products.append(Product(attr, price, link, img, fav, logo, int(price_int)))

def AttributeHepsiBurada(brand,cpu,ram,storagemedia):
    global Products

    Cpu = {"i7": "?filtreler=islemcitipi:Intel%E2%82%AC20Core%E2%82%AC20i7",
           "i5": "?filtreler=islemcitipi:Intel%E2%82%AC20Core%E2%82%AC20i5",
           "i3": "?filtreler=islemcitipi:AMD%E2%82%AC20Ryzen%E2%82%AC205",
           "ryzen": "?filtreler=islemcitipi:AMD%E2%82%AC20Ryzen%E2%82%AC205"}

    Ram = {
        "4gb": "?filtreler=VariantList.Ram%E2%82%AC20%E2%82%AC28Sistem%E2%82%AC20Belle%E2%82%ACC4%E2%82%AC9Fi%E2%82%AC29:4%E2%82%AC20GB",
        "8gb": "?filtreler=VariantList.Ram%E2%82%AC20%E2%82%AC28Sistem%E2%82%AC20Belle%E2%82%ACC4%E2%82%AC9Fi%E2%82%AC29:8%E2%82%AC20GB",
        "16gb": "?filtreler=VariantList.Ram%E2%82%AC20%E2%82%AC28Sistem%E2%82%AC20Belle%E2%82%ACC4%E2%82%AC9Fi%E2%82%AC29:16%E2%82%AC20GB",
        "32gb": "?filtreler=VariantList.Ram%E2%82%AC20%E2%82%AC28Sistem%E2%82%AC20Belle%E2%82%ACC4%E2%82%AC9Fi%E2%82%AC29:16%E2%82%AC20GB"}

    StorageMedia = {"HDD": "?filtreler=ssdkapasitesi:128%E2%82%AC20GB,256%E2%82%AC20GB,512%E2%82%AC20GB",
           "SSD": "?filtreler=harddiskkapasitesi1:1%E2%82%AC20TB"}

    if brand != "brands":
        my_url = "https://www.hepsiburada.com/" + brand + "/laptop-notebook-dizustu-bilgisayarlar-c-98"
    else:
        my_url = "https://www.hepsiburada.com/laptop-notebook-dizustu-bilgisayarlar-c-98"
    count = 0
    num = len(my_url)

    dash = Cpu.get(cpu, 0)
    if dash:
        if count > 0:
            my_url = my_url + ";"
            num = num + 1
        my_url = insert_dash(my_url, num, dash)
        num = num + len(dash)
        count = count + 1

    dash = Ram.get(ram, 0)
    if dash:
        if count > 0:
            my_url = my_url + ";"
            num = num + 1
        my_url = insert_dash(my_url, num, dash)
        num = num + len(dash)
        count = count + 1

    dash = StorageMedia.get(storagemedia, 0)
    if dash:
        if count > 0:
            my_url = my_url + ";"
            num = num + 1
        my_url = insert_dash(my_url, num, dash)
        num = num + len(dash)
        count = count + 1

    my_url = my_url.encode('ascii', 'ignore').decode('ascii')
    uClient = uReq(my_url)
    page_html = uClient.read()
    uClient.close()

    page_soup = soup(page_html, "html.parser")
    container = page_soup.findAll("li", {"class": "search-item col lg-1 md-1 sm-1 custom-hover not-fashion-flex"})

    lenght = len(container)
    for i in range(0, lenght):
        check = container[i].find("span", {"class": "out-of-stock-text"})
        if not check:
            link = container[i].a["href"]
            link = "https://www.hepsiburada.com" + link
            contain = container[i].find("div", {"class": "carousel-lazy-item"})
            img = contain.img["src"]
            attr = contain.img["alt"]
            contain = container[i].find("div", {"class": "price-value"})
            if contain:
                price = contain.text
                price = re.sub(r"\s+", '', price)
            else:
                contain = container[i].find("span", {"class": "price product-price"})
                price = contain.text
            price_new = price.split(",")[0]
            price_new = price_new.replace(".", "")
            price_int = int(price_new)
            fav = True
            logo = "../static/img/icon/hb.png"
            Products.append(Product(attr, price, link, img, fav, logo, price_int))

########################################


##### FAVORITE OPERATIONS ######

def getWishList():
    userid = session['userid']
    connection = dbapi2.connect(config)
    cursor = connection.cursor()
    cursor.execute("""SELECT * FROM wishlist WHERE userid = %s""", [userid])
    wishlist = cursor.fetchall()
    session['wishlist'] = wishlist
    connection.commit()
    cursor.close()
    y=len(Products)
    for i in range(0,y):
        link = Products[i].link
        for row in wishlist:
            if(row[4] == link):
                Products[i].fav = False

@app.route("/favorites",methods=["POST","GET"])
def favorites():
    global Products
    getWishList()
    large = len(Products)
    if large > 3:
        AdsProducts = []
        ads1 = random.randrange(0, (large-1))
        ads2 = random.randrange(0, (large-1))
        ads3 = random.randrange(0, (large-1))

        AdsProducts.append(Products[ads1])
        AdsProducts.append(Products[ads2])
        AdsProducts.append(Products[ads3])
        return render_template("favorites.html",adsProducts = AdsProducts,large=large)
    return render_template("favorites.html",large=large)

@app.route("/addfavorite/<int:s>/<int:j>",methods=["POST","GET"])
def addfavorite(s,j):
    if session['logged_in']:
        title = Products[s].attr
        link =  Products[s].link
        image = Products[s].image
        price = Products[s].price
        logo = Products[s].logo
        userid = session['userid']
        connection = dbapi2.connect(config)
        cursor = connection.cursor()
        cursor.execute("""INSERT INTO wishlist(userid,urun_image,urun_title,urun_link,urun_price,urun_logo) VALUES(%s, %s, %s, %s, %s,%s)""",
                       (userid, image, title, link, price, logo))
        connection.commit()
        cursor.close()
        return redirect(url_for('listele', i=j))
    else:
        return redirect(url_for("login"))
    return render_template("listele.html")

@app.route("/unFavorite/<int:s>/<int:j>",methods=["POST","GET"])
def unFavorite(s,j):
    link = Products[s].link
    if session['logged_in']:
        userid= session['userid']
        connection = dbapi2.connect(config)
        cursor = connection.cursor()
        cursor.execute("""DELETE FROM wishlist WHERE userid = %s AND urun_link = %s """, (userid, link))
        connection.commit()
        cursor.close()
        Products[s].fav = True
        return redirect(url_for('listele', i=j))
    return render_template("listele.html")

@app.route("/deleteFavorite/<string:favid>",methods=["POST","GET"])
def deleteFavorite(favid):
    connection = dbapi2.connect(config)
    cursor = connection.cursor()
    cursor.execute("""DELETE FROM wishlist WHERE wish_id = %s""", [favid])
    connection.commit()
    cursor.close()
    return redirect(url_for("favorites"))

########################################


##### OTHER FUNCTIONS ( FILTER - ADDING STRING - IS ASCII? ) ######

def insert_dash(string, index, input):
    return string[:index] + input + string[index:]

def priceFilter(minprice,maxprice):
    global Products
    length = len(Products)
    Products = [x for x in Products if not (x.intprice < minprice or x.intprice > maxprice)]

def is_ascii(s):
    return all(ord(c) < 128 for c in s)

########################################


##### CONTACT ######

@app.route("/contact",methods=["POST","GET"])
def cotact():
    return render_template("contact.html")

@app.route("/aboutus",methods=["POST","GET"])
def aboutus():
    return render_template("aboutus.html")

########################################





if __name__ == '__main__':
    app.run()


