from pathlib import Path
import hashlib,json,math,os,subprocess,sys
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parent
P=Path(os.environ.get('EXPLAINER_OUT',str(ROOT.parents[1]/'out'/'approved-narration'))).resolve()
CONFIG=json.loads((ROOT/'project.json').read_text())
ART=(ROOT/CONFIG['illustration_sheet']).resolve() if CONFIG.get('illustration_sheet') else None
if ART is not None and not ART.is_file():raise SystemExit(f'Missing illustration sheet: {ART}')
T=json.loads((P/'timings.json').read_text())
RENDERER_HASH=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
ART_HASH=hashlib.sha256(ART.read_bytes()).hexdigest() if ART else None
W,H=1280,720; BG='#F5F0E6'; INK='#213E34'; SAGE='#A6B59C'; SOFT='#E0E6D6'; MUTED='#526858'; RULE='#C4CEBA'
FONTDIR=Path(CONFIG['font_dir'])
SANS=str(FONTDIR/'DejaVuSans.ttf');BOLD=str(FONTDIR/'DejaVuSans-Bold.ttf');SERIF=str(FONTDIR/'DejaVuSerif.ttf')
def f(size,bold=False,serif=False):return ImageFont.truetype(SERIF if serif else BOLD if bold else SANS,size)
def new():
 im=Image.new('RGBA',(W,H),(0,0,0,0));return im,ImageDraw.Draw(im)
def txt(d,s,x,y,size=36,width=1120,bold=False,serif=False,color=INK,gap=1.32):
 font=f(size,bold,serif);lines=[]
 for para in s.split('\n'):
  line=''
  for word in para.split():
   test=(line+' '+word).strip()
   if d.textlength(test,font=font)>width and line:lines.append(line);line=word
   else:line=test
  lines.append(line)
 for line in lines:
  if d.textlength(line,font=font)>width+2:raise ValueError('Text overflow: '+line)
  d.text((x,y),line,font=font,fill=color);y+=round(size*gap)
 return y
def heading(d,title,kicker=None):
 if kicker:txt(d,kicker.upper(),72,44,19,bold=True,color=MUTED)
 return txt(d,title,72,100 if kicker else 65,47,serif=True)
def label(d,s,x,y):return txt(d,s.upper(),x,y,19,bold=True,color=MUTED)
def line(d,x,y,x2,y2):d.line((x,y,x2,y2),fill=RULE,width=3)
def arrow(d,x,y,x2,y2):
 d.line((x,y,x2,y2),fill=MUTED,width=3);a=math.atan2(y2-y,x2-x)
 d.polygon([(x2,y2),(x2-13*math.cos(a-.5),y2-13*math.sin(a-.5)),(x2-13*math.cos(a+.5),y2-13*math.sin(a+.5))],fill=MUTED)
def speech(d,x,y,w,h,thought=False):
 d.rounded_rectangle((x,y,x+w,y+h),radius=40 if thought else 15,outline=SAGE,width=3)
 if thought:
  d.ellipse((x+30,y+h+10,x+47,y+h+27),outline=SAGE,width=3);d.ellipse((x+15,y+h+35,x+25,y+h+45),outline=SAGE,width=2)
 else:d.line((x+70,y+h,x+50,y+h+30,x+110,y+h),fill=SAGE,width=3)
def paper(d,x,y,w=160,h=200):
 d.rounded_rectangle((x,y,x+w,y+h),radius=8,fill=SOFT,outline=SAGE,width=3)
 for j in range(4):line(d,x+25,y+45+j*30,x+w-25,y+45+j*30)

def phone(d,x,y):
 w,h=270,410
 d.rounded_rectangle((x,y,x+w,y+h),radius=30,fill='#EEEBDD',outline=INK,width=4)
 d.rounded_rectangle((x+12,y+12,x+w-12,y+h-12),radius=22,fill='#FAF7EF',outline=RULE,width=1)
 d.rounded_rectangle((x+90,y+12,x+180,y+24),radius=5,fill=INK)
 d.rounded_rectangle((x+28,y+100,x+w-28,y+180),radius=15,fill=SOFT)
 txt(d,'Your message',x+45,y+125,22,width=200)
 d.line((x+95,y+h-22,x+175,y+h-22),fill=INK,width=4)
 # A time marker explains the wait; no decorative objects.
 d.ellipse((x+215,y+260,x+345,y+390),fill=BG,outline=SAGE,width=3)
 txt(d,'2',x+263,y+275,42,bold=True)
 txt(d,'days',x+254,y+330,23,color=MUTED)
def notebook(d,x,y):
 w,h=245,175
 d.rounded_rectangle((x,y,x+w,y+h),radius=10,fill='#FAF7EF',outline=SAGE,width=3)
 d.line((x+30,y+5,x+30,y+h-5),fill=RULE,width=2)
 for j in range(3):
  txt(d,str(j+1),x+45,y+23+j*48,20,color=MUTED)
  line(d,x+80,y+42+j*48,x+w-25,y+42+j*48)

def timeof(t,phrase,fallback=0):
 for c in t['cues']:
  if phrase.lower() in c['text'].lower():return c['start']
 return fallback
def stacked(d,items,starty=240):
 for j,item in enumerate(items):
  y=starty+j*115
  d.ellipse((80,y+10,122,y+52),fill=SOFT);txt(d,str(j+1),92,y+16,21,bold=True)
  txt(d,item,155,y,37,width=1010)

aw,ah=Image.open(ART).size if ART is not None else (2,2);cw,ch=aw//2,ah//2
artpos={
 'title':(0,0,760,427,500,268),
 'tuesday':(0,0,990,556,180,168),
 'thursday':(cw,0,990,556,180,168),
 'feeling':(cw,0,630,354,620,345),
 'impact':(cw,0,660,371,610,330),
 'request_change':(cw,0,660,371,620,315),
}

for t in T:
 i=t['number'];kind=t['kind'];dur=t['duration'];layers=[]
 def add(im,start=0,end=None):
  path=P/f'text-{i:02}-{len(layers)}.png';im.save(path);layers.append((path,start,end))
 im,d=new()
 if kind=='title':
  label(d,'A fictional workplace example',72,60)
  txt(d,'Why we\nmisinterpret\npeople',72,190,68,width=700,serif=True)
 elif kind in ('tuesday','thursday'):
  label(d,'What Rowan said',72,45)
  txt(d,kind.capitalize(),72,93,32,bold=True)
  q='“Your idea looks promising.”' if kind=='tuesday' else '“I don’t think it’s ready yet.”'
  txt(d,q,72,155,44,serif=True)
 elif kind=='feeling':
  heading(d,'An effect. A suspected reason.')
  label(d,'How it may feel',80,235);txt(d,'“I felt embarrassed.”',80,280,37,width=1000)
  label(d,'What you might think',80,385)
  txt(d,'“Rowan wanted to make me look bad in front of everyone.”',80,430,36,width=530)
 elif kind=='compatible':
  heading(d,'These can both be true')
  txt(d,'Promising',100,280,63,serif=True)
  txt(d,'Needs work',700,280,63,serif=True)
  d.ellipse((593,285,653,345),fill=SOFT);txt(d,'+',608,286,42)
  line(d,100,400,1180,400)
  txt(d,'Not necessarily contradictory',220,490,43,width=1000,bold=True)
 elif kind=='heard_guessed':
  heading(d,'Keep the words and the guess separate')
  label(d,'What you heard',90,225)
  speech(d,80,275,510,230)
  txt(d,'“I don’t think\nit’s ready yet.”',115,325,40,width=450)
 elif kind=='impact':
  heading(d,'The impact matters')
  txt(d,'“I felt embarrassed.”',80,245,49,serif=True)
  txt(d,'Describes the effect on you.',82,340,29,color=MUTED)
  txt(d,'Does not establish\nRowan’s intention.',82,465,36,width=520)
 elif kind=='possibilities':
  heading(d,'Possible explanations to check')
  label(d,'Possibilities — not findings',75,160)
 elif kind=='uncertainty':
  heading(d,'More than one could be true')
  txt(d,'We do not know which is right.',80,220,33,color=MUTED)
  line(d,80,315,1200,315)
  txt(d,'“What do I know,\nand what am I guessing?”',80,385,53,width=1120,serif=True)
 elif kind in ('confirmation_definition','correspondence_definition'):
  title='Confirmation bias' if kind=='confirmation_definition' else 'Correspondence bias'
  heading(d,title,'Two kinds of bias')
  definition='Looking for information—or understanding it in a way—that supports what you already believe.' if kind=='confirmation_definition' else 'Judging someone’s character from their behaviour while giving too little weight to their circumstances.'
  d.rectangle((78,245,86,585),fill=SAGE)
  txt(d,definition,120,265,43,width=1010,gap=1.5)
 elif kind=='confirmation_example':
  heading(d,'Which information are you noticing?')
  label(d,'Existing belief',80,190);txt(d,'Rowan dislikes your idea.',80,225,38)
  line(d,80,305,1200,305)
  label(d,'Noticed',100,370);txt(d,'Criticism',100,425,45,serif=True)
  label(d,'Overlooked',720,370);txt(d,'Positive comments',720,425,39,serif=True)
  txt(d,'You may not realise you are doing it.',240,610,30,color=MUTED)
 elif kind=='nickerson':
  heading(d,'Research explains the pattern')
  paper(d,90,240,180,245)
  txt(d,'Raymond Nickerson · 1998',330,260,38,bold=True)
  txt(d,'Examined earlier research\non confirmation bias.',330,335,35,width=800)
  txt(d,'It cannot tell us whether your\nconclusion about Rowan is right.',100,555,35,width=1100)
 elif kind=='correspondence_example':
  heading(d,'A judgment about the person')
  label(d,'Judgment',85,235);txt(d,'“Rowan is an\nunhelpful person.”',85,285,44,width=540,serif=True)
  label(d,'Circumstance not yet checked',700,235);txt(d,'A new budget problem',700,285,39,width=500,serif=True)
  line(d,80,510,1200,510)
  txt(d,'Gilbert and Malone · 1995',80,560,27,bold=True)
  txt(d,'Examined earlier research on correspondence bias.',80,610,25,color=MUTED)
 elif kind=='compare_biases':
  heading(d,'Two different ideas')
  label(d,'Confirmation bias',90,235);txt(d,'How you handle\ninformation',90,305,45,width=510,serif=True)
  line(d,640,225,640,535)
  label(d,'Correspondence bias',710,235);txt(d,'How you explain\nbehaviour',710,305,45,width=510,serif=True)
  txt(d,'You may judge the person while overlooking their situation.',710,470,27,width=500,color=MUTED)
 elif kind=='ask':
  heading(d,'What could you ask Rowan?')
 elif kind=='specific_checks':
  heading(d,'“What would help me check that?”')
 elif kind=='limits_questions':
  heading(d,'A specific question has limits')
  stacked(d,['It does not guarantee honesty or agreement.','Compare the answer with relevant information.','You can still feel hurt while asking.'],240)
 elif kind=='friend':
  heading(d,'A different fictional situation')
  phone(d,135,230)
  label(d,'What happened',690,245);txt(d,'No reply\nfor two days.',690,285,43,width=510,serif=True)
  label(d,'What you think',690,455);txt(d,'“They don’t care\nabout me.”',690,495,37,width=510)
 elif kind=='pause':
  heading(d,'Pause the video here','A moment to practise')
  stacked(d,['What do you know?','What are you guessing?','What could you ask or check?'],245)
 elif kind=='friend_separate':
  heading(d,'Separate what you know from the guess')
  label(d,'What you know',80,240);txt(d,'No reply for two days.',80,285,41,width=1100)
  line(d,80,370,1200,370)
  label(d,'What you are guessing',80,420);txt(d,'They do not care about you.',80,465,38,width=800)
 elif kind=='friend_possibilities':
  heading(d,'Several possibilities remain')
  for j,s in enumerate(['Avoiding you','Busy','Unwell','Unsure what to say']):
   x=90+(j%2)*600;y=225+(j//2)*90
   d.ellipse((x,y+14,x+12,y+26),fill=SAGE);txt(d,s,x+35,y,33,width=520)
  line(d,80,440,1200,440)
  txt(d,'“Did you see my message?”',120,490,45,serif=True)
  txt(d,'It does not settle everything about the friendship.',150,625,27,color=MUTED)
 elif kind=='boundaries':
  heading(d,'There is an important limit')
  txt(d,'You do not have to discover\nsomeone’s motive before\nresponding to repeated\nharmful behaviour.',95,245,48,width=1100,serif=True,gap=1.45)
 elif kind=='request_change':
  heading(d,'Where it is safe, request a specific change')
  txt(d,'Raise problems\nbefore a meeting.',80,275,49,width=1100,serif=True)
  txt(d,'So you have time\nto address them.',82,440,33,width=500,color=MUTED)
 elif kind=='safety':
  label(d,'If asking directly could put you at risk',80,100)
  txt(d,'Seek appropriate support.',80,190,51,serif=True)
  line(d,80,330,1200,330)
  txt(d,'Understanding someone\ndoes not require\naccepting harm.',80,400,51,serif=True)
 elif kind in ('practice','end'):
  heading(d,'Three questions to take with you' if kind=='end' else 'Choose one ordinary situation this week')
  stacked(d,['What did they say or do?','Why do I think they did it?','How could I check?'],220)
  if kind=='practice':txt(d,'If it is safe and useful, make that check.',85,640,27,color=MUTED)
  if kind=='end':
   line(d,80,570,1200,570)
   txt(d,CONFIG['book_url'],80,598,27,color=INK)
   txt(d,CONFIG['copyright'],80,649,22,color=MUTED)
 elif kind=='review':
  heading(d,'Afterwards, note what you learned')
  notebook(d,920,440)
  txt(d,'Did it change your explanation,\nor what you will do next?',80,235,39,width=1100)
  txt(d,'You may still be uncertain.\nYou may nevertheless have enough\ninformation for a useful next step.',80,430,32,width=780,color=MUTED)
 add(im)
 if kind=='heard_guessed':
  im,d=new();label(d,'What you guessed',710,225);speech(d,690,275,510,230,True)
  txt(d,'“Rowan wants to\nembarrass me.”',725,325,40,width=450)
  add(im,timeof(t,'You do not yet know'))
  im,d=new();txt(d,'The guess could be right. It is still a guess.',200,600,30,color=MUTED)
  add(im,timeof(t,'The guess could be right'))
 if kind=='possibilities':
  data=[('Perhaps Rowan discovered','A budget problem emerged after Tuesday.'),('Perhaps Rowan liked','“Promising” did not mean “ready”.'),('Or perhaps Rowan wanted','Rowan wanted to protect their reputation.')]
  for j,(cue,content) in enumerate(data):
   im,d=new();y=245+j*133;txt(d,f'0{j+1}',80,y,27,color=MUTED);txt(d,content,150,y,36,width=1030);line(d,150,y+95,1200,y+95)
   add(im,timeof(t,cue))
 if kind=='ask':
  switch=timeof(t,'Instead,')
  im,d=new();label(d,'Assumes the intention',80,245);txt(d,'“Why did you try\nto embarrass me?”',80,310,53,serif=True);add(im,0,switch)
  im,d=new();label(d,'Describe the statements. Ask what is needed.',80,205)
  txt(d,'“On Tuesday you said the idea looked promising. Today you said it wasn’t ready. What needs more work?”',80,260,42,width=1100,serif=True)
  add(im,switch)
  im,d=new();txt(d,'Then listen.',80,620,31,bold=True);add(im,timeof(t,'Then listen'))
 if kind=='specific_checks':
  data=[('If Rowan mentions','Staffing costs','“Can we look at the figures?”'),('If Rowan says','Unfinished proposal','“What still needs doing?”')]
  for j,(cue,title,q) in enumerate(data):
   im,d=new();y=255+j*195;label(d,title,80,y);txt(d,q,80,y+50,42,width=1100,serif=True);add(im,timeof(t,cue))

 # Compose original illustration quadrants into video scenes, preserving alpha.
 outfile=P/f'clip-{i:02}.mp4'
 if '--only' in sys.argv and i not in [int(x) for x in sys.argv[sys.argv.index('--only')+1].split(',')]:continue
 signature=hashlib.sha256(json.dumps({'scene':t,'config':CONFIG,'renderer':RENDERER_HASH,'art':ART_HASH,'fonts':[hashlib.sha256(Path(x).read_bytes()).hexdigest() for x in [SANS,BOLD,SERIF]]},sort_keys=True).encode()).hexdigest()
 stamp=outfile.with_suffix('.sha256')
 if outfile.exists() and stamp.exists() and stamp.read_text()==signature and '--force' not in sys.argv:continue
 cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi','-i',f'color=c={BG}:s=1280x720:r=24:d={dur}']
 filters=[];base='0:v';idx=1
 if ART is not None and kind in artpos:
  x,y,w,h,ox,oy=artpos[kind];cmd+=['-loop','1','-framerate','24','-i',str(ART)]
  filters.append(f'[{idx}:v]crop={cw}:{ch}:{x}:{y},scale={w}:{h},format=rgba,fade=t=in:st=0:d=0.5:alpha=1[art]')
  filters.append(f'[{base}][art]overlay=x={ox}+3*sin(t/8):y={oy}:shortest=1[b0]');base='b0';idx+=1
 for j,(path,start,end) in enumerate(layers):
  cmd+=['-loop','1','-framerate','24','-i',str(path)]
  ff=f'[{idx}:v]format=rgba,fade=t=in:st={start}:d=0.3:alpha=1'
  if end is not None:ff+=f',fade=t=out:st={max(start,end-.18)}:d=0.18:alpha=1'
  filters.append(ff+f'[txt{j}]');filters.append(f'[{base}][txt{j}]overlay=0:0:shortest=1[b{j+1}]');base=f'b{j+1}';idx+=1
 filters.append(f'[{base}]format=yuv420p[v]')
 cmd+=['-filter_complex',';'.join(filters),'-map','[v]','-t',str(dur),'-an','-c:v','libx264','-crf','20','-preset','veryfast','-threads','2','-filter_complex_threads','2',str(outfile)]
 subprocess.run(cmd,check=True);stamp.write_text(signature);print(f"Rendered {i+1:02}/{len(T)}: {kind}",flush=True)

(P/'clips.txt').write_text(''.join(f"file 'clip-{t['number']:02}.mp4'\n" for t in T))
if '--no-mux' not in sys.argv and '--only' not in sys.argv and all((P/f"clip-{t['number']:02}.mp4").exists() for t in T):
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(P/'clips.txt'),'-i',str(P/'narration.wav'),'-i',str(P/'captions.srt'),'-map','0:v','-map','1:a','-map','2:s','-c:v','copy','-af','loudnorm=I=-16:TP=-1.5:LRA=11','-c:a','aac','-b:a','160k','-c:s','mov_text','-metadata:s:s:0','language=eng','-movflags','+faststart','-metadata','title='+CONFIG['title'],'-metadata','comment=Approved narration. Synthetic voice: '+CONFIG['voice']+'. Source: '+CONFIG['source_url'],str(P/'why-we-misinterpret-people.mp4')],check=True)
 print('FINAL VIDEO READY',flush=True)
