#!/usr/bin/env python
# coding: utf-8



import requests


name = 'gutalax'

lang = 'de'
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
    'de': {
        'band': 'band',
        'wikitemplate': 'Infobox Band',
        'name': 'Name',
        'genre': 'Genre',
        'origin': 'Herkunft',
        'origin2': 'birth_place',
        'years': 'Gründung',
    },
    'en': {
        'band': 'band',
        'wikitemplate': 'Infobox musical artist',
        'name': 'name',
        'genre': 'genre',
        'origin': 'origin',
        'origin2': 'birth_place',
        'years': 'years_active',
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



def find_article_name(search_string):
    search = search_string + ' ' + strs['band']
    page_title = wikipedia.search(search, 1)[0]
    return page_title



def get_article_wikitext(lang, article_title):
    url = 'https://%s.wikipedia.org/w/api.php' % lang
    params = {
                'action': 'query',
                'format': 'json',
                'prop': 'revisions',
                'formatversion': 2,
                'rvprop': 'content',
                'rvslots': '*',
                'titles': article_title,
            }
     
    response = requests.get(url, params=params)
    data = response.json()
    content = data.get('query').get('pages')[0].get('revisions')[0].get('slots').get('main').get('content')
    return content






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

def extract_infos(article_title, wikitext):
    for template in [template for template in wtp.parse(wikitext).templates if template.name.strip() == strs['wikitemplate']]:
        name = template.get_arg(strs['name'])
        name = untangle_template(name.value) or article_title

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

        url = 'https://%s.wikipedia.org/wiki/%s' % (lang, urllib.parse.quote(article_title))

        return {
                    'name': name,
                    'url': url,
                    'genres': genres,
                    'country': origin_country,
                    'country_code': origin_country_code,
                    'year': first_year,
                }





article_title = find_article_name(name)
wikitext = get_article_wikitext(lang, article_title)
infos = extract_infos(article_title, wikitext)

print('%s; %s/%s; %s; %s; %s' % (infos['genres'], infos['country_code'], infos['country'], infos['year'], infos['name'], infos['url']))
