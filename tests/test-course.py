import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location("course",ROOT/'tach-video.py')
course=importlib.util.module_from_spec(spec);spec.loader.exec_module(course)


class CourseTests(unittest.TestCase):
    def test_absolute_ranges_and_removed_gaps(self):
        ranges=[(120,125),(130,140)]
        cuts=course.complement(ranges,120,140)
        self.assertEqual(course.av.keep_ranges({'cuts':cuts},20),[(0,5),(10,20)])
        self.assertEqual(course.seconds('01:02:03.5'),3723.5)

    def test_reject_invalid_or_repeated_ranges(self):
        meta={'start':120,'end':165}
        for ranges in [[{'start':119,'end':125}],[{'start':float('nan'),'end':130}],
                       [{'start':120,'end':135},{'start':130,'end':150}]]:
            with self.assertRaises(course.av.VideoError):
                course.validate_plan({'lessons':[{'id':'1','title':'A','segments':ranges}]},meta)
        same=[{'id':str(i),'title':'A','segments':[{'start':120,'end':130}]} for i in range(2)]
        with self.assertRaises(course.av.VideoError):course.validate_plan({'lessons':same},meta)
        self.assertEqual(len(course.validate_plan({'lessons':same,'allow_reuse':True},meta)),2)

    def test_same_duration_different_content_invalidates_approval(self):
        old=[{'id':'1','title':'A','segments':[{'start':120,'end':130}]}]
        new=[{'id':'1','title':'A','segments':[{'start':140,'end':150}]}]
        self.assertNotEqual(course.plan_hash(old,{}),course.plan_hash(new,{}))

    def test_changed_or_missing_media_not_reused(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'video.mp4';p.write_bytes(b'media')
            s=Path(temp)/'phu-de.srt';s.write_text('caption')
            record={'status':'done','signature':'1','output':str(p),'sha256':course.checksum(p),'assets':{str(s):course.checksum(s)}}
            self.assertTrue(course.reusable(record,'1'))
            s.write_text('changed')
            self.assertFalse(course.reusable(record,'1'))
            s.unlink()
            self.assertFalse(course.reusable(record,'1'))

    def test_lock_released_and_prevents_duplicate_export(self):
        with tempfile.TemporaryDirectory() as temp:
            job=Path(temp)
            first=course.acquire_lock(job)
            try:
                with self.assertRaises(course.av.VideoError):course.acquire_lock(job)
            finally:course.release_lock(first)
            second=course.acquire_lock(job);course.release_lock(second)

    def test_vietnamese_titles_become_safe_names(self):
        self.assertEqual(course.slug('Đọc sách: Từ ý tưởng → hành động'),'doc-sach-tu-y-tuong-hanh-dong')

    def test_transcription_resumes_completed_chunks_after_network_failure(self):
        import requests
        from types import SimpleNamespace
        def response(word):
            return SimpleNamespace(status_code=200,json=lambda:{'words':[{'word':word,'start':0,'end':1}],'segments':[]})
        with tempfile.TemporaryDirectory(prefix='course-cache-test-') as temp:
            job=Path(temp);audio=job/'audio.flac';audio.write_bytes(b'synthetic-audio')
            def extraction(args,*unused,**kw):Path(args[-1]).write_bytes(b'chunk')
            with patch.object(course.av,'config',return_value={'GROQ_API_KEY':'synthetic-test-value'}), \
                 patch.object(course.av,'tool',return_value='ffmpeg'),patch.object(course.av,'run',side_effect=extraction), \
                 patch.object(course.av.time,'sleep'),patch.object(requests,'post') as post:
                post.side_effect=[response('first'),requests.ConnectionError(),requests.ConnectionError(),requests.ConnectionError()]
                with self.assertRaises(course.av.VideoError):course.av.groq_transcribe(audio,job,601)
                self.assertTrue((job/'groq-0.json').is_file())
                post.reset_mock();post.side_effect=None;post.return_value=response('second')
                words=course.av.groq_transcribe(audio,job,601)
                self.assertEqual(post.call_count,1)
                self.assertEqual([w['start'] for w in words],[0,600])


if __name__=='__main__':unittest.main()
