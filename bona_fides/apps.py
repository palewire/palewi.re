

class Application(object):
    """
    A piece of software that does something. Sometimes a website, sometimes not.
    """
    def __init__(self, *args, **kwargs):
        self.name = kwargs['name']
        self.url = kwargs['url']
        self.image = kwargs['image']
        self.description = kwargs['description']


class ApplicationSet(object):
    """
    A set of applications grouped together by a theme.
    """
    def __init__(self, *args, **kwargs):
        self.name = kwargs['name']
        self.description = kwargs['description']
        self.app_list = kwargs['app_list']


APP_LIST = [
    ApplicationSet(
        name='Los Angeles Times Data Desk',
        description='Maps, databases and visualizations published by our newsroom team',
        app_list=[
            Application(
                name='How fast is LAFD where you live?',
                url='http://graphics.latimes.com/how-fast-is-lafd/',
                image='lafdmap.jpg',
                description='How 911 response times stack up across L.A.'
            ),
            Application(
                name='L.A. mayoral election results',
                url='http://graphics.latimes.com/la-mayoral-maps/',
                image='mayoralmaps.png',
                description='Every ballot cast in the city since 2001'
            ),
            Application(
                name='Mapping L.A.: Neighborhoods',
                url='http://maps.latimes.com/neighborhoods/',
                image='mappingla.png',
                description='Stats, maps and data about more than 200 L.A. neighborhoods'
            ),
            Application(
                name='Mapping L.A.: Crime',
                url='http://maps.latimes.com/crime/',
                image='crimela.png',
                description='Analysis of the latest crime patterns and trends across L.A. County'
            ),
            Application(
                name='2012 Election Results',
                url='http://graphics.latimes.com/2012-election-results-national-map/',
                image='election2012.png',
                description='Returns for <a href="http://graphics.latimes.com/2012-election-gop-results-map-iowa/">state primaries</a> and the <a href="http://graphics.latimes.com/2012-election-results-national-map/">general election</a>, with a special focus on <a href="http://graphics.latimes.com/2012-election-results-california/">California</a>'
            ),
            Application(
                name='L.A. street quality grades',
                url='http://graphics.latimes.com/la-streets-map/',
                image='',
                description='Explore pavement quality ratings for each of the 68,000 street segments in LA'
            ),
            Application(
                name='California\'s War Dead',
                url='http://projects.latimes.com/wardead/',
                image='wardead.png',
                description='Stories about California servicemembers who died during the wars in Iraq and Afghanistan'
            ),
            Application(
                name='Hollywood Star Walk',
                url='http://projects.latimes.com/hollywood/star-walk/',
                image='starwalk.png',
                description='A virtual tour of the 2,500 stars on the Walk of Fame'
            ),
            Application(
                name='California Schools Guide',
                url='http://schools.latimes.com/',
                image='',
                description='Test scores, demographics and comments about California\'s schools'
            ),
            Application(
                name='DWP salaries database',
                url='http://salaries.latimes.com/dwp/',
                image='',
                description='An interactive database reporting the pay of each of the department\'s employees'
            ),
            Application(
                name='boundaries.latimes.com',
                url='http://boundaries.latimes.com',
                image='',
                description='A website and API that allows anyone to quickly browse, download and reuse dozens of different maps'
            ),
            Application(
                name='documents.latimes.com',
                url='http://documents.latimes.com',
                image='documents.png',
                description='A CMS for publishing tens of thousands of pages via DocumentCloud'
            ),
            Application(
                name='timelines.latimes.com',
                url='http://timelines.latimes.com/',
                image='timelines.jpg',
                description='A CMS for quickly publishing interactive timelines using a redesigned <a href="http://propublica.github.com/timeline-setter/">TimelineSetter</a>'
            ),
            Application(
                name='spreadsheets.latimes.com',
                url='http://spreadsheets.latimes.com',
                image='spreadsheets.png',
                description='A CMS for publishing interactive tables, and doing it on deadline.'
            ),
            Application(
                name='Billions to Spend',
                url='http://laccd.latimes.com',
                image='',
                description='The political money behind the rebuilding of the L.A. Community College District'
            ),
            Application(
                name='datadesk.latimes.com',
                url='http://datadesk.latimes.com',
                image='',
                description='A blog to showcase our team\'s work'
            ),
        ]
    ),
    ApplicationSet(
        name='PastPages',
        description='A crowd-funded, open-source website that archives dozens of news hompages each hour',
        app_list=[
            Application(
                name='pastpages.org',
                url='http://www.pastpages.org',
                image='pastpages.png',
                description='The archive captures the shifting homepages of major media sites'
            ),
            Application(
                name='github.com/pastpages',
                url='https://github.com/pastpages/pastpages.org',
                image='',
                description='The open-source code that powers the site'
            ),
            Application(
                name='The PastPages API',
                url='http://www.pastpages.org/api/docs/',
                image='',
                description='A machine-readable version for programmers to access the archive\'s database'
            ),
            Application(
                name='pastpages2gif',
                url='https://github.com/pastpages/pastpages2gif',
                image='',
                description='A tool to create animated GIFs from the homepage archive'
            ),
        ]
    ),
    ApplicationSet(
        name='Open-source software',
        description='Free and open code projects that I\'ve developed or contributed to',
        app_list=[
            Application(
                name='python-elections',
                url='http://datadesk.github.io/python-elections/',
                image='pythonelections.jpg',
                description='A Python wrapper for AP\'s election data service'
            ),
            Application(
                name='django-bakery',
                url='http://datadesk.latimes.com/posts/2012/03/introducing-django-bakery/',
                image='bakery.png',
                description='A set of helpers for baking out a Django site as flat files'
            ),
            Application(
                name='jquery-geocodify',
                url='http://datadesk.github.io/jquery-geocodify/',
                image='geocodify.png',
                description='A jQuery plug-in that provides autocomplete for address searches'
            ),
            Application(
                name='calculate',
                url='http://datadesk.github.io/latimes-calculate/',
                image='calculate.png',
                description='A collection of simple math functions useful for doing journalism'
            ),
            Application(
                name='python-documentcloud',
                url='http://datadesk.github.io/python-documentcloud/',
                image='doccloud.png',
                description='A simple Python wrapper for the DocumentCloud API'
            ),
            Application(
                name='python-lametro-api',
                url='http://datadesk.github.io/python-lametro-api/',
                image='metroapi.png',
                description='A simple Python wrapper for LA Metro\'s API for bus stops, routes and vehicles'
            ),
            Application(
                name='Quiet L.A.',
                url='http://datadesk.latimes.com/posts/2012/11/introducing-quiet-la/',
                image='quietla.png',
                description='A muted base map for overlaying loud data visualizations'
            ),
            Application(
                name='Silent L.A.',
                url='http://datadesk.latimes.com/posts/2013/02/introducing-silent-la/',
                image='mayoralmaps.png',
                description='A black base map for overlaying bright data visualizations'
            ),
            Application(
                name='django-softhyphen',
                url='http://datadesk.latimes.com/posts/2011/12/django-softhyphen/',
                image='softhyphen.png',
                description='Automates the hyphenation of text, allowing easy formatting of HTML in more bookish style'
            ),
            Application(
                name='django-yamlfield',
                url='https://github.com/datadesk/django-yamlfield',
                image='yamlfield.png',
                description='A Django database field for storing YAML data'
            ),
            Application(
                name='python-googlegeocoder',
                url='https://github.com/datadesk/python-googlegeocoder',
                image='googlegeocoder.png',
                description='A simple Python wrapper for version three of Google\'s geocoder API'
            ),
            Application(
                name='latimes-statestyle',
                url='https://github.com/datadesk/latimes-statestyle',
                image='statestyle.gif',
                description='A Python library that standardizes U.S. state names'
            ),
            Application(
                name='django-greeking',
                url='https://github.com/palewire/django-greeking',
                image='greeking.jpg',
                description='Tools for printing filler text in your Django templates, a technique from the days of hot type known as greeking'
            ),
            Application(
                name='appengine-template',
                url='https://github.com/datadesk/latimes-appengine-template',
                image='appengine.png',
                description='Bootstrap a Google App Engine project with Django and other goodies'
            ),
            Application(
                name='django-project-template',
                url='https://github.com/datadesk/django-project-template',
                image='',
                description='A custom template for initializing a new Django project the Data Desk way'
            ),
            Application(
                name='django-boundaryservice',
                url='https://github.com/datadesk/django-boundaryservice',
                image='',
                description='A series of fixes and features for the Chicago Tribune\'s map API framework'
            ),
            Application(
                name='uptime-grove',
                url='https://github.com/datadesk/uptime-grove',
                image='',
                description='A nodejs plugin for Uptime that sends notifications to the Grove.io IRC service.'
            ),
            Application(
                name='Leaflet for Mapstraction',
                url='https://github.com/mapstraction/mxn',
                image='',
                description='Added support for Leaflet to the Mapstraction framework'
            ),
            Application(
                name='Leaflet',
                url='https://github.com/Leaflet/Leaflet/commits?author=palewire',
                image='',
                description='Added linejoin and linecap support to the JavaScript mapping library'
            ),
        ]
    ),
    ApplicationSet(
        name='WXWTF',
        description='We are the INTERNET. We are NOTHING. We are EVERYTHING. We are ERRBODY OUT HERE.',
        app_list=[
            Application(
                name='Questionheds',
                url='https://twitter.com/#!/questionheds/',
                image='questionheds.png',
                description='Is it news?'
            ),
            Application(
                name='copyboy',
                url='https://github.com/datadesk/copyboy',
                image='copyboy.png',
                description='A fork of GitHub\'s Campfire bot for IRC, aware of all Internet traditions'
            ),
            Application(
                name='BRING THE NEWS BACK!',
                url='/apps/bring-the-news-back/',
                image='bringthenewsback.png',
                description='Excellence in art / We must preserve that'
            ),
            Application(
                name='Kennedy Name Generator',
                url='/kennedy/',
                image='kennedy.png',
                description='Find your place in the Democratic Party\'s royal family'
            ),
            Application(
                name='iesaysno.com',
                url='http://www.iesaysno.com',
                image='iesaysno.png',
                description='For those special moments of denial, known to every web developer'
            ),
            Application(
                name='whogetsthegasface.com',
                url='http://www.whogetsthegasface.com',
                image='whogetsthegasface.png',
                description='<b>gasface, the</b> <i>noun</i> a stupid face directed towards someone you don\'t like'
            ),
            Application(
                name='Return of the Mack: The Ringtone',
                url='/mack/?autoplay',
                image='mack.png',
                description='You lied to me!'
            ),
            Application(
                name='Candy says',
                url='/candysays/',
                image='',
                description='She\'s not an anchor, she just crush a lot'
            ),
        ]
    ),
#    Application(
#        name='',
#        url='',
#        image='',
#        description=''
#    ),
]


