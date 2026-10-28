from pathlib import Path
import asyncio,bisect,hashlib,json,math,os,re,subprocess,wave
from importlib.metadata import version
import numpy as np
import edge_tts

ROOT=Path(__file__).resolve().parent
P=Path(os.environ.get('EXPLAINER_OUT',str(ROOT.parents[1]/'out'/'approved-narration'))).resolve()
P.mkdir(parents=True,exist_ok=True)
CONFIG=json.loads((ROOT/'project.json').read_text())
SCENES=json.loads((ROOT/'narration.json').read_text())
SR=24000
def spoken(s):
 lexicon=CONFIG.get('pronunciation',{})
 if lexicon:
  pattern=r'(?<!\w)(?:'+'|'.join(re.escape(k) for k in sorted(lexicon,key=len,reverse=True))+r')(?!\w)'
  s=re.sub(pattern,lambda m:lexicon[m.group(0)],s)
 return s.replace('—',', ').replace('“','"').replace('”','"').replace('’',"'")
def norm(s):return ''.join(c.lower() for c in spoken(s) if c.isalnum())
async def generate(i,s,sem):
 if not s['text']:return
 mp3=P/f'raw-{i:02}.mp3';meta=P/f'words-{i:02}.json'
 signature=hashlib.sha256(json.dumps({'text':spoken(s['text']),'voice':CONFIG['voice'],'rate':CONFIG['rate'],'edge_tts':version('edge-tts'),'boundary':'WordBoundary'},sort_keys=True).encode()).hexdigest()
 if mp3.exists() and meta.exists():
  cached=json.loads(meta.read_text())
  if isinstance(cached,dict) and cached.get('signature')==signature:return
 async with sem:
  for attempt in range(3):
   try:
    c=edge_tts.Communicate(spoken(s['text']),voice=CONFIG['voice'],rate=CONFIG['rate'],boundary='WordBoundary',proxy=os.environ.get('HTTPS_PROXY'))
    words=[]
    with mp3.open('wb') as out:
     async for item in c.stream():
      if item['type']=='audio':out.write(item['data'])
      elif item['type']=='WordBoundary':words.append(item)
    assert words
    meta.write_text(json.dumps({'signature':signature,'words':words},ensure_ascii=False))
    print(f"Generated {i+1:02}: {s['kind']}",flush=True)
    return
   except Exception:
    if attempt==2:raise
    await asyncio.sleep(2)
async def main():
 sem=asyncio.Semaphore(3)
 await asyncio.gather(*(generate(i,s,sem) for i,s in enumerate(SCENES)))
asyncio.run(main())

def write(path,a):
 with wave.open(str(path),'wb') as w:
  w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes(a.astype(np.int16).tobytes())
def ts(t):
 n=round(t*1000);h,n=divmod(n,3600000);m,n=divmod(n,60000);s,ms=divmod(n,1000);return f'{h:02}:{m:02}:{s:02},{ms:03}'
all_audio=[];T=[];captions=[];cursor=0
for i,s in enumerate(SCENES):
 if not s['text']:
  a=np.zeros(SR*5,dtype=np.int16);T.append(dict(s,number=i,start=cursor,duration=5,cues=[]));all_audio.append(a);cursor+=5;continue
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(P/f'raw-{i:02}.mp3'),'-ar',str(SR),'-ac','1',str(P/f'raw-{i:02}.wav')],check=True)
 with wave.open(str(P/f'raw-{i:02}.wav'),'rb') as w:a=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).copy()
 words=json.loads((P/f'words-{i:02}.json').read_text())['words']
 joined='';starts=[];ends=[]
 for w in words:starts.append(len(joined));joined+=norm(w['text']);ends.append(len(joined))
 assert joined==norm(s['text']),f'Boundary text mismatch: {i}'
 # Keep a little audio before and after the provider's first/last word timings.
 cut=max(0,words[0]['offset']/1e7-.08)
 end=min(len(a)/SR,(words[-1]['offset']+words[-1]['duration'])/1e7+.23)
 a=a[round(cut*SR):round(end*SR)]
 lead=.25;tail=4.5 if s['kind']=='pause' else .7 if s['kind']=='title' else .45
 a=np.concatenate([np.zeros(round(lead*SR),dtype=np.int16),a,np.zeros(round(tail*SR),dtype=np.int16)])
 duration=math.ceil(len(a)/SR*24)/24;a=np.pad(a,(0,round(duration*SR)-len(a)))
 cues=[];charpos=0
 for sentence in re.findall(r'.+?(?:[.!?][”"]?(?=\s|$)|$)',s['text']):
  sentence=sentence.strip()
  if not sentence:continue
  n=len(norm(sentence));first=bisect.bisect_right(ends,charpos);last=bisect.bisect_left(ends,charpos+n)
  start=words[first]['offset']/1e7-cut+lead;finish=(words[last]['offset']+words[last]['duration'])/1e7-cut+lead
  cues.append({'start':start,'end':finish,'text':sentence})
  chunks=[];chunk=[]
  for word in sentence.split():
   if len(' '.join(chunk+[word]))>86 and chunk:chunks.append(' '.join(chunk));chunk=[]
   chunk.append(word)
  if chunk:chunks.append(' '.join(chunk))
  for chunk in chunks:
   length=len(norm(chunk));fidx=bisect.bisect_right(ends,charpos);lidx=bisect.bisect_left(ends,charpos+length)
   ca=words[fidx]['offset']/1e7-cut+lead;cb=(words[lidx]['offset']+words[lidx]['duration'])/1e7-cut+lead
   captions.append((cursor+ca,cursor+cb,chunk));charpos+=length
 assert charpos==len(joined)
 write(P/f'audio-{i:02}.wav',a);all_audio.append(a);T.append(dict(s,number=i,start=cursor,duration=duration,cues=cues));cursor+=duration
print('TOTAL DURATION:',cursor,flush=True)
assert CONFIG['min_seconds']<=cursor<=CONFIG['max_seconds'], f'Adjust delivery rate or deliberate holds: {cursor}s'
write(P/'narration.wav',np.concatenate(all_audio))
(P/'timings.json').write_text(json.dumps(T,ensure_ascii=False,indent=2))
(P/'captions.srt').write_text('\n\n'.join(f'{i+1}\n{ts(a)} --> {ts(b)}\n{s}' for i,(a,b,s) in enumerate(captions))+'\n')
(P/'transcript.txt').write_text(CONFIG['title']+'\n\nDisplay narration, preserved in full.\nSynthetic voice: '+CONFIG['voice']+'.\nSource: '+CONFIG['source_url']+'\n\n'+'\n\n'.join(s['text'] for s in SCENES if s['text']))
