
#  <img src="https://github.com/MatejRojec/Gamma/blob/main/logo.jpg" width="40" height="40"> 



<p align="center">
  <img src="https://readme-typing-svg.herokuapp.com?lines=Gamma&center=true&width=500&height=50">
</p>


## Start app:

[![bottle.py](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/vitorozman/GAMMA/main?urlpath=proxy/8080/)

## Opis

To je repozitorij projekta pri predmetu Osnove podatkovnih baz. Naš projekt je namenjen beleženju vseh kripto sredstev uporabnika (AUM). Ko se uporabnik registrera dobi "Gama" račun, kjer ima možnost povezati svoje denarnice, odprte na različnih borzah. Skupno stanje se posodablja s trenutnimi deviznimi tečaji. Ko se uporabnik odloči za investicijo (ali katero koli drugo spremebo v denarnici), to ročno spremeni in vnese potrebne informacije za spremembo. Tako se mu stanje posodobi in mu omogoča pregled in vrednost celotnega portfelja.

## ER 
Povezava do [ER](https://github.com/MatejRojec/Gamma/blob/main/ER.pdf) diagrama.

## Struktura baze

Tu so naštete tabele, ki jih bomo imeli v naši bazi:
- Uporabnik (ID uporabnika, ime, priimek, spol, datum rojstva, drzava, email, geslo datum registracije)
- Borza (ID borze, ime, vrsta, lokacija, povezava)
- Devizni tečaj (osnovna valuta, kotirajoča valuta, valutno razmerje, datum razmerja)
- Transakcija (ID transakcije, id uporabnika, id borze,  iz valute, v valuto, iz količine, v količino, datum in čas, tip naročila)
