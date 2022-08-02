#!/usr/bin/env python
# coding: utf-8



import requests



import wikipedia
wikipedia.set_lang('cs')




import re




import wikitextparser as wtp




import pycountry

import gettext
translate = gettext.translation('iso3166', pycountry.LOCALES_DIR, languages=['cs']).gettext

def get_country_code(translated_country_name):
    return ''.join(
        [country.alpha_2 for country in pycountry.countries
         if translate(country.name).lower() == translated_country_name.lower()]
    ) or '??'




import urllib.parse




name = 'eluveitie'
search = name + ' kapela'
page_title = wikipedia.search(search, 1)[0]




url = 'https://cs.wikipedia.org/w/api.php'
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

#plain_text = wtp.parse(wikitext).plain_text(replace_templates=template_mapper)
# genre = template.get_arg('genre')
# plain_text = untangle_template(genre.value)
# print('result =', plain_text)  # "Salt – Pepper"




for template in [template for template in wtp.parse(content).templates if template.name.strip() == 'Infobox - hudební umělec']:
    name = template.get_arg('jméno')
    name = wtp.parse(name.value).plain_text().strip() or page_title
    origin = template.get_arg('původ')
    origin = untangle_template(origin.value) or 'EMPTY'
    origin_country = origin.split(',')[-1].strip()
    try:
        origin_country_code = pycountry.countries.search_fuzzy(origin_country)[0].alpha_2
    except:
        origin_country_code = get_country_code(origin_country)
    genre = template.get_arg('žánr')
    genre.value = re.sub('(\s*,\s*)?<br[^>]*>\s*', ', ', genre.value)
    genres = untangle_template(genre.value).replace(',', ' +').replace(';', ',')
    years = template.get_arg('aktivní roky')
    first_year = min(map(int, re.findall(r'\b\d{4}\b', years.value)))
    url = 'https://cs.wikipedia.org/wiki/%s' % urllib.parse.quote(page_title)
    print('%s; %s/%s; %s; %s; %s' % (genres, origin_country_code, origin_country, first_year, name, url))




# for template in [template for template in wtp.parse(content).templates if template.name.strip() == 'Infobox musical artist']:
#     name = template.get_arg('name')
#     name = wtp.parse(name.value).plain_text().strip()
#     origin = template.get_arg('origin') or template.get_arg('birth_place')
#     origin = wtp.parse(origin.value).plain_text().strip()
#     origin_country = origin.split(',')[-1].strip()
#     origin_country_code = pycountry.countries.search_fuzzy(origin_country)[0].alpha_2
#     genre = template.get_arg('genre')
#     print(genre)
#     genres = set()
#     genres.update([s.strip() for s in wtp.parse(genre.value).plain_text().strip().split(',')])
#     for tpl in wtp.parse(genre.value).templates:
#         if tpl.get_lists():
#             for l in tpl.get_lists():
#                 genres.update([s.strip(l.pattern).strip() for s in l.plain_text().splitlines()])
#         else:
#             genres.update([s.strip() for s in tpl.plain_text().split(',')])
#     print('GENRES', ' + '.join(genres))
#     years_active = template.get_arg('years_active')
#     first_year = min(map(int, re.findall(r'\b\d{4}\b', years_active.value)))
#     url = 'https://en.wikipedia.org/wiki/%s' % urllib.parse.quote(page_title)
#     print('%s, %s/%s, %s, %s, %s' % ('&'.join(genres), origin_country_code, origin_country, first_year, name, url))

