DROP TABLE IF EXISTS devizni_tecaj;
DROP TABLE IF EXISTS transakcija;
DROP TABLE IF EXISTS valute;
DROP TABLE IF EXISTS borza;
DROP TABLE IF EXISTS uporabnik;

CREATE TABLE uporabnik (
    id_uporabnika SERIAL PRIMARY KEY,
    ime TEXT NOT NULL,
    priimek TEXT NOT NULL,  
    spol TEXT NOT NULL,
    datum_rojstva DATE NOT NULL,
    drzava TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    geslo TEXT NOT NULL,
    datum_registracije DATE NOT NULL DEFAULT now()
);

CREATE TABLE borza (
    id_borze INTEGER PRIMARY KEY,
    ime TEXT NOT NULL,
    vrsta TEXT NOT NULL,
    lokacija TEXT,
    povezava TEXT NOT NULL
);

CREATE TABLE valute (
    valuta TEXT PRIMARY KEY
);

CREATE TABLE transakcija (
    id_transakcije SERIAL PRIMARY KEY,
    uporabnik_id INTEGER REFERENCES uporabnik(id_uporabnika),
    borza_id INTEGER REFERENCES borza(id_borze),
    datum_cas TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
    iz_kolicine DOUBLE PRECISION,
    v_kolicino DOUBLE PRECISION,
    iz_valute TEXT REFERENCES valute(valuta),
    v_valuto TEXT REFERENCES valute(valuta),
    tip_narocila TEXT NOT NULL
);


CREATE TABLE devizni_tecaj (
    osnovna_valuta TEXT REFERENCES valute(valuta),
    kotirajoca_valuta TEXT REFERENCES valute(valuta),
    valutno_razmerje DOUBLE PRECISION NOT NULL,
    datum_razmerja DATE,
    PRIMARY KEY (osnovna_valuta, kotirajoca_valuta, datum_razmerja)
);
