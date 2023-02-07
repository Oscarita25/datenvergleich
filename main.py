from flask import Flask, render_template, request
import pandas as pd
import datetime


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
            try:
                # Dateien einlesen
                csv = pd.read_csv(file1, sep=";", encoding="latin-1")
                xl = pd.read_excel(file2, engine="openpyxl", header=1)
            except Exception as e:
                return index(err=str(e))

            # Zellen aus den Dateien auswaehlen
            csv = csv[["Buchungstag", "Betrag"]]
            xl = xl[["Datum", "Umsatz Soll", "Umsatz Haben"]]

            # Dateinamen und Datenformatierung beheben
            csv = csv.rename(columns={"Buchungstag": "Datum"})
            csv['Betrag'] = csv['Betrag'].str.replace(",", ".").astype(float)

            csv["Datum"] = csv["Datum"].apply(lambda x: datetime.datetime.strptime(x, "%d.%m.%y").strftime("%d.%m.%Y") if len(x) <= 8 else x)
            csv = csv.iloc[::-1]
            csv = csv.reset_index()
            csv = csv[["Datum", "Betrag"]]

            # Soll und Haben zusammenfuehren zu "Betrag"
            xl["Betrag"] = xl["Umsatz Haben"].apply(lambda x: x * -1 if pd.notna(x) and isinstance(x, (int, float)) else x)
            xl["Betrag"].fillna(xl["Umsatz Soll"], inplace=True)
            xl = xl.drop(["Umsatz Soll", "Umsatz Haben", ], axis=1)

            # Betraege Summieren fuer jedes Datum
            result_csv = csv.groupby('Datum').sum().to_dict()['Betrag']
            result_xl = xl.groupby("Datum").sum().to_dict()["Betrag"]

            # 2 Tabellen erstellen fuer ungueltige und fehlende Datenpaare
            invalid = pd.DataFrame(columns=["Datum", "Bank", "Datev"])
            missing = pd.DataFrame(columns=["Datum", "Betrag"])

            # vergleichen der datenpaare
            for key, value in result_xl.items():
                if key in result_csv:
                    if result_csv[key] == value:
                        continue
                    elif round(result_csv[key], 0) == round(value, 0):
                        continue
                    else:
                        invalid = invalid.append({'Datum': key,"Datev": value,"Bank": result_csv[key]}, ignore_index=True)
                else:
                    missing = missing.append({'Datum': key, "Betrag": value}, ignore_index=True)

            return tables([invalid.to_html(classes="table data-sticky-header r-flag", index=False), missing.to_html(classes="table data-sticky-header  g-flag", index=False)])

    return index(err="Bitte wählen Sie mindestens 2 Dateien aus.")


@app.route('/table')
def tables(t):
    return render_template('./index.html', tables=t)


@app.route('/', methods=["GET"])
def index(err=None):
    return render_template('./index.html', tables=None, err=err)


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=False)
