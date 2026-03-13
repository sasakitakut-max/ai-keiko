
import streamlit as st
import streamlit.components.v1 as components
from difflib import SequenceMatcher
import asyncio
import edge_tts
import tempfile
import base64
import time
import os
import re
import unicodedata

TITLE = "AI稽古"
SUBTITLE = "スマホでも使いやすい、AI読み合わせデモ"
TAGLINE = "半自動 / AIは自動進行 / あなたは録音して判定"

st.set_page_config(page_title=TITLE, layout="centered", initial_sidebar_state="collapsed")

SCRIPT = [
    {"role": "A", "text": "どうして黙ってたの？"},
    {"role": "B", "text": "言えなかったんだ"},
    {"role": "A", "text": "……どうして？"},
]

USER_ROLE = "A"
AI_VOICE = "ja-JP-NanamiNeural"
AUTO_ADVANCE_SEC = 2.8

st.markdown(
"""
<style>

/* 全体背景 */
.stApp {
    background: linear-gradient(180deg,#f6f2ea 0%,#f1ece3 100%);
}

/* コンテンツ幅 */
.block-container{
    max-width:760px;
    padding-top:3.5rem;
    padding-bottom:1rem;
    padding-left:1rem;
    padding-right:1rem;
}

/* タイトルエリア */
.brand-wrap{
    text-align:center;
    margin-top:0.8rem;
    margin-bottom:1.2rem;
}

.brand-title{
    font-size:34px;
    font-weight:900;
    letter-spacing:0.03em;
    color:#1c1c1c;
    margin-bottom:0.2rem;
}

.brand-subtitle{
    font-size:15px;
    color:#5a5248;
}

.brand-tagline{
    display:inline-block;
    margin-top:0.4rem;
    padding:0.4rem 0.8rem;
    border-radius:999px;
    background:#1c1c1c;
    color:#fff;
    font-size:12px;
}

/* カード */
.stage-card{
    background:white;
    border-radius:18px;
    padding:18px;
    box-shadow:0 8px 24px rgba(0,0,0,0.08);
    border:1px solid #e5ddd0;
}

/* セリフ表示 */
.role{
    font-size:16px;
    font-weight:700;
    color:#6a5640;
    margin-top:6px;
}

.line{
    font-size:26px;
    line-height:1.7;
    margin-left:0.5em;
    margin-bottom:10px;
}

/* ボタン */
.stButton>button{
    width:100%;
    min-height:56px;
    font-size:18px;
    font-weight:700;
    border-radius:14px;
}

/* スコア */
.score{
    font-size:30px;
    text-align:center;
    font-weight:900;
}

.score-sub{
    text-align:center;
    font-size:14px;
    color:#6c6258;
}

/* スマホ最適化 */
@media (max-width:640px){

.block-container{
    padding-top:4.5rem;
}

.brand-title{
    font-size:28px;
}

.brand-subtitle{
    font-size:14px;
}

.stage-card{
    padding:14px;
}

.line{
    font-size:22px;
}

.stButton>button{
    font-size:16px;
    min-height:54px;
}

}

</style>
""",
unsafe_allow_html=True,
)

if "idx" not in st.session_state:
    st.session_state.idx = 0

if "started" not in st.session_state:
    st.session_state.started = False

if "score" not in st.session_state:
    st.session_state.score = None

if "transcript" not in st.session_state:
    st.session_state.transcript = ""


@st.cache_data(show_spinner=False)
def synthesize_tts(text):
    async def run():
        with tempfile.NamedTemporaryFile(delete=False,suffix=".mp3") as f:
            path=f.name
        try:
            communicate=edge_tts.Communicate(text=text,voice=AI_VOICE)
            await communicate.save(path)
            with open(path,"rb") as af:
                return af.read()
        finally:
            if os.path.exists(path):
                os.remove(path)

    return asyncio.run(run())


def autoplay(audio_bytes):
    b64=base64.b64encode(audio_bytes).decode()
    st.markdown(
        f'<audio autoplay controls style="width:100%"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>',
        unsafe_allow_html=True,
    )


def normalize(text):
    text=unicodedata.normalize("NFKC",text)
    text=re.sub(r"[、。,.!！?？「」『』（）()\\s]","",text)
    return text


def similarity(a,b):
    return int(SequenceMatcher(None,normalize(a),normalize(b)).ratio()*100)


def speech_to_text(audio_bytes):

    import speech_recognition as sr

    with tempfile.NamedTemporaryFile(delete=False,suffix=".wav") as f:
        f.write(audio_bytes)
        path=f.name

    r=sr.Recognizer()
    with sr.AudioFile(path) as source:
        audio=r.record(source)

    try:
        text=r.recognize_google(audio,language="ja-JP")
    except:
        text=""

    os.remove(path)
    return text


st.markdown(
f"""
<div class="brand-wrap">
<div class="brand-title">{TITLE}</div>
<div class="brand-subtitle">{SUBTITLE}</div>
<div class="brand-tagline">{TAGLINE}</div>
</div>
""",
unsafe_allow_html=True,
)


if not st.session_state.started:

    if st.button("▶ アクションスタート"):
        st.session_state.started=True
        st.rerun()

    st.stop()


current=SCRIPT[st.session_state.idx]

st.markdown('<div class="stage-card">',unsafe_allow_html=True)

if current["role"]!=USER_ROLE:

    st.markdown(f"<div class='role'>相手役</div>",unsafe_allow_html=True)
    st.markdown(f"<div class='line'>{current['text']}</div>",unsafe_allow_html=True)

    audio=synthesize_tts(current["text"])
    autoplay(audio)

    time.sleep(AUTO_ADVANCE_SEC)

    st.session_state.idx+=1
    st.rerun()

else:

    st.markdown("<div class='role'>あなた</div>",unsafe_allow_html=True)
    st.markdown(f"<div class='line'>{current['text']}</div>",unsafe_allow_html=True)

    audio=st.audio_input("録音")

    if audio:

        st.audio(audio)

        if st.button("判定"):

            text=speech_to_text(audio.getvalue())
            score=similarity(text,current["text"])

            st.session_state.transcript=text
            st.session_state.score=score

    if st.session_state.transcript:

        st.write("認識:",st.session_state.transcript)

    if st.session_state.score is not None:

        score=st.session_state.score

        st.markdown(f"<div class='score'>{score}%</div>",unsafe_allow_html=True)

        if st.button("次へ"):
            st.session_state.idx+=1
            st.session_state.score=None
            st.session_state.transcript=""
            st.rerun()

st.markdown("</div>",unsafe_allow_html=True)
