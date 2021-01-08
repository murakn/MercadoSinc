from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from dbfread import DBF
from shutil import copyfile
import time
import pickle
from datetime import datetime
import os
import requests
import json

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument('--disable-gpu')
options.add_experimental_option('excludeSwitches', ['enable-logging'])

client_secret = "TnkpxGW9LnCbaYrnGvetdZ2lfj3udxjE"
client_id = "6545766642471155"
token_splash = "APP_USR-6545766642471155-010715-f3704c368d7e0109413cde129a2b8342-291850849"
refresh_splash = "TG-5ff5fe2dbb65270007f68b55-291850849"
token_abib = "APP_USR-6545766642471155-010718-3e83f765cb6e809ca7acf3c98f63018d-657456460"
refresh_abib = "TG-5ff752b1d56cb400066b95e8-657456460"
tempo = 180

def getqtd(file):
    qtd = {}
    esto = DBF(file, load = True)
    for i in esto.records:
        if int(i['QTDE']) < 0:
            continue
        if i['PROD'] not in qtd:
            qtd[i['PROD']] = int(i['QTDE'])
        else:
            if int(i['QTDE']) > qtd[i['PROD']]:
                qtd[i['PROD']] = int(i['QTDE'])
    return qtd

def modolist(ean, n, driver):
    t = 6
    driver.get("https://app.olist.com/")
    time.sleep(t)
    driver.find_element_by_id("email").send_keys("compras@grupoabib.com.br")
    pw = driver.find_element_by_id("password")
    pw.send_keys("FeViMa0406")
    pw.submit()
    driver.get("https://app.olist.com/stock/stock-and-price/")
    time.sleep(t)
    search = driver.find_element_by_id("id_search")
    time.sleep(t)
    search.send_keys(ean)
    time.sleep(t)
    search.submit()
    try:
        time.sleep(t)
        st = driver.find_element_by_name("stock")
        time.sleep(t)
        st.click()
        for x in range(15):
            st.send_keys(Keys.DELETE)
        time.sleep(t)
        st.send_keys(n)
        time.sleep(t)
        st.send_keys(Keys.ENTER)
        time.sleep(t)
    except Exception as e:
        print(e)

def modp(nml, n, token, reftoken, conta):
    if nml[0] == "#":
        nml = nml[1:]
    headers = {'Authorization':'Bearer '+token, "content-type": "application/json", "accept": "application/json"}
    arg = "{available_quantity: "+str(n)+"}"
    url = "https://api.mercadolibre.com/items/MLB"+nml
    r = requests.put(url, data = arg, headers = headers)
    a = json.loads(r.text)
    if r.status_code == 200:
        print(nml, "atualizado com sucesso.")
    elif r.status_code == 400 or r.status_code == 403:
        if a['error'] == "invalid_grant" or a['error'] == 'forbidden':
            ref = requests.post("https://api.mercadolibre.com/oauth/token?grant_type=refresh_token&client_id="+client_id+"&client_secret="+client_secret+"&refresh_token="+reftoken)
            resp = json.loads(ref.text)
            if conta == "s":
                token_splash = resp['access_token']
                refresh_splash = resp['refresh_token']
                modp(nml, n, token_splash, refresh_splash, 's')
            else:
                token_abib = resp['access_token']
                refresh_abib = resp['refresh_token']
                modp(nml, n, token_abib, refresh_abib, 'a')


def cic():
    qtd = getqtd("qtdloj.DBF")
    print('Esperando...('+datetime.now().strftime("%d/%m/%Y %H:%M:%S)"))
    time.sleep(tempo)
    qtd2 = getqtd("//Fxsorbase/acsn/CENTRAL/DADOS/qtdloj.DBF")
    dsplash = pickle.load(open("data_splash.pkl", "rb"))
    dabib = pickle.load(open("data_abib.pkl", "rb"))
    lista = []
    mciclo = []
    for i in qtd2:
        if i not in qtd:
            continue
        if qtd2[i] != qtd[i] and i not in mciclo:
            lista.append([i, qtd2[i]])
            mciclo.append(i)
    for i in lista:
        try:
            modp(dsplash[i[0]][1], int(i[1]), token_splash, refresh_splash, 's')
        except Exception as e:
            with open('erros.txt', 'a') as f:
                f.write(str(i[0])+": "+str(e))
            print(e)
        try:
            modp(dabib[i[0]][1], int(i[1]), token_abib, refresh_abib, 'a')
        except Exception as e:
            with open('erros.txt', 'a') as f:
                f.write(str(i[0])+": "+str(e))
            print(e)
        driver = webdriver.Chrome(options = options)
        try:
            modolist(i[0], int(i[1]), driver)
        except Exception as e:
            with open('erros.txt', 'a') as f:
                f.write(str(i[1])+": "+str(e))
            print(e)
        driver.close()
    if len(lista) > 0:
        copyfile("//Fxsorbase/acsn/CENTRAL/DADOS/qtdloj.DBF", os.getcwd()+ "/qtdloj.DBF")

if __name__ == "__main__":
    while True:
        try:
            cic()
        except Exception as e:
            print(e)
