import numpy
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

            csv["Datum"] = csv["Datum"].apply(
                lambda x: datetime.datetime.strptime(x, "%d.%m.%y").strftime("%d.%m.%Y") if len(x) <= 8 else x)
            csv = csv.iloc[::-1]
            csv = csv.reset_index()
            csv = csv[["Datum", "Betrag"]]
            csv['Datum'] = pd.to_datetime(csv['Datum'], format='%d.%m.%Y', dayfirst=True)
            csv = csv.sort_values(by='Datum')

            # Soll und Haben zusammenfuehren zu "Betrag"
            xl["Betrag"] = xl["Umsatz Haben"].apply(
                lambda x: x * -1 if pd.notna(x) and isinstance(x, (int, float)) else x)
            xl["Betrag"].fillna(xl["Umsatz Soll"], inplace=True)
            xl = xl.drop(["Umsatz Soll", "Umsatz Haben", ], axis=1)
            xl['Datum'] = pd.to_datetime(xl['Datum'], format='%d.%m.%Y', dayfirst=True)
            xl = xl.sort_values(by='Datum')

            # Betraege Summieren fuer jedes Datum
            result_csv = csv.groupby("Datum").sum().to_dict()['Betrag']
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
                        invalid = invalid.append(
                            {'Datum': key, "Datev": round(value, 2), "Bank": round(result_csv[key], 2)},
                            ignore_index=True)
                else:
                    missing = missing.append({'Datum': key, "Betrag": round(value, 2)}, ignore_index=True)

            invalid = invalid.sort_values(by='Datum')
            missing = missing.sort_values(by='Datum')

            csv_filtered = csv[csv['Datum'].isin(invalid['Datum'])]
            xl_filtered = xl[xl['Datum'].isin(invalid['Datum'])]
            csv_filtered = csv_filtered.reset_index(drop=True)
            xl_filtered = xl_filtered.reset_index(drop=True)
            # merge the dataframes

            # combine date and amount as a single key
            xl_filtered['key'] = xl_filtered['Datum'].astype(str) + xl_filtered['Betrag'].astype(str)
            csv_filtered['key'] = csv_filtered['Datum'].astype(str) + csv_filtered['Betrag'].astype(str)

            # find the keys that match between the two tables
            matching_keys = set(xl_filtered['key']) & set(csv_filtered['key'])

            # find the indices of the matching keys in each table
            match_indices_1 = [i for i, key in enumerate(xl_filtered['key']) if key in matching_keys]
            match_indices_2 = [i for i, key in enumerate(csv_filtered['key']) if key in matching_keys]

            # delete the rows with matching keys from both tables
            xl_filtered = xl_filtered.drop(match_indices_1)
            csv_filtered = csv_filtered.drop(match_indices_2)

            # find the keys with no matches
            non_matching_keys = set(xl_filtered['key']) ^ set(csv_filtered['key'])

            # create a list of rows with no matches
            no_matches = pd.DataFrame(columns=['Datum', 'Betrag'])
            for key in non_matching_keys:
                if key in set(xl_filtered['key']):
                    no_matches = no_matches.append(
                        xl_filtered.loc[xl_filtered['key'] == key][['Datum', 'Betrag']].iloc[0])
                else:
                    no_matches = no_matches.append(
                        csv_filtered.loc[csv_filtered['key'] == key][['Datum', 'Betrag']].iloc[0])

            no_matches['Datum'] = pd.to_datetime(no_matches['Datum'], format='%d-%m-%Y')
            no_matches = no_matches.sort_values(by='Datum')

            # reset the index of no_matches
            no_matches = no_matches.reset_index(drop=True)

            # just debug for pandas
            # pd.set_option('display.max_rows', None)
            # pd.set_option('display.max_columns', None)
            # pd.set_option('display.width', None)
            # pd.set_option('display.max_colwidth', -1)

            invalid["Differenz"] = round(abs(invalid["Bank"] - invalid["Datev"]), 2)

            no_matches["Datum"] = no_matches["Datum"].dt.strftime('%d-%m-%Y')
            invalid["Datum"] = invalid["Datum"].dt.strftime('%d-%m-%Y')
            missing["Datum"] = missing["Datum"].dt.strftime('%d-%m-%Y')

            # turn dataframes into dictonaries
            invalid_dict, missing_dict, no_matches_dict = invalid.to_dict(), missing.to_dict(), no_matches.to_dict(
                'split')

            return tables([invalid_dict, missing_dict, no_matches_dict])

    return index(err="Bitte wählen Sie mindestens 2 Dateien aus.")


@app.route('/table')
def tables(t):
    return render_template('./index.html', tables=t)


@app.route('/', methods=["GET"])
def index(err=None):
    return render_template('./index.html', tables=None, err=err)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port="80", debug=False)
