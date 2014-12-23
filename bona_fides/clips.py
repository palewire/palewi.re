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
        description='A groundbreaking data analysis that uncovered deep-rooted problems in LA\'s 911 rescue service',
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
                name='Flawed data stall 911 upgrades',
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
        name="LAFD hiring controversy",
        description="A series of investigative reports that prompted an overhaul of how city firefighters are hired",
        app_list=[
            Clip(
                name="LAFD jobs gone in 60 seconds",
                url="http://www.latimes.com/local/la-me-lafd-hiring-20140227,0,5250682.story",
                image="lafd-lineup.jpeg",
                description="Only those who submitted key paperwork inside one minute considered, thousands eliminated"
            ),
            Clip(
                name="Nearly 25% of recruits related to firefighters",
                url="http://www.latimes.com/local/la-me-0228-lafd-recruit-20140228,0,1584181.story",
                image="lafd-training.jpeg",
                description="Of 70 hired, 13 are sons and 3 are nephews"
            ),
            Clip(
                name="Two L.A. fire commanders reassigned",
                url="http://www.latimes.com/local/la-me-0301-lafd-hiring-20140301,0,5887646.story",
                image="lafd-backs.jpeg",
                description="The two, who oversaw hiring and training, have sons who advanced in the recruiting process"
            ),
            Clip(
                name="Mayor suspends LAFD hiring",
                url="http://www.latimes.com/local/la-me-lafd-20140321,0,6241555.story",
                image="lafd-garcetti.jpeg",
                description="Move coincides with release of emails that show special workshops for relatives of LAFD insiders"
            ),
        ]
    ),
    ClipSet(
        name='L.A. elections, government and civic life',
        description='Data-driven coverage for and about the City of Angels',
        app_list=[
            Clip(
                name='The road to an election romp',
                url='http://www.latimes.com/news/local/la-me-winning-coalition-20130523,0,7639081.story',
                image='magicmap.png',
                description='A Times analysis lays out the winning strategy in L.A.\'s 2013 race for mayor'
            ),
            Clip(
                name='Forecast for mayor\'s race: Paltry turnout',
                url='http://www.latimes.com/news/local/la-me-mayor-turnout-20130515-big-dto,0,1068221.htmlstory',
                image='turnout.png',
                description='The next mayor is likely to garner fewer votes than any new mayor since the pre-freeway era, according to Times projection'
            ),
            Clip(
                name='Where does the Westside start?',
                url='http://maps.latimes.com/debates/westside/',
                image='westside.png',
                description='Is it a fixed place, with its own borders, customs and society, or only a state of mind?'
            ),
            Clip(
                name='L.A.\'s Eastside: Where do you draw the line?',
                url='http://maps.latimes.com/debates/eastside/',
                image='eastside.png',
                description='With no official definition, there\'s no official answer'
            ),
            Clip(
                name='Tax vote tells tale of two realities',
                url='http://www.latimes.com/news/local/la-me-tax-two-cities-20130309,0,1992530.story',
                image='measurea.jpg',
                description='Those in higher-crime areas supported proposal while affluent areas rejected it, according to Times analysis'
            ),
            Clip(
                name='LAPD map omits nearly 40% of crimes',
                url='http://articles.latimes.com/print/2009/jul/09/local/me-lapd-crimemap9',
                image='lapdmap.jpg',
                description='The public database doesn\'t include about 19,000 serious crimes reported in other LAPD data'
            ),
            Clip(
                name='Occupy L.A.: A portrait of arrested protesters',
                url='http://latimesblogs.latimes.com/lanow/2011/12/occupy-la-a-portrait-of-the-arrested-protesters.html',
                image='occupy.jpg',
                description='The nearly 300 protesters arrested near City Hall skewed young, white, male and local, a Times analysis found'
            ),
        ]
    ),
    ClipSet(
        name='State and federal government',
        description='Data analysis that developed new insights into how government works',
        app_list=[
            Clip(
                name='Hear No Evil, Smell No Evil',
                url='http://archive.fwweekly.com/content.asp?article=6967',
                image='txu.jpg',
                description='State regulators don\'t seem worried about lapses in reporting power-plant pollution identified by a CPI analysis'
            ),
            Clip(
                name='Nuclear power increasing through uprating',
                url='http://articles.latimes.com/print/2011/apr/17/local/la-me-uprates-20110418',
                image='uprates.jpg',
                description='Turning up the power is a little-publicized way of getting more electricity from existing nuclear plants, according a Times analysis'
            ),
            Clip(
                name='Clear Channel gives Tate talking points',
                url='http://benton.org/node/5487',
                image='tate.jpg',
                description='FCC commissioner received talking points against the proposed satellite radio merger'
            ),
            Clip(
                name='Pakistan\'s $4.7 billion \'blank check\'',
                url='http://www.publicintegrity.org/2007/05/22/5737/collateral-damage',
                image='pakistan.jpg',
                description='After 9/11, U.S. military funding to country soared with little oversight, according to CPI analysis'
            ),
            Clip(
                name='Half of high schools met U.S. goals',
                url='http://articles.latimes.com/print/2008/sep/05/local/me-scores5',
                image='highschool.jpg',
                description='The figure would have been even lower if the state hadn&rsquo;t used an easier measure than it does for lower grades',
            ),
            Clip(
                name='Federal loans go for risky business',
                url='http://www.columbiamissourian.com/stories/2005/12/27/federal-loans-go-for-risky-business',
                image='columbia.jpg',
                description='The high percentage of loans to Columbia bars and restaurants surpasses a national trend, according to Missourian analysis',
            ),
        ]
    ),
]
