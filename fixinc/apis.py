from urllib.error import HTTPError

import pandas as pd
import requests
from dateutil.relativedelta import relativedelta


TODAY = pd.to_datetime('today').normalize()


class SGS(object):
    """
    Wrapper for the Data API of the SGS (Sistema de Gerenciamento de Séries) of
    the Brazilian Central Bank.
    """

    def fetch(self, series_id, start_date=None):
        # TODO add start and end dates to speed things up
        # TODO fallback with offline data?
        """
        Grabs series from the SGS

        Parameters
        ----------
        series_id: int, str, list of int, list of str or dict
            Series code on the SGS. If a dict is passed, the dict keys are used
            as series codes and the dict values are used as column names.

        start_date: date-like
            Starting date of the series. If the date is too far back in the
            past, the scraping will take longer as there is a cap on the SGS.
            Shorter series return faster.
        """

        if type(series_id) is list:  # loop all series codes
            df = pd.DataFrame()

            for cod in series_id:
                single_series = self._fetch_single_code(cod, start_date)
                df = pd.concat([df, single_series], axis=1)

        elif type(series_id) is dict:
            df = pd.DataFrame()

            for cod in series_id.keys():
                single_series = self._fetch_single_code(cod, start_date)
                df = pd.concat([df, single_series], axis=1)

            df = df.rename(series_id, axis=1)

        else:
            df = self._fetch_single_code(series_id, start_date)

        df = df.sort_index()
        return df

    def _fetch_single_code(self, series_id, start_date):
        # These variable are going to loop to scrape the data.
        dt_end = TODAY

        if start_date is None:
            dt_ini = dt_end - relativedelta(years=10)
            start_date = dt_ini
        else:
            dt_ini = max(
                pd.to_datetime(start_date),
                dt_end - relativedelta(years=10),
            )

        url = self._build_url(series_id, dt_ini, dt_end)
        df = pd.read_json(url)

        len_df = 10
        while len_df > 0:
            dt_end = dt_ini - pd.Timedelta(days=1)
            dt_ini = dt_end - relativedelta(years=10)

            url = self._build_url(series_id, dt_ini, dt_end)
            try:
                aux_df = pd.read_json(url)
            except HTTPError:
                break

            len_df = len(aux_df)
            df = pd.concat([df, aux_df], axis=0)

            if pd.to_datetime(df["data"], dayfirst=True).min() <= pd.to_datetime(start_date):
                break

        df['data'] = pd.to_datetime(df['data'], dayfirst=True)
        df = df.set_index('data').sort_index()
        return df['valor'].rename(series_id)

    @staticmethod
    def _build_url(series_id, initial_date, end_date):
        return (f'http://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_id}/'
                f'dados?formato=json'
                f'&dataInicial={initial_date:%d/%m/%Y}'
                f'&dataFinal={end_date:%d/%m/%Y}')


class BCBFocusScraper:
    """
    BCB Focus API
    https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/aplicacao#!/recursos

    Consultas manuais
    https://www3.bcb.gov.br/expectativas2/#/consultas
    """
    bcb_tables = {
        "anual": {
            "url": "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/ExpectativasMercadoAnuais?$format=json",
            "available_indicators": [
                "Dívida bruta do governo geral",
                "Dívida líquida do setor público",
                "Resultado primário",
                "Resultado nominal",
                "PIB Total",
                "PIB Agropecuária",
                "PIB Indústria",
                "PIB Serviços",
                "PIB Despesa de consumo das famílias",
                "PIB Despesa de consumo da administração pública",
                "PIB Formação Bruta de Capital Fixo",
                "PIB Exportação de bens e serviços",
                "PIB Importação de bens e serviços",
                'Taxa de desocupação',
                "Selic",
                "Câmbio",
                'IPCA',
                'IPCA Livres',
                'IPCA Serviços',
                'IPCA Bens industrializados',
                'IPCA Alimentação no domicílio',
                'IPCA Administrados',
                'IGP-M',
            ],
        },
        "mensal": {
            "url": "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/ExpectativaMercadoMensais?$format=json",
            "available_indicators": [
                'IPCA',
                'IPCA Livres',
                'IPCA Serviços',
                'IPCA Bens industrializados',
                'IPCA Alimentação no domicílio',
                'IPCA Administrados',
                'IGP-M',
                'Câmbio',
                'Taxa de desocupação',
            ],
        },
        "trimestral": {
            "url": "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/ExpectativasMercadoTrimestrais?$format=json",
            "available_indicators": [
                'IPCA',
                'IPCA Livres',
                'IPCA Serviços',
                'IPCA Bens industrializados',
                'IPCA Alimentação no domicílio',
                'IPCA Administrados',
                'Câmbio',
                "PIB Total",
                'Taxa de desocupação',
            ],
        },
        "selic": {
            "url": "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/ExpectativasMercadoSelic?$format=json",
            "available_indicators": ['Selic'],
        },
    }
    rename_cols = {
        'Indicador': "indicator",
        'Data': "date",
        'DataReferencia': "prediction_scope",
        'Reuniao': "prediction_scope",
        'Media': "mean",
        'Mediana': "median",
        'DesvioPadrao': "stdev",
        'Minimo': "minimum",
        'Maximo': "maximum",
        'numeroRespondentes': "number_answers",
        'baseCalculo': "survey_type",
        'IndicadorDetalhe': "",
    }
    table_name = 'bcbfocus'
    id_vars = ["date", "indicator", "prediction_scope", "survey_type"]
    value_vars = [
        "mean",
        "median",
        "stdev",
        "minimum",
        "maximum",
        "number_answers",
    ]
    max_items = 10000

    def run_scraper(self, bcb_table, indicator, start_date):
        """
        Scrapes the BCB Focus API for a single indicator. The date range is
        covered by the `max_itens` parameter, as I could not find out how to
        filter ranges of dates through the API.

        Parameters
        ----------
        bcb_table: str
            Name of the table to fetch from. Available tables and indicators are
            described in the `bcb_tables` attribute of the class.

        indicator: str
            Which indicator to fetch. Indicator must be available for the
            required `bcb_table`. Available tables and indicators are described
            in the `bcb_tables` attribute of the class. If this is passed,
            start_date should be None.

        start_date: date-like
            Starting date filter. If this is passed, indicator should be None.
        """
        assert bcb_table in list(self.bcb_tables.keys())
        assert indicator in self.bcb_tables[bcb_table]["available_indicators"]

        last_date = pd.to_datetime(start_date)
        new_date = last_date + pd.tseries.offsets.Day(1)

        df = []
        while new_date > last_date:
            aux_df = self._scrape_single(indicator, bcb_table, last_date, self.max_items)
            df.append(aux_df)
            last_date = new_date
            new_date = aux_df["Data"].max()

        df = pd.concat(df, axis=0)
        df = df.drop_duplicates(keep="last")
        df = df.drop("IndicadorDetalhe", axis=1, errors='ignore')
        df = df.rename(self.rename_cols, axis=1)

        # Only keep indicators we keep track of
        df = df[df['indicator'].isin(self.bcb_tables[bcb_table]["available_indicators"])]

        # Organize in friendly format
        df = df.melt(
            id_vars=self.id_vars, value_vars=self.value_vars, var_name="metric"
        )
        df["frequency"] = bcb_table
        df['date'] = pd.to_datetime(df['date'])

        return df

    def _scrape_single(self, indicator, bcb_table, start_date, max_itens):
        # https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/ExpectativasMercadoAnuais?$format=json&$filter=Indicador eq 'IPCA' and Data gt '2007-01-01'&$top=100&$orderby=Data asc

        table = self.bcb_tables[bcb_table]['url']
        indsd = f"&$filter=Indicador eq '{indicator}' and Data gt '{start_date: %Y-%m-%d}'"
        top = f"&$top={max_itens}"

        url = f"{table}{indsd}{top}&$orderby=Data asc"

        res = requests.get(url)
        res = res.json()
        res = res["value"]
        df = pd.DataFrame(res)

        if 'Data' in df.columns:
            df["Data"] = pd.to_datetime(df["Data"])

        return df
