"""Run a real FFmpeg batch and resume without any cloud key/private recording."""
from pathlib import Path
import importlib.util
import sys
import tempfile
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('course',ROOT/'tach-video.py')
app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)


def main():
    with tempfile.TemporaryDirectory(prefix='course-smoke-') as temp:
        job=Path(temp)
        assert job.resolve().parent==Path(tempfile.gettempdir()).resolve()
        source=job/'nguon.mkv'
        app.av.run([app.av.tool('ffmpeg'),'-v','error','-y','-f','lavfi','-i','testsrc2=size=640x360:rate=25:duration=6',
                    '-f','lavfi','-i','sine=frequency=440:duration=6','-c:v','ffv1','-c:a','pcm_s16le',source])
        app.av.save_json(job/'khoa-hoc.json',{'source':str(source),'source_identity':app.source_identity(source),
                        'start':0,'end':6,'width':640,'height':360,'title':'Synthetic test'})
        words=[{'text':'Thử','start':i+.1,'end':i+.4} for i in range(6)]
        app.av.save_json(job/'phien-am.json',{'words':words})
        lessons=[{'id':'1','title':'Hai đoạn cùng bài','segments':[{'start':1,'end':2.4},{'start':3.1,'end':4.5}]},
                 {'id':'2','title':'Bài thứ hai','segments':[{'start':4.7,'end':5.9}]}]
        plan={'approved':False,'lessons':[{'id':'bai-1','title':'Một bài học gồm hai video','blocks':[
            {'type':'video',**lessons[0]},
            {'type':'activity','id':'thuc-hanh','kind':'practice','instructions':'Thực hành 8 phút rồi xem phần 2',
             'duration_minutes':8,'next_video':'2','placement':'between_videos'},
            {'type':'video',**lessons[1]}]}]}
        app.av.save_json(job/'bai-hoc.json',plan)
        args=SimpleNamespace(duyet=True,rong=0,phu_de='roi',kieu_chu='toi-gian',crf=20,preset='fast',khung=None,muc_dich='bai-hoc')
        app.export(job,args)
        structure=app.av.load_json(job/'cau-truc-bai-hoc.json')
        assert len(structure['lessons'])==1
        blocks=structure['lessons'][0]['blocks']
        assert [b['type'] for b in blocks]==['video','activity','video']
        assert blocks[1]['duration_minutes']==8 and all(Path(b['video']).is_file() for b in blocks if b['type']=='video')
        states=app.av.load_json(job/'tien-do.json')
        assert all(s['status']=='done' for s in states.values())
        assert abs(states['1']['duration']-2.8)<.15 and abs(states['2']['duration']-1.2)<.15
        mtimes={i:Path(s['output']).stat().st_mtime_ns for i,s in states.items()}
        args.duyet=False;app.export(job,args)
        assert all(Path(s['output']).stat().st_mtime_ns==mtimes[i] for i,s in states.items())
        # Missing subtitles must rerender only their lesson, while retaining the prior video.
        Path(states['1']['subtitle']).unlink()
        app.export(job,args)
        now=app.av.load_json(job/'tien-do.json')
        assert now['1']['output']!=states['1']['output']
        assert Path(states['1']['output']).exists()
        assert Path(now['2']['output']).stat().st_mtime_ns==mtimes['2']
        print('SMOKE PASS: one lesson, two videos, activity between, unchanged cut durations, resume and selective recovery.')


if __name__=='__main__':main()
