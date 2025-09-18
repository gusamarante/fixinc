import pandas as pd
from dateutil.relativedelta import relativedelta
from urllib.error import HTTPError


TODAY = pd.to_datetime('today').normalize()


class SGS(object):
    """
    Wrapper for the Data API of the SGS (Sistema de Gerenciamento de Séries) of
    the Brazilian Central Bank.
    """

    def fetch(self, series_id):
        """
        Grabs series from the SGS

        Parameters
        ----------
        series_id: int, str, list of int, list of str or dict
            Series code on the SGS. If a dict is passed, the dict keys are used
            as series codes and the dict values are used as column names.
        """

        if type(series_id) is list:  # loop all series codes
            df = pd.DataFrame()

            for cod in series_id:
                single_series = self._fetch_single_code(cod)
                df = pd.concat([df, single_series], axis=1)

        elif type(series_id) is dict:
            df = pd.DataFrame()

            for cod in series_id.keys():
                single_series = self._fetch_single_code(cod)
                df = pd.concat([df, single_series], axis=1)

            df = df.rename(series_id, axis=1)

        else:
            df = self._fetch_single_code(series_id)

        df = df.sort_index()
        return df

    def _fetch_single_code(self, series_id):
        # These variable are going to loop to scrape the data.
        dt_end = TODAY
        dt_ini = dt_end - relativedelta(years=10)

        url = self._build_url(series_id, dt_ini, dt_end)
        df = pd.read_json(url)

        len_df = 10
        while len_df > 0:
            dt_end = dt_ini - pd.Timedelta(days=1)
            dt_ini = dt_end - relativedelta(years=10)

            url = self._build_url(series_id, dt_ini, dt_end)
            print(url)
            try:
                aux_df = pd.read_json(url)
            except HTTPError:
                break

            len_df = len(aux_df)
            print(len_df)
            df = pd.concat([df, aux_df], axis=0)

        df['data'] = pd.to_datetime(df['data'], dayfirst=True)
        df = df.set_index('data').sort_index()
        return df['valor'].rename(series_id)

    @staticmethod
    def _build_url(series_id, initial_date, end_date):
        return (f'http://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_id}/'
                f'dados?formato=json'
                f'&dataInicial={initial_date:%d/%m/%Y}'
                f'&dataFinal={end_date:%d/%m/%Y}')




