#!/usr/bin/env python
# coding: utf-8



import requests


name = 'eluveitie'

lang = 'cs'
lang_strs = {
    'cs': {
        'band': 'kapela',
        'wikitemplate': 'Infobox - hudební umělec',
        'name': 'jméno',
        'genre': 'žánr',
        'origin': 'původ',
        'origin2': 'birth_place',
        'years': 'aktivní roky',
    },
}
strs = lang_strs[lang]
import wikipedia
wikipedia.set_lang(lang)




import re




import wikitextparser as wtp




import pycountry

import gettext
try:
    translate = gettext.translation('iso3166', pycountry.LOCALES_DIR, languages=[lang]).gettext
except:
    # NOOP (English is the original language, it doesn't have translation files)
    translate = str

def get_country_code(translated_country_name):
    return ''.join(
        [country.alpha_2 for country in pycountry.countries
         if translate(country.name).lower() == translated_country_name.lower()]
    ) or '??'




import urllib.parse




search = name + ' ' + strs['band']
page_title = wikipedia.search(search, 1)[0]




url = 'https://%s.wikipedia.org/w/api.php' % lang
params = {
            'action': 'query',
            'format': 'json',
            'prop': 'revisions',
            'formatversion': 2,
            'rvprop': 'content',
            'rvslots': '*',
            'titles': page_title,
        }
 
response = requests.get(url, params=params)
data = response.json()




content = data.get('query').get('pages')[0].get('revisions')[0].get('slots').get('main').get('content')









def untangle_template(wikitext):
    def template_mapper(template: wtp.Template):
        if template.normal_name() in {'dash', 'snd', 'spnd', 'sndash', 'spndash', 'spaced en dash'}:
            return ' –'  # &nbsp;&ndash;
        
        elif template.normal_name() in {'nowrap', 'hlist', 'Vlajka a název'}:
            # examples:
            #   {{hlist|[[Rock music|Rock]]|[[Pop music|pop]]|[[beat music|beat]]}}
            #   -> Rock, pop, beat
            #   {{nowrap|[[Christian metal]]}}
            #   -> Christian metal
            result = []
            for arg in template.arguments:
                result.append(arg.plain_text(replace_templates=template_mapper).lstrip('|').strip())
            return ', '.join(result)
        
        elif template.normal_name() in ('flatlist'):
            # examples:
            #   {{flatlist|
            #   * [[Metalcore]]
            #   * [[melodic metalcore]]
            #   }}
            #   -> Metalcore, melodic metalcore
            result = []
            for l in template.get_lists():
                for item in l.items:
                    result.append(wtp.parse(item).plain_text(replace_templates=template_mapper).strip())
            result = ', '.join(result)
            return result
        
        else:
            return ''  # remove other templates
    
    return wtp.parse(wikitext).plain_text(replace_templates=template_mapper).strip()

for template in [template for template in wtp.parse(content).templates if template.name.strip() == strs['wikitemplate']]:
    name = template.get_arg(strs['name'])
    name = wtp.parse(name.value).plain_text().strip() or page_title
    origin = template.get_arg(strs['origin']) or template.get_arg(strs['origin2'])
    origin = untangle_template(origin.value) or 'EMPTY'
    origin_country = origin.split(',')[-1].strip()
    # According to https://en.wikipedia.org/wiki/Template:Infobox_musical_artist#origin
    # > For "United States" and "United Kingdom", it is preferred that they be abbreviated "U.S." and "UK"
    if origin_country == 'U.S.':
        origin_country = 'United States'
    if origin_country == 'UK':
        origin_country = 'United Kingdom'
    if origin_country.lower() in ['england', 'wales', 'scotland', 'northern ireland']:
        # Workaround for https://github.com/flyingcircusio/pycountry/issues/94#issuecomment-1201863223
        origin_country = 'United Kingdom'
    try:
        origin_country_code = pycountry.countries.search_fuzzy(origin_country)[0].alpha_2
    except:
        origin_country_code = get_country_code(origin_country)
    genre = template.get_arg(strs['genre'])
    genre.value = re.sub('(\s*,\s*)?<br[^>]*>\s*', ', ', genre.value)
    genres = untangle_template(genre.value).replace(',', ' +').replace(';', ',')
    years = template.get_arg(strs['years'])
    first_year = min(map(int, re.findall(r'\b\d{4}\b', years.value)))
    url = 'https://%s.wikipedia.org/wiki/%s' % (lang, urllib.parse.quote(page_title))
    print('%s; %s/%s; %s; %s; %s' % (genres, origin_country_code, origin_country, first_year, name, url))




