#!/usr/bin/env python3
"""Strict one-off maintenance for two VERIFIED Blue Sea Pages.

Default mode is dry-run. Uses WordPress's Trash, never force-deletes content,
files, users, or project records. Does not change Astro build/cache pipelines.
"""
import argparse
import html
from html.parser import HTMLParser
import http.cookiejar
import json
import os
from urllib.parse import urlencode, urljoin, urlparse, parse_qs
from urllib.request import Request, build_opener, HTTPCookieProcessor, urlopen
from urllib.error import HTTPError

BASE = 'https://api-nghiencuukhoahoc.webnvn.com'
TARGETS = {
    53390: ('ve-chung-toi', 'about'),
    47222: ('lien-he', 'contact'),
}

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            u = dict(attrs).get('href', '')
            if u:
                self.urls.append(html.unescape(u))

def public_page(pid):
    uri = BASE + '/wp-json/wp/v2/pages/' + str(pid) + '?_fields=id,slug,status,acf,title,content'
    with urlopen(Request(uri, headers={'Accept':'application/json'}),timeout=25) as r:
        return json.load(r)

def verify_sources():
    for pid,(slug,key) in TARGETS.items():
        data = public_page(pid)
        body = str(data.get('content',{}).get('rendered','')).lower()
        if (data.get('id') != pid or data.get('slug') != slug
                or data.get('acf',{}).get('key') != key
                or data.get('status') != 'publish'
                or 'blue sea' not in body
                or 'mũ bảo hiểm' not in body):
            raise RuntimeError('WP Page evidence changed; refusing cleanup of ' + str(pid))
        print('PASS source check: old Blue Sea WP Page id=' + str(pid)
              + ' slug=' + slug + ' key=' + key)

def auth_wp():
    name = os.environ.get('WP_ADMIN_USERNAME','')
    pwd = os.environ.get('WP_ADMIN_PASSWORD','')
    if not name or not pwd:
        raise RuntimeError('WordPress credentials missing in Actions secrets')
    agent = build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def request(path, data=None):
        dest = urljoin(BASE, path)
        if urlparse(dest).netloc != urlparse(BASE).netloc or not dest.startswith(BASE+'/'):
            raise RuntimeError('Refusing non-WordPress admin URL')
        req = Request(dest, data=data, headers={'User-Agent':'NCKH-Legacy-Page-Cleanup/1'})
        with agent.open(req, timeout=30) as r:
            final = r.geturl()
            if urlparse(final).netloc != urlparse(BASE).netloc:
                raise RuntimeError('Unexpected external login redirect')
            return final, r.read(800000).decode('utf-8','replace')
    request('/wp-login.php')
    form = urlencode({
        'log':name, 'pwd':pwd, 'wp-submit':'Log In',
        'redirect_to':BASE+'/wp-admin/edit.php?post_type=page',
        'testcookie':'1'
    }).encode('utf-8')
    final, body = request('/wp-login.php', form)
    if not urlparse(final).path.startswith('/wp-admin/'):
        raise RuntimeError('WP admin authentication failed')
    return request

def find_action_page(request, status, action, pid):
    _, body = request('/wp-admin/edit.php?post_type=page&post_status='
                      + status + '&posts_per_page=100')
    links = Links()
    links.feed(body)
    valid=[]
    for href in links.urls:
        u = urlparse(urljoin(BASE + '/wp-admin/', href))
        if u.netloc != urlparse(BASE).netloc or not u.path.endswith('/wp-admin/post.php'):
            continue
        q=parse_qs(u.query)
        if q.get('post') == [str(pid)] and q.get('action') == [action] and q.get('_wpnonce'):
            valid.append(u.geturl())
    if len(valid) != 1:
        raise RuntimeError('Could not uniquely resolve WP admin '+action+' action for Page '+str(pid))
    return valid[0]

def do_action(request, url, pid, expected):
    path = url.replace(BASE,'',1)
    final, _ = request(path)
    # After trash/restore WP redirects to its admin page list; no unrelated host.
    if '/wp-admin/' not in final:
        raise RuntimeError('WordPress '+expected+' did not return to admin for '+str(pid))
    print('WP admin action performed: '+expected+' id='+str(pid))

def verify_trash(request,pid):
    # Inspect WordPress admin's own Trash list; public endpoints may hide trash.
    _, page = request('/wp-admin/edit.php?post_type=page&post_status=trash&posts_per_page=100')
    if ('id="post-'+str(pid)+'"') not in page and ("id='post-"+str(pid)+"'") not in page:
        raise RuntimeError('WP Trash does not contain expected Page '+str(pid))
    print('PASS trash verified: Page '+str(pid))

def run(mode):
    verify_sources()
    request = auth_wp()
    links = {}
    for pid in TARGETS:
        links[pid] = find_action_page(request,'publish','trash',pid)
        print('PASS nonce-authenticated WP Trash action resolved: '+str(pid))
    if mode == 'check':
        print('PRECHECK PASS; no WordPress data modified')
        return
    if mode != 'trash':
        raise RuntimeError('Invalid mode')
    print('Beginning reversible WordPress Trash of exactly two legacy Blue Sea Pages.')
    completed = []
    try:
        for pid in TARGETS:
            do_action(request, links[pid], pid, 'trash')
            completed.append(pid)
            verify_trash(request,pid)
    except Exception:
        print('ERROR: cleanup interrupted; attempting to restore already-trashed Pages.')
        for pid in reversed(completed):
            try:
                restore_url = find_action_page(request,'trash','untrash',pid)
                do_action(request,restore_url,pid,'restore')
                print('Rollback restored Page '+str(pid))
            except Exception:
                print('WARNING: automated rollback unavailable for Page '+str(pid)
                      + '; recover via WordPress Admin > Pages > Trash.')
        raise
    print('TRASH_COMPLETE '+json.dumps({'trashedIds':completed,'forceDelete':False,
                                        'otherWordPressRecordsTouched':0}))

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['check','trash'], default='check')
    args=parser.parse_args()
    run(args.mode)
