#Bottle
from bottle import *
from bottleext import *
# avtorizacija za priklop na bazo
from auth_public import *
# za gesla
import hashlib
#za trenutni cas
from datetime import date    
# za priklop na bazo
import psycopg2, psycopg2.extensions, psycopg2.extras
#znebimo problema s sumniki
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)

import os
# privzete nastavitve
SERVER_PORT = os.environ.get('BOTTLE_PORT', 8080)
RELOADER = os.environ.get('BOTTLE_RELOADER', True)
DB_PORT = os.environ.get('POSTGRES_PORT', 5432)

# PRIKLOP NA BAZO
conn = psycopg2.connect(database=db, host=host, user=user, password=password, port=DB_PORT)
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor) 

# sporočila o napakah
debug(True)  # za izpise pri razvoju

# params
static_dir = "./static"

skrivnost = 'laqwXUtKfHTp1SSpnkSg7VbsJtCgYS89QnvE7PedkXqbE8pPj7VeRUwqdXu1Fr1kEkMzZQAaBR93PoGWks11alfe8y3CPSKh3mEQ'

########################################################################################
# Pomozne funkcije in funkcije s piskotki 
########################################################################################

def nastaviSporocilo(sporocilo = None):
    staro = request.get_cookie("sporocilo", secret=skrivnost)
    if sporocilo is None:
        response.delete_cookie('sporocilo', path="/")
    else:
        response.set_cookie('sporocilo', sporocilo, path="/", secret=skrivnost)
    return staro 

def preveriUporabnika(): 
    id_uporabnika = request.get_cookie("id", secret=skrivnost)
    if id_uporabnika:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        try: 
            cur.execute("SELECT id_uporabnika FROM uporabnik WHERE id_uporabnika = %s", [id_uporabnika])
            id_uporabnika = cur.fetchone()[0]
        except:
            id_uporabnika = None
        if id_uporabnika: 
            return id_uporabnika
    redirect(url('prijava_get'))


# za ločitev med prijavo in odjavo
def preveriZnacko():
    if request.get_cookie("id", secret = skrivnost):
        return 1
    else:
        return 0


# Ob napacnem vnoszu pri registraciji si zapomnimo vrednosti
def nastaviPiskotek(piskotek, vrednost):
    response.set_cookie(piskotek, vrednost, path="/", secret=skrivnost)

def preberiPiskotek(piskotek, privzeto=''):
    vrednost = request.get_cookie(piskotek, default=privzeto, secret=skrivnost)
    response.delete_cookie(piskotek, path="/")
    return vrednost

# pomoc za graf
def nastaviValuto(valuta = 'BTC'):
    staro = request.get_cookie("valuta", secret=skrivnost)
    if valuta is None:
        response.delete_cookie('valuta', path="/")
    else:
        response.set_cookie('valuta', valuta, path="/", secret=skrivnost)
    return staro

# zakodiranje gesl na bazi
def hashGesla(s):
    m = hashlib.sha256()
    m.update(s.encode("utf-8"))
    return m.hexdigest()


########################################################################################
# Začetne predpostavke
########################################################################################

@get('/')
def index():
    znacka = preveriZnacko()
    if znacka:
        redirect(url('uporabnik_get'))
    return template('zacetna_stran.html', znacka=znacka)

@get("/views/images/<filepath:re:.*\.(jpg|png|gif|ico|svg)>")
def img(filepath):
    return static_file(filepath, root="views/images")

@route("/static/<filename:path>")
def static(filename):
    return static_file(filename, root=static_dir)



########################################################################################
# Registracija
########################################################################################

@get('/registracija')
def registracija_get():
    napaka = nastaviSporocilo()
    ime = preberiPiskotek('ime')
    priimek = preberiPiskotek('priimek')
    spol = preberiPiskotek('spol', 'M')
    datum = preberiPiskotek('datum')
    drzava = preberiPiskotek('drzava')
    email = preberiPiskotek('email')

    return template('registracija.html', naslov="Registracija", napaka=napaka, ime=ime, priimek=priimek, spol=spol, datum=datum, drzava=drzava, email=email)

@post('/registracija')
def registracija_post():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    ime = request.forms.ime
    priimek = request.forms.priimek
    spol = request.forms.spol
    datum_rojstva = request.forms.datum_rojstva
    drzava = request.forms.drzava
    email = request.forms.email
    geslo = request.forms.geslo
    geslo2 = request.forms.geslo2

    try: 
        cur.execute("SELECT * FROM uporabnik WHERE email = %s", [email])
        data = cur.fetchall()   
        if data != []:
            email = None
        else:
            email = email
    except:
        email = email

    while True:
        if email is None:
            nastaviSporocilo('Registracija ni možna ta email je že v uporabi!')
        elif len(geslo) < 4:
            nastaviSporocilo('Geslo mora imeti vsaj 4 znake!')
        elif geslo != geslo2:
            nastaviSporocilo('Gesli se ne ujemata!')
        else: # ni napake, skočimo iz zanke
            break
        # imamo napako, nastavimo piškotke in preusmerimo
        nastaviPiskotek('ime', ime)
        nastaviPiskotek('priimek', priimek)
        nastaviPiskotek('spol', spol)
        nastaviPiskotek('datum', datum_rojstva)
        nastaviPiskotek('drzava', drzava)
        nastaviPiskotek('email', email)
        
        redirect(url('registracija_get'))
      
    zgostitev = hashGesla(geslo)

    try:
        cur.execute("""
            INSERT INTO uporabnik (ime, priimek, spol, datum_rojstva, drzava, email, geslo) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id_uporabnika
        """,
        [ime, priimek, spol, datum_rojstva, drzava, email, zgostitev])
        id_uporabnika = cur.fetchone()[0]
        conn.commit()
    except:
        nastaviSporocilo('Registracija ni možna!') 
        redirect(url('registracija_get'))

    response.set_cookie('id', id_uporabnika, secret=skrivnost)
    redirect(url('uporabnik_get'))




########################################################################################
# Prijava
########################################################################################

@get('/prijava') 
def prijava_get():
    napaka = nastaviSporocilo()
    return template("prijava.html", naslov = "Prijava", napaka=napaka)

@post('/prijava')
def prijava_post():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    email = request.forms.email
    geslo = request.forms.geslo

    try: 
        cur.execute("SELECT geslo FROM uporabnik WHERE email = %s", [email])
        hashBaza = cur.fetchone()[0]
    except:
        hashBaza = None

    if hashBaza is None:
        nastaviSporocilo('Elektronski naslov ne obstaja!') 
        redirect(url('prijava_get'))

    if hashGesla(geslo) != hashBaza:
        nastaviSporocilo('Elektronski naslov ali geslo nista ustrezni!') 
        redirect(url('prijava_get'))
    
    cur.execute('SELECT id_uporabnika FROM uporabnik WHERE email = %s', [email])
    id_uporabnika = cur.fetchone()[0]
    response.set_cookie('id', id_uporabnika, secret=skrivnost)
    redirect(url('uporabnik_get'))




########################################################################################
# Stanje uporabnika in izpis borz ter denarnic
########################################################################################

@get('/uporabnik')
def uporabnik_get():
    id_uporabnika = preveriUporabnika()
    znacka = preveriZnacko()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        #pridobitev stanj posameznih denarnc za posamezno borzo
        cur.execute('''
        WITH t1 AS (SELECT uporabnik_id,
                        borza_id,
                        iz_valute AS valuta,
                        sum(iz_kolicine) AS x
        FROM transakcija AS trx
        WHERE uporabnik_id = %s
        GROUP BY 1, 2, 3),
        t2 AS (SELECT uporabnik_id,
                    borza_id,
                    v_valuto AS valuta,
                    sum(v_kolicino) AS y
        FROM transakcija AS trx
        WHERE uporabnik_id = %s 
        GROUP BY 1, 2, 3),
        t3 AS (SELECT t1.uporabnik_id,
                    b.ime,
                    t1.valuta, 
                    COALESCE(y, 0) - COALESCE(x, 0) AS amount       
        FROM t1 
            FULL JOIN t2 ON t1.uporabnik_id = t2.uporabnik_id 
                AND t1.valuta = t2.valuta 
                AND t1.borza_id = t2.borza_id
            LEFT JOIN borza AS b ON b.id_borze = t1.borza_id
        WHERE t1.valuta <> ''),
        t4 AS (SELECT t2.uporabnik_id,
                    b.ime,
                    t2.valuta, 
                    COALESCE(y, 0) - COALESCE(x, 0) AS amount       
        FROM t2 
            FULL JOIN t1 ON t1.uporabnik_id = t2.uporabnik_id 
                AND t1.valuta = t2.valuta 
                AND t1.borza_id = t2.borza_id
            LEFT JOIN borza AS b ON b.id_borze = t2.borza_id
        WHERE t2.valuta <> '')
        SELECT * FROM t3 
        UNION 
        SELECT * FROM t4
        ''', [id_uporabnika]*2)
        data = cur.fetchall()
    except:
        data = []
    #pridobitev borz, ki jih uporabnik se nima
    cur.execute('''
        WITH t1 AS (SELECT DISTINCT id_borze FROM borza),
        excluded AS (SELECT DISTINCT borza_id FROM transakcija WHERE uporabnik_id = %s)
        SELECT t1.id_borze, t3.ime FROM t1 LEFT JOIN excluded AS t2 ON t2.borza_id = t1.id_borze 
        LEFT JOIN borza AS t3 ON t3.id_borze = t1.id_borze 
        WHERE t2.borza_id IS NULL
        ORDER BY 2
        ''', [id_uporabnika])
    uporabnik_borze = cur.fetchall()
    cur.execute("SELECT osnovna_valuta FROM devizni_tecaj WHERE osnovna_valuta <> 'USD' GROUP BY osnovna_valuta ORDER BY 1")
    valute = cur.fetchall()
    # izracun AUM
    cur.execute('''
    SELECT SUM(COALESCE(v_kolicino * er2.valutno_razmerje, 0)) - SUM(COALESCE(iz_kolicine * er1.valutno_razmerje, 0)) AS client_aum
        FROM transakcija
            LEFT JOIN devizni_tecaj AS er1 ON er1.osnovna_valuta = iz_valute AND er1.datum_razmerja = datum_cas	
            LEFT JOIN devizni_tecaj AS er2 ON er2.osnovna_valuta = v_valuto AND er2.datum_razmerja = datum_cas	
        WHERE uporabnik_id = %s
    ''', [id_uporabnika])
    aum = cur.fetchone()[0]  
    aum = aum if aum else 0
    napaka = nastaviSporocilo()
    return template('uporabnik.html', aum=aum, data=data, uporabnik_borze=uporabnik_borze, valute=valute, napaka=napaka, znacka=znacka)


@post('/uporabnik')
def uporabnik_post():
    id_uporabnika = preveriUporabnika()
    denarnica = request.forms.valuta
    ime_borze = request.forms.ime_borze
    borza_id = request.forms.id_borze
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    if ime_borze == "":
        cur.execute(""" 
        INSERT INTO transakcija ( uporabnik_id, borza_id, iz_kolicine, v_kolicino, v_valuto, tip_narocila) 
        VALUES (%s,%s,%s,%s,%s,%s);
        """,
        [id_uporabnika, borza_id, 0, 0, "USD", "A"])
        conn.commit()
        redirect(url('uporabnik_get'))
    else:
        cur.execute("SELECT id_borze FROM borza WHERE ime = %s ", [ime_borze])
        borza_id = cur.fetchone()[0] 
        cur.execute(""" 
        SELECT v_valuto FROM transakcija 
        WHERE uporabnik_id = %s AND borza_id = %s AND v_valuto <> ''
        GROUP BY v_valuto
        """, [id_uporabnika, borza_id])
        uporabnik_valute = cur.fetchall()
        if [denarnica] in uporabnik_valute:
            nastaviSporocilo("Ta denarnica že obstaja")
            redirect(url('uporabnik_get'))
        else:
            cur.execute(""" 
            INSERT INTO transakcija (uporabnik_id, borza_id, iz_kolicine, v_kolicino, v_valuto, tip_narocila) 
            VALUES (%s,%s,%s,%s,%s,%s);
            """,
            [id_uporabnika, borza_id, 0, 0, denarnica, "A"])
            conn.commit()
            redirect(url('uporabnik_get'))




########################################################################################
# Tansakcija
########################################################################################

@get('/transakcija/<borza>')
def transakcija_get(borza):
    id_uporabnika = preveriUporabnika()
    znacka = preveriZnacko()
    today = date.today()
    datum = today.strftime("%Y-%m-%d")
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT id_borze FROM borza WHERE ime = %s", [borza])
    borza_id = cur.fetchone()[0]
    cur.execute("""
    SELECT v_valuto FROM transakcija 
    WHERE uporabnik_id=%s AND borza_id = %s AND v_valuto <> ''
    GROUP BY v_valuto
    """, [id_uporabnika, borza_id])
    valute = cur.fetchall()
    napaka = nastaviSporocilo()
    return template("transakcija.html", borza=[borza_id, borza], datum=datum, valute=valute, napaka=napaka, znacka=znacka)


@post('/transakcija/<borza>')
def transkacija_post(borza):
    id_uporabnika = preveriUporabnika()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    iz_valute = request.forms.iz_valute
    v_valuto = request.forms.v_valuto
    iz_kolicine = float(request.forms.kolicina)
    datum_transakcije = request.forms.datum_transakcije
    borza_id = int(request.forms.id_borze)
    

    if iz_valute == v_valuto: #napaka
        nastaviSporocilo('Valuti morata biti različni, sicer transakcija ni možna!')
        redirect(url('transakcija_get', borza=borza))
        return
    elif iz_valute == 'USD': 
        cur.execute("""
        SELECT valutno_razmerje FROM devizni_tecaj
        WHERE osnovna_valuta = %s AND datum_razmerja = %s; 
        """, [v_valuto, datum_transakcije])
        razmerje = cur.fetchone()[0]
        razmerje = float(razmerje) if razmerje else 0
        v_kolicino = iz_kolicine / razmerje
        cur.execute(""" 
        INSERT INTO transakcija (uporabnik_id, borza_id, datum_cas, iz_kolicine, v_kolicino,iz_valute, v_valuto, tip_narocila) 
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s);
        """,
        [id_uporabnika, borza_id,datum_transakcije, iz_kolicine, v_kolicino, iz_valute, v_valuto, "T"])
        conn.commit()
    elif v_valuto == 'USD': 
        cur.execute("""
        SELECT valutno_razmerje FROM devizni_tecaj
        WHERE osnovna_valuta = %s AND datum_razmerja = %s; 
        """, [iz_valute, datum_transakcije])
        razmerje = cur.fetchone()[0]
        razmerje = float(razmerje) if razmerje else 0
        v_kolicino = iz_kolicine * razmerje
        cur.execute(""" 
        INSERT INTO transakcija (uporabnik_id, borza_id, datum_cas, iz_kolicine, v_kolicino,iz_valute, v_valuto, tip_narocila) 
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s);
        """,
        [id_uporabnika, borza_id, datum_transakcije, iz_kolicine, v_kolicino, iz_valute, v_valuto, "T"])
        conn.commit()
    else:
        cur.execute("""
        SELECT valutno_razmerje FROM devizni_tecaj
        WHERE osnovna_valuta = %s AND datum_razmerja = %s; 
        """, [iz_valute, datum_transakcije])
        razmerje1 = float(cur.fetchone()[0])
        cur.execute("""
        SELECT valutno_razmerje FROM devizni_tecaj
        WHERE osnovna_valuta = %s AND datum_razmerja = %s; 
        """, [v_valuto, datum_transakcije])
        razmerje2 = float(cur.fetchone()[0])
        v_kolicino = iz_kolicine * (razmerje1/razmerje2)   
        cur.execute(""" 
        INSERT INTO transakcija (uporabnik_id, borza_id, datum_cas, iz_kolicine, v_kolicino,iz_valute, v_valuto, tip_narocila) 
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s);
        """,
        [id_uporabnika, borza_id, datum_transakcije, iz_kolicine, v_kolicino, iz_valute, v_valuto, "T"])
        conn.commit()

    redirect(url('uporabnik_get'))

    


########################################################################################
# Polog in dvig valut 
#########################################################################################

@post('/depwith/<borza_id>')
def depwith_post(borza_id):
    id_uporabnika = preveriUporabnika()
    valuta = request.forms.valuta
    kolicina = float(request.forms.kolicina)
    datum_narocila = request.forms.datum
    narocilo = request.forms.narocilo
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT ime FROM borza WHERE id_borze = %s", [borza_id])
    borza = cur.fetchone()[0]
    
    if narocilo == "D":
        cur.execute(""" 
               INSERT INTO transakcija (uporabnik_id, borza_id, datum_cas, iz_kolicine, v_kolicino, v_valuto, tip_narocila) 
               VALUES (%s,%s,%s,%s,%s,%s,%s);
               """,
               [id_uporabnika, int(borza_id), datum_narocila, 0, kolicina, valuta, narocilo])
        conn.commit()
        redirect(url('uporabnik_get'))
    else:
        cur.execute('''
        WITH t0 AS (SELECT *
        FROM transakcija
        WHERE uporabnik_id = %s),

        t1 AS (SELECT uporabnik_id,
                            borza_id,
                            iz_valute AS valuta,
                            sum(iz_kolicine) AS x
        FROM t0 AS trx
        GROUP BY 1, 2, 3),

        t2 AS (SELECT uporabnik_id,
                    borza_id,
                    v_valuto AS valuta,
                    sum(v_kolicino) AS y
        FROM t0 AS trx 
        GROUP BY 1, 2, 3),

        t3 AS (SELECT t1.uporabnik_id,
                    b.id_borze,
                    t1.valuta, 
                    COALESCE(y, 0) - COALESCE(x, 0) AS amount       
        FROM t1 
            FULL JOIN t2 ON t1.uporabnik_id = t2.uporabnik_id 
                AND t1.valuta = t2.valuta 
                AND t1.borza_id = t2.borza_id
            LEFT JOIN borza AS b ON b.id_borze = t1.borza_id
        WHERE t1.valuta <> ''),

        t4 AS (SELECT t2.uporabnik_id,
                    b.id_borze,
                    t2.valuta, 
                    COALESCE(y, 0) - COALESCE(x, 0) AS amount       
        FROM t2 
            FULL JOIN t1 ON t1.uporabnik_id = t2.uporabnik_id 
                AND t1.valuta = t2.valuta 
                AND t1.borza_id = t2.borza_id
            LEFT JOIN borza AS b ON b.id_borze = t2.borza_id
        WHERE t2.valuta <> ''),

        t5 as(     
        SELECT * FROM t3 
        UNION 
        SELECT * FROM t4)

        SELECT t5.amount
        FROM t5 
        WHERE t5.id_borze = %s AND valuta = %s    
        ''',  [id_uporabnika, borza_id, valuta])
        stanje = cur.fetchone()[0]

        if stanje < kolicina:
            nastaviSporocilo('Stanje na denarnici je prenizko!')
            redirect(url('transakcija_get', borza=borza))
        else:
            cur.execute(""" 
                   INSERT INTO transakcija (uporabnik_id, borza_id, datum_cas, iz_kolicine, v_kolicino, iz_valute, v_valuto, tip_narocila) 
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s);
                   """,
                   [id_uporabnika, int(borza_id), datum_narocila, kolicina, 0, valuta, valuta, narocilo])
            conn.commit()
            redirect(url('uporabnik_get'))






########################################################################################
# Malo za salo malo za res
########################################################################################

@get('/profil')
def profil_get():
    id_uporabnika = preveriUporabnika()
    znacka = preveriZnacko()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT ime, priimek, datum_rojstva, spol, drzava, datum_registracije, email FROM uporabnik WHERE id_uporabnika = %s", [id_uporabnika])
    info = cur.fetchone()
    napaka = nastaviSporocilo()
    return template("profil.html",napaka=napaka, znacka=znacka, info=info)

@post('/profil')
def profil_post():
    id_uporabnika = preveriUporabnika()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    staro_geslo = request.forms.geslo_staro
    novo_geslo1 = request.forms.geslo1
    novo_geslo2 = request.forms.geslo2
    cur.execute("SELECT geslo FROM uporabnik WHERE id_uporabnika = %s", [id_uporabnika])
    hash_geslo = cur.fetchone()[0]
    if hashGesla(staro_geslo) != hash_geslo:
        nastaviSporocilo('Staro geslo je napačno!')
        redirect(url('profil_get'))
    elif len(novo_geslo1) < 4:
        nastaviSporocilo('Novo geslo mora imeti vsaj 4 znake')
        redirect(url('profil_get'))
    elif novo_geslo1 != novo_geslo2:
        nastaviSporocilo('Gesli se ne ujemata')
        redirect(url('profil_get'))
    else:
        novo_geslo = hashGesla(novo_geslo1)  
        cur.execute("UPDATE uporabnik SET geslo = %s WHERE id_uporabnika = %s", [novo_geslo, id_uporabnika])
        conn.commit()
        nastaviSporocilo('Uspešno')
        redirect(url('profil_get'))
        

@get('/about')
def about():
    znacka = preveriZnacko()
    return template("about.html", naslov='O podjetju', znacka=znacka)


@get('/borze')
def borze():
    znacka = preveriZnacko()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor) 
    cur.execute("SELECT ime, vrsta, lokacija, povezava FROM borza ORDER BY ime")
    data = cur.fetchall()
    return template("borze.html", naslov='Borze', data=data, znacka=znacka)


@get('/crypto')
def crypto():
    znacka = preveriZnacko()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor) 
    ime_valute = nastaviValuto() if nastaviValuto() != None else 'BTC'
    cur.execute('''
    SELECT to_char(datum_razmerja, 'YYYY-MM') as ym, 
        AVG(valutno_razmerje) as BTC_price
    FROM devizni_tecaj
    WHERE osnovna_valuta  = %s
    AND kotirajoca_valuta  = 'USD'
    AND datum_razmerja <= date(now())
    GROUP BY 1
    ORDER BY 1
    ''', [ime_valute])
    data = cur.fetchall()
    
    sez =[]
    vrednosti = []
    for vrstica in data:
        sez.append(str(vrstica[0]))
        vrednosti.append(str(vrstica[1]))
    sez = ','.join(sez)
    vrednosti = ','.join(vrednosti)

    cur.execute("SELECT * FROM valute WHERE valuta <> 'USD' ORDER BY 1 ")
    valute = cur.fetchall()
    return template("crypto.html", naslov='Crypto', sez=sez, vrednosti=vrednosti, znacka=znacka, valute=valute, ime_valute=ime_valute)


@post('/crypto')
def crypto_post():
    valuta = request.forms.valuta
    nastaviValuto(valuta=valuta)
    redirect(url('crypto'))
    



########################################################################################
# Odjava
########################################################################################

@get('/odjava')
def odjava():
    response.delete_cookie("id")
    redirect(url('index'))



run(host='localhost', port=SERVER_PORT, reloader=RELOADER)