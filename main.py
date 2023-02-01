import datetime
import hashlib
import os

import numpy as np
from flask import Flask, render_template, request
import pandas as pd
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='staticfiles')
UPLOAD_FOLDER = '.'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/', methods=["POST"])
def readfile():
    if request.method == 'POST':
        # file lists
        file1 = request.files.getlist("file1")[0]
        file2 = request.files.getlist("file2")[0]

        if file1 and file2:
            csv = pd.read_csv(file1, sep=";", encoding="latin-1")
            csv = csv[["Buchungstag", "Betrag"]]
            csv = csv.rename(columns={"Buchungstag": "Datum"})
            csv['Betrag'] = csv['Betrag'].str.replace(",", ".").astype(float)

            csv["Datum"] = csv["Datum"].apply(lambda x: datetime.datetime.strptime(x, "%d.%m.%y").strftime("%d.%m.%Y") if len(x) <= 8 else x)
            csv = csv.iloc[::-1]
            csv = csv.reset_index()
            csv = csv[["Datum", "Betrag"]]

            xl = pd.read_excel(file2, engine="openpyxl", header=1)
            xl = xl[["Datum", "Umsatz Soll", "Umsatz Haben"]]

            xl["Betrag"] = xl["Umsatz Haben"].apply(
                lambda x: x * -1 if pd.notna(x) and isinstance(x, (int, float)) else x)
            xl["Betrag"].fillna(xl["Umsatz Soll"], inplace=True)
            xl = xl.drop(["Umsatz Soll", "Umsatz Haben", ], axis=1)

            result_csv = csv.groupby('Datum').sum().to_dict()['Betrag']
            result_xl = xl.groupby("Datum").sum().to_dict()["Betrag"]

            #edge = pd.DataFrame(columns=["Datum", "Erwartet", "Tatsächlich"])
            bad = pd.DataFrame(columns=["Datum", "Bank", "Datev"])
            missmatch = pd.DataFrame(columns=["Datum", "Betrag"])

            big_name = "Datev"
            small_name = "Bank"
            bigger_dict = result_xl
            smaller_dict = result_csv
            if len(result_csv.keys()) > len(result_xl.keys()):
                big_name = "Bank"
                small_name = "Datev"
                bigger_dict = result_csv
                smaller_dict = result_xl

            for key, value in bigger_dict.items():
                if key in smaller_dict:
                    if smaller_dict[key] == value:
                        continue
                    elif round(smaller_dict[key], 0) == round(value, 0):
                        continue
                    else:
                        bad = bad.append({'Datum': key,big_name: value,small_name: smaller_dict[key]}, ignore_index=True)
                else:
                    missmatch = missmatch.append({'Datum': key,"Betrag": value}, ignore_index=True)

            return tables([bad.to_html(classes="table data-sticky-header r-flag", index=False),missmatch.to_html(classes="table data-sticky-header  g-flag", index=False)])
    return index()


@app.route('/table')
def tables(t):
    return render_template('./index.html',
                           tables=t,
                           titles=["Dringend"])


@app.route('/', methods=["GET"])
def index():
    return render_template('./index.html', tables=None)


if __name__ == '__main__':
    app.run(debug=False)
