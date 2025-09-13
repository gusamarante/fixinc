from pandas.tseries.holiday import (
    AbstractHolidayCalendar,
    Holiday,
    nearest_workday,
    USMartinLutherKingJr,
    USPresidentsDay,
    GoodFriday,
    USMemorialDay,
    USLaborDay,
    USThanksgivingDay,
    Easter,
    Day,
)

# Holidays not in pandas
NewYear = Holiday("New Year's Day", month=1, day=1, observance=nearest_workday)
Christmas = Holiday("Christmas Day", month=12, day=25, observance=nearest_workday)

BRCarnavalSeg  = Holiday("Segunda de Carnaval",  month=1, day=1, offset=[Easter(), Day(-48)])
BRCarnavalTer = Holiday("Terça de Carnaval", month=1, day=1, offset=[Easter(), Day(-47)])
BRTiradentes = Holiday("Tiradentes", month=4, day=21, start_date="1965-04-20", observance=nearest_workday)
BRDiaDoTrabalho = Holiday("Dia do Trabalho", month=5, day=1, start_date="1925-04-30", observance=nearest_workday)
BRCorpusChristi = Holiday("Corpus Christi", month=1, day=1, offset=[Easter(), Day(60)])
BRIndependencia = Holiday("Independência do Brasil", month=9, day=7, start_date="1822-09-06", observance=nearest_workday)
BRNossaSenhoraAparecida = Holiday("Nossa Senhora Aparecida", month=10, day=12, start_date="1980-10-11", observance=nearest_workday)
BRFinados = Holiday("Finados", month=11, day=2, start_date="1966-11-01", observance=nearest_workday)
BRRepublica = Holiday("Proclamação da República", month=11, day=15, start_date="1890-11-14", observance=nearest_workday)
BRConscienciaNegra = Holiday("Consciência Negra", month=11, day=20, start_date="2024-11-19", observance=nearest_workday)  # In São Paulo first, national from 2024

USJuneteenth = Holiday("Juneteenth National Independence Day", month=6, day=19, start_date="2021-06-18", observance=nearest_workday)
USIndependenceDay = Holiday("Independence Day", month=7, day=4, observance=nearest_workday)



class ANBIMA(AbstractHolidayCalendar):
    rules = [
        NewYear,
        BRCarnavalSeg,
        BRCarnavalTer,
        GoodFriday,
        BRTiradentes,
        BRDiaDoTrabalho,
        BRCorpusChristi,
        BRIndependencia,
        BRNossaSenhoraAparecida,
        BRFinados,
        BRRepublica,
        BRConscienciaNegra,
        Christmas,
    ]


class USTrading(AbstractHolidayCalendar):
    rules = [
        NewYear,
        USMartinLutherKingJr,
        USPresidentsDay,
        GoodFriday,
        USMemorialDay,
        USJuneteenth,
        USIndependenceDay,
        USLaborDay,
        USThanksgivingDay,
        Christmas,
    ]
