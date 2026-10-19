"""Collect public Telegram post evidence. Photo anchors and video players are distinct.
Raw pages and expiring CDN URLs stay in .qa; the curated manifest retains stable source links.
"""
import re, json, html, urllib.request, time
from pathlib import Path
from html.parser import HTMLParser

class Text(HTMLParser):
    def __init__(self): super().__init__(); self.parts=[]
    def handle_data(self,data): self.parts.append(data)
    def handle_starttag(self,tag,attrs):
        if tag=='br': self.parts.append('\n')

def parse_page(raw):
    posts=[]
    for block in re.split(r'<div class="tgme_widget_message_wrap',raw)[1:]:
        match=re.search(r'data-post="colibri_look/(\d+)"',block)
        if not match: continue
        post={'id':int(match[1]),'source':'https://t.me/colibri_look/'+match[1],'media':[]}
        caption=re.search(r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>',block,re.S)
        t=Text(); t.feed(caption[1] if caption else ''); post['text']=''.join(t.parts)
        dt=re.search(r'<time[^>]*datetime="([^"]+)"',block);post['date']=dt[1] if dt else ''
        for anchor in re.finditer(r'<a\b([^>]*class="[^"\n]*tgme_widget_message_(?:photo_wrap|video_player)[^"\n]*"[^>]*)>(.*?)</a>',block,re.S):
            attrs,body=anchor.groups(); tag=attrs+body
            href=re.search(r'href="([^"]+)"',attrs)
            srcpost=re.search(r'colibri_look/(\d+)',href[1] if href else '')
            ident=int(srcpost[1]) if srcpost else post['id']
            image=re.search(r"background-image:url\('([^']+)'\)",tag)
            if 'tgme_widget_message_video_player' in attrs:
                video=re.search(r'<video[^>]*src="([^"]+)"',body)
                media={'type':'video','id':ident,'url':html.unescape(video[1]) if video else None,'poster':html.unescape(image[1]) if image else None}
            else: media={'type':'photo','id':ident,'url':html.unescape(image[1]) if image else None}
            if media not in post['media']: post['media'].append(media)
        posts.append(post)
    return posts

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(); parser.add_argument('--pages',type=int,default=12); args=parser.parse_args()
    root=Path('.qa/archive'); root.mkdir(parents=True,exist_ok=True)
    before=None; allposts={}
    for i in range(args.pages):
        path=root/f'{before or "latest"}.html'
        if path.exists(): raw=path.read_text()
        else:
            url='https://t.me/s/colibri_look'+(f'?before={before}' if before else '')
            raw=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=35).read().decode();path.write_text(raw)
        posts=parse_page(raw)
        if not posts: break
        for p in posts: allposts[p['id']]=p
        nextbefore=min(p['id'] for p in posts)
        print(f'Page {i+1}: {nextbefore}–{max(p["id"] for p in posts)}; {len(posts)} posts',flush=True)
        if before and nextbefore>=before: break
        before=nextbefore
    result=sorted(allposts.values(),key=lambda p:p['id'])
    Path('.qa/telegram-evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    Path('.qa/telegram-captions.txt').write_text('\n\n'.join(f'{p["id"]} | {p["date"]} | '+','.join(f'{m["type"]}:{m["id"]}{" unavailable" if not m["url"] else ""}' for m in p['media'])+'\n'+p['text'] for p in result))
    print('Total:',len(result),'posts;',sum(len(p['media']) for p in result),'media')
