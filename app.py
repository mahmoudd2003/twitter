# ========== Auto Install snscrape if missing ==========
import subprocess, sys
try:
    import snscrape  # noqa
except ImportError:
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "snscrape==0.7.0.20230622", "httpx<0.28"],
        check=False
    )
# ======================================================

import streamlit as st
import pandas as pd
from libs.utils import load_baseline, save_baseline, get_env
from libs.scoring import update_ema, spike_scores
from libs.twitter_client import search_with_snscrape, search_with_tweepy
from libs.trends import rising_queries
from libs.alerts import telegram_notify

st.set_page_config(page_title="Trend Radar — Twitter (Arabic)", layout="wide")
st.title("📈 Trend Radar — Twitter (Arabic)")

st.sidebar.header("الإعدادات")
lang = st.sidebar.selectbox("اللغة", ["ar", "en"], index=0)
window_minutes = st.sidebar.number_input("نافذة الرصد (دقائق)", min_value=5, max_value=120, value=int(get_env("DEFAULT_WINDOW_MINUTES", 15)))
threshold = st.sidebar.number_input("عتبة التنبيه (Spike Score)", min_value=5, max_value=200, value=int(get_env("DEFAULT_SPIKE_THRESHOLD", 25)))
regions = st.sidebar.text_input("الدول (Google Trends، مفصولة بفواصل)", value=get_env("REGIONS", "JO,SA,AE,EG"))
use_api = st.sidebar.checkbox("استخدام X API (بدلاً من snscrape)")

seed_terms = st.sidebar.text_area("الكلمات/العبارات المراد مراقبتها (سطر لكل كلمة)", value="عاجل\nبيان رسمي\nالرياض\nالأردن\nدبي\nالسعودية").strip().splitlines()
seed_terms = [s for s in seed_terms if s.strip()]

st.sidebar.markdown("---")
if st.sidebar.button("جلب اقتراحات من Google Trends"):
    st.session_state.setdefault("trends", {})
    out = {}
    for geo in [g.strip() for g in regions.split(",") if g.strip()]:
        out[geo] = rising_queries(seed_terms, geo=geo)
    st.session_state["trends"] = out
    st.sidebar.success("تم جلب الاقتراحات. أنظر التبويب في الأسفل.")

tab1, tab2, tab3 = st.tabs(["رادار (Twitter)", "اقتراحات Google Trends", "الإعدادات المتقدمة"])

with tab1:
    st.subheader("الرصد الحالي")
    mode = "X API" if use_api else "snscrape"
    st.caption(f"وضع البحث: {mode} | النافذة: آخر {window_minutes} دقيقة | اللغة: {lang}")
    bearer = get_env("X_BEARER_TOKEN", None)
    counts, details = {}, {}

    for term in seed_terms:
        try:
            if use_api and bearer:
                tweets = search_with_tweepy(term, bearer_token=bearer, lang=lang, minutes=window_minutes)
            else:
                tweets = search_with_snscrape(term, lang=lang, minutes=window_minutes)
        except Exception as e:
            st.error(f"خطأ أثناء جلب التغريدات: {e}")
            tweets = []
        counts[term] = len(tweets)
        details[term] = tweets

    baseline = load_baseline()
    baseline_updated = update_ema(baseline, counts, alpha=0.3)
    scores = spike_scores(baseline_updated, counts)
    save_baseline(baseline_updated)

    df = pd.DataFrame({
        "term": list(counts.keys()),
        "count": list(counts.values()),
        "ema": [baseline_updated.get(t, {}).get("ema", 0.0) for t in counts.keys()],
        "spike_score": [scores.get(t, 0.0) for t in counts.keys()],
    }).sort_values("spike_score", ascending=False)

    st.dataframe(df, use_container_width=True)

    bot = get_env("TELEGRAM_BOT_TOKEN", "")
    chat = get_env("TELEGRAM_CHAT_ID", "")
    high = df[df["spike_score"] >= threshold]
    if not high.empty:
        st.warning(f"تنبيهات محتملة: {len(high)} مصطلح تجاوز العتبة")
        if st.button("إرسال تنبيه Telegram الآن"):
            msg_lines = ["<b>🚨 Trend Radar Alerts</b>"]
            for _, row in high.iterrows():
                msg_lines.append(f"• <b>{row['term']}</b> — score={row['spike_score']}, count={row['count']}")
            ok = telegram_notify(bot, chat, "\n".join(msg_lines))
            st.success("تم إرسال التنبيه" if ok else "فشل إرسال التنبيه (تحقق من الإعدادات)")

with tab2:
    st.subheader("اقتراحات Google Trends (عالية النمو)")
    trends_cache = st.session_state.get("trends", {})
    if not trends_cache:
        st.info("استخدم زر 'جلب اقتراحات Google Trends' من الشريط الجانبي.")
    else:
        for geo, mapping in trends_cache.items():
            st.markdown(f"#### {geo}")
            for seed, related in mapping.items():
                if related:
                    st.write(f"**{seed}** → {', '.join(related)}")
                else:
                    st.write(f"**{seed}** → لا توجد اقتراحات صاعدة حالياً.")

with tab3:
    st.subheader("ملاحظات وضبط متقدم")
    st.markdown("""
- نافذة قصيرة (5–15 دقيقة) = رصد مبكر أدق.
- يمكنك تعديل حساسية spike من libs/scoring.py.
- لإشعارات فورية استخدم Telegram.
- لتفعيل X API، ضع مفاتيحك في .env ثم فعّل الخيار من الشريط الجانبي.
""")
