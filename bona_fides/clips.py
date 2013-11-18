class Clip(object):
    """
    A news story I worked on
    """
    def __init__(self, *args, **kwargs):
        self.name = kwargs['name']
        self.url = kwargs['url']
        self.image = kwargs['image']
        self.description = kwargs['description']


class ClipSet(object):
    """
    A set of clips grouped together by a theme.
    """
    def __init__(self, *args, **kwargs):
        self.name = kwargs['name']
        self.description = kwargs['description']
        self.app_list = kwargs['app_list']


CLIP_LIST = [
    ClipSet(
        name='Life on the line: 911 breakdowns at LAFD',
        description='An investigative series driven by groundbreaking data analysis that uncovered deep-rooted problems in a safety net millions of Angelenos rely on when they dial 911',
        app_list=[
            Clip(
                name='Dispatch lag slows call response',
                url='http://www.latimes.com/news/local/lafddata/la-me-fire-response-20120518,0,5314236.story',
                image='lafd-dispatch-lag.jpeg',
                description='Operators on average take far longer than the national standard to send rescuers, a Times analysis shows'
            ),
            Clip(
                name='Boundaries hold up 911 response',
                url='http://www.latimes.com/news/local/lafddata/la-me-lafd-aid-20121021,0,7787277.story',
                image='lafd-borders.jpeg',
                description='Dispatchers rarely reach across jurisdictional lines, even when outside help is closer, according to a Times analysis'
            ),
            Clip(
                name='Dispatchers waste time prompting CPR',
                url='http://www.latimes.com/news/local/lafddata/la-me-fire-report-20120914,0,5129089.story',
                image='lafd-cpr.jpeg',
                description='Valuable time is routinely lost before 911 callers start CPR, according to study obtained by The Times'
            ),
            Clip(
                name='Response lags in pricey neighborhoods',
                url='http://www.latimes.com/news/local/lafddata/la-me-lafd-response-disparities-20121115,0,7435489.story',
                image='lafd-disparities.jpeg',
                description='A Times investigation finds wide geographic disparities in how quickly LAFD rescuers deliver aid'
            ),
            Clip(
                name='Flawed data stall California\'s 911 upgrades',
                url='http://www.latimes.com/news/local/lafddata/la-me-ems-data-problems-20121222,0,6217938.story',
                image='lafd-data.jpeg',
                description='Poor record-keeping stymies state effort to improve emergency responses, a Times investigation found'
            ),
            Clip(
                name='New mayor replaces LAFD chief',
                url='http://www.latimes.com/local/la-me-1011-lafd-chief-20131011,0,4972575,full.story',
                image='lafd-cummings.jpeg',
                description='In the wake of our reporting the city instituted a series of reforms, capped by the replacement of the fire chief'
            ),
        ]
    ),
    ClipSet(
        name='California and Los Angeles',
        description='A selection of data-driven coverage for and about the Golden State and its City of Angels',
        app_list=[
            Clip(
                name='',
                url='',
                image='',
                description=''
            ),
            Clip(
                name='',
                url='',
                image='',
                description=''
            ),
            Clip(
                name='',
                url='',
                image='',
                description=''
            ),
            Clip(
                name='',
                url='',
                image='',
                description=''
            ),
        ]
    ),
    ClipSet(
        name='Federal government regulation',
        description='Investigative stories that use data to develop new insights into the policies of the U.S. government',
        app_list=[
            Clip(
                name='',
                url='',
                image='',
                description=''
            ),
            Clip(
                name='',
                url='',
                image='',
                description=''
            ),
            Clip(
                name='',
                url='',
                image='',
                description=''
            ),
            Clip(
                name='',
                url='',
                image='',
                description=''
            ),
        ]
    ),
]
